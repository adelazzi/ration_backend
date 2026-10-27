from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    MaterialEditForm, MaterialForm, MaterialPriceForm, MixIngredientFormSet, MixRatioForm,
    ProjectEditForm, ProjectForm,
)
from .models import BlockType, Material, MaterialPrice, MixBlockType, MixRatio, Project, ProjectBlock
from .permissions import config_viewer_required, manager_required, price_reviewer_required
from .services import estimate_project, latest_approved_prices, price_per_base_unit, save_estimate
from .templatetags.ration import money


@login_required
def home_view(request):
    return redirect('project_list')


# ---------- Projects ----------

def visible_projects(user):
    projects = Project.objects.all()
    if user.sees_only_approved_projects:
        # Business rule 5: creators see reports only after approval.
        projects = projects.filter(status__in=[Project.Status.APPROVED, Project.Status.COMPLETED])
    return projects


@login_required
def project_list_view(request):
    projects = visible_projects(request.user).select_related('created_by').prefetch_related(
        Prefetch('blocks', queryset=ProjectBlock.objects.order_by('block_type'))  # full before half
    )
    status = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()
    if status in Project.Status.values:
        projects = projects.filter(status=status)
    else:
        status = ''
    if query:
        projects = projects.filter(Q(name__icontains=query) | Q(description__icontains=query))

    counts = {s: 0 for s in Project.Status.values}
    for row in visible_projects(request.user).values('status'):
        counts[row['status']] += 1
    statuses = [
        {'value': value, 'label': label, 'count': counts[value]}
        for value, label in Project.Status.choices
        if not request.user.sees_only_approved_projects or counts[value]
    ]
    pending_prices = (
        MaterialPrice.objects.filter(status=MaterialPrice.Status.PENDING).count()
        if request.user.can_review_prices else 0
    )
    return render(request, 'core/project_list.html', {
        'projects': projects.order_by('-created_at'),
        'statuses': statuses,
        'status': status,
        'query': query,
        'total': sum(counts.values()),
        'pending_prices': pending_prices,
    })


def _save_blocks(project, form):
    """Make the project's block lines match the quantities in the form."""
    wanted = dict(form.block_quantities())
    strength = form.cleaned_data['required_strength_mpa']
    for block_type in BlockType.values:
        quantity = wanted.get(block_type)
        if quantity:
            ProjectBlock.objects.update_or_create(
                project=project, block_type=block_type,
                defaults={'quantity': quantity, 'required_strength_mpa': strength},
            )
        else:
            ProjectBlock.objects.filter(project=project, block_type=block_type).delete()


@manager_required
def project_new_view(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            _save_blocks(project, form)
        return redirect('project_detail', pk=project.pk)

    mixes = MixRatio.objects.filter(is_active=True).prefetch_related('ingredients__material').order_by('name')
    return render(request, 'core/project_new.html', {'form': form, 'mixes': mixes})


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(visible_projects(request.user).select_related('created_by'), pk=pk)
    estimate = estimate_project(project)

    # Materials this project's mixes use, with the price each one is costed at.
    materials = {}
    for line in estimate['lines']:
        for option in line['options']:
            for item in option['lines']:
                materials.setdefault(item['material'].pk, item['material'])
    material_rows = []
    for material in sorted(materials.values(), key=lambda m: m.name):
        price = estimate['prices'].get(material.pk)
        material_rows.append({
            'material': material,
            'price': price,
            'unit_price': price_per_base_unit(price) if price else None,
        })

    context = {
        'project': project,
        'estimate': estimate,
        'blocks': estimate['lines'],
        'material_rows': material_rows,
        'project_prices': project.material_prices.select_related('material', 'created_by', 'reviewed_by')
        .order_by('-created_at'),
        'final': project.final_estimate,
        'statuses': [choice for choice in Project.Status.choices if choice[0] != project.status],
    }
    if context['final']:
        context['final_materials'] = context['final'].materials.select_related('material')
    if request.user.is_manager:
        # Default to the currency this project is already priced in, so totals stay addable.
        currency = estimate['currency'] or next(
            (row['price'].currency for row in material_rows if row['price']), 'ZAR'
        )
        context['price_form'] = MaterialPriceForm(prefix='price', initial={'currency': currency})
    return render(request, 'core/project_detail.html', context)


@manager_required
@require_POST
def project_choose_mix_view(request, pk, block_pk):
    block = get_object_or_404(ProjectBlock.objects.select_related('project'), pk=block_pk, project_id=pk)
    if block.project.is_locked:
        return _locked(request, block.project)
    block.mix = get_object_or_404(
        MixRatio, pk=request.POST.get('mix') or 0, is_active=True,
        block_type__in=[block.block_type, MixBlockType.BOTH],
    )
    block.save(update_fields=['mix'])
    messages.success(request, f'{block.get_block_type_display()} blocks now use {block.mix.name}.')
    return redirect(f"{reverse('project_detail', args=[pk])}#block-{block.pk}")


@manager_required
@require_POST
def project_price_add_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.is_locked:
        return _locked(request, project)
    form = MaterialPriceForm(request.POST, prefix='price')
    if form.is_valid():
        price = form.save(commit=False)
        price.project = project
        price.created_by = request.user
        price.save()
        messages.success(request, f'{price.material} price for this project sent for approval.')
    else:
        messages.error(request, _first_error(form))
    return redirect(f"{reverse('project_detail', args=[pk])}#project-prices")


@manager_required
@require_POST
def project_status_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.is_locked:
        return _locked(request, project)
    status = request.POST.get('status')
    if status not in Project.Status.values or status == project.status:
        messages.error(request, 'Choose a new status.')
        return redirect('project_detail', pk=pk)

    if status == Project.Status.COMPLETED:
        estimate = estimate_project(project)
        if estimate['total'] is None:
            messages.error(
                request,
                'A project can only be completed once every block type has a chosen mix with approved prices.',
            )
            return redirect(f"{reverse('project_detail', args=[pk])}#project-status")
        with transaction.atomic():
            saved = save_estimate(project, request.user, estimate)
            project.status = status
            project.completed_at = timezone.now()
            project.save(update_fields=['status', 'completed_at', 'updated_at'])
        messages.success(
            request,
            f'Project completed. Its costs are saved as history ({money(saved.total_material_cost, saved.currency)}).',
        )
    else:
        project.status = status
        project.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Status changed to {project.get_status_display().lower()}.')
    return redirect('project_detail', pk=pk)


@manager_required
def project_edit_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.is_locked:
        return _locked(request, project)
    form = ProjectEditForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
            _save_blocks(project, form)
        messages.success(request, 'Project saved.')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'core/project_edit.html', {'form': form, 'project': project})


@manager_required
@require_POST
def project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.is_locked:
        return _locked(request, project)
    try:
        project.delete()
    except ProtectedError:
        messages.error(request, f'"{project.name}" has saved estimates or approvals, so it can\'t be deleted.')
        return redirect('project_detail', pk=pk)
    messages.success(request, f'Project "{project.name}" deleted.')
    return redirect('project_list')


# ---------- Mixes, materials and prices ----------

@config_viewer_required
def config_view(request):
    prices = latest_approved_prices()
    materials = list(Material.objects.order_by('-is_active', 'name'))
    for material in materials:
        material.current_price = prices.get(material.pk)
        material.current_unit_price = (
            price_per_base_unit(material.current_price) if material.current_price else None
        )
    context = {
        'mixes': MixRatio.objects.prefetch_related('ingredients__material').order_by('-is_active', 'name'),
        'materials': materials,
        'pending_count': MaterialPrice.objects.filter(status=MaterialPrice.Status.PENDING).count(),
        'prices': MaterialPrice.objects.select_related('material', 'project', 'created_by', 'reviewed_by')
        .order_by('-created_at')[:40],
        'material_form': MaterialForm(prefix='material'),
        'price_form': MaterialPriceForm(prefix='price'),
    }
    return render(request, 'core/config.html', context)


@manager_required
@require_POST
def material_add_view(request):
    form = MaterialForm(request.POST, prefix='material')
    if form.is_valid():
        form.save()
        messages.success(request, f'Material "{form.instance.name}" added.')
    else:
        messages.error(request, _first_error(form))
    return redirect('config')


@manager_required
def material_edit_view(request, pk):
    material = get_object_or_404(Material, pk=pk)
    form = MaterialEditForm(request.POST or None, instance=material)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Material "{material.name}" saved.')
        return redirect('config')
    used = material.mix_ingredients.exists() or material.prices.exists()
    return render(request, 'core/material_form.html', {'form': form, 'material': material, 'used': used})


@manager_required
@require_POST
def material_delete_view(request, pk):
    material = get_object_or_404(Material, pk=pk)
    try:
        material.delete()
    except ProtectedError:
        messages.error(
            request,
            f'"{material.name}" is used in mixes or prices, so it can\'t be deleted. '
            'Mark it unavailable instead.',
        )
        return redirect('material_edit', pk=pk)
    messages.success(request, f'Material "{material.name}" deleted.')
    return redirect('config')


@manager_required
@require_POST
def price_add_view(request):
    form = MaterialPriceForm(request.POST, prefix='price')
    if form.is_valid():
        price = form.save(commit=False)
        price.created_by = request.user
        price.save()
        messages.success(request, f'Price for {price.material} sent for approval.')
    else:
        messages.error(request, _first_error(form))
    return redirect('config')


@manager_required
@require_POST
def price_delete_view(request, pk):
    # Reviewed prices stay as history (business rule 2); only pending ones can be withdrawn.
    price = get_object_or_404(MaterialPrice, pk=pk, status=MaterialPrice.Status.PENDING)
    price.delete()
    messages.success(request, f'Pending price for {price.material} withdrawn.')
    return _back(request)


@price_reviewer_required
@require_POST
def price_review_view(request, pk):
    price = get_object_or_404(MaterialPrice.objects.select_related('material'), pk=pk,
                              status=MaterialPrice.Status.PENDING)
    decision = request.POST.get('decision')
    if decision not in (MaterialPrice.Status.APPROVED, MaterialPrice.Status.DECLINED):
        messages.error(request, 'Choose approve or decline.')
        return _back(request)

    corrected = None
    raw = request.POST.get('corrected_price', '').strip().replace(',', '.')
    if decision == MaterialPrice.Status.DECLINED and raw:
        try:
            corrected = Decimal(raw)
        except InvalidOperation:
            corrected = None
        if corrected is None or corrected <= 0 or corrected.as_tuple().exponent < -2:
            messages.error(request, 'Enter the correct price as a positive amount, e.g. 16.43.')
            return _back(request)

    now = timezone.now()
    with transaction.atomic():
        price.status = decision
        price.reviewed_by = request.user
        price.reviewed_at = now
        price.save()
        if corrected is not None:
            # The accountant's own figure replaces the declined one and is approved at once.
            MaterialPrice.objects.create(
                material=price.material, project=price.project, price=corrected, unit=price.unit,
                currency=price.currency,
                status=MaterialPrice.Status.APPROVED, created_by=request.user,
                reviewed_by=request.user, reviewed_at=now,
            )

    if corrected is not None:
        messages.success(request, f'Price for {price.material} declined and set to {corrected} {price.currency}.')
    else:
        messages.success(request, f'Price for {price.material} {decision}.')
    return _back(request)


@manager_required
def mix_edit_view(request, pk=None):
    mix = get_object_or_404(MixRatio, pk=pk) if pk else MixRatio()
    form = MixRatioForm(request.POST or None, instance=mix)
    formset = MixIngredientFormSet(request.POST or None, instance=mix)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            mix = form.save()
            formset.instance = mix
            formset.save()
        messages.success(request, f'Mix "{mix.name}" saved.')
        return redirect('config')
    return render(request, 'core/mix_form.html', {'form': form, 'formset': formset, 'mix': mix})


@manager_required
@require_POST
def mix_delete_view(request, pk):
    mix = get_object_or_404(MixRatio, pk=pk)
    mix.delete()
    messages.success(request, f'Mix "{mix.name}" deleted.')
    return redirect('config')


def _locked(request, project):
    messages.error(request, f'"{project.name}" is completed and kept as history, so it can\'t be changed.')
    return redirect('project_detail', pk=project.pk)


def _back(request):
    """Redirect to the page the form came from (the 'next' field), or the config page."""
    target = request.POST.get('next', '')
    if url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return redirect(target)
    return redirect('config')


def _first_error(form):
    for errors in form.errors.values():
        return errors[0]
    return 'Please check the form.'
