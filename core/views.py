from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User

from .forms import MaterialForm, MaterialPriceForm, MixIngredientFormSet, MixRatioForm, ProjectForm
from .models import Material, MaterialPrice, MixRatio, Project, ProjectBlock
from .services import estimate_block, latest_approved_prices


def can_review_prices(user):
    return user.is_superuser or user.role == User.Role.ACCOUNTANT


@login_required
def home_view(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            for block_type, quantity in form.block_quantities():
                ProjectBlock.objects.create(
                    project=project,
                    block_type=block_type,
                    quantity=quantity,
                    required_strength_mpa=form.cleaned_data['required_strength_mpa'],
                )
        return redirect('project_detail', pk=project.pk)

    projects = Project.objects.filter(created_by=request.user).order_by('-created_at')[:10]
    return render(request, 'core/home.html', {'form': form, 'projects': projects})


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(Project.objects.prefetch_related('blocks'), pk=pk)
    prices = latest_approved_prices()
    blocks = [
        {'block': block, 'options': estimate_block(block, prices)}
        for block in project.blocks.all()
    ]
    return render(request, 'core/project_detail.html', {'project': project, 'blocks': blocks})


@login_required
def config_view(request):
    context = {
        'mixes': MixRatio.objects.prefetch_related('ingredients__material').order_by('block_type', 'name'),
        'materials': Material.objects.order_by('name'),
        'prices': MaterialPrice.objects.select_related('material', 'created_by', 'reviewed_by')
        .order_by('-created_at')[:30],
        'material_form': MaterialForm(prefix='material'),
        'price_form': MaterialPriceForm(prefix='price'),
        'can_review': can_review_prices(request.user),
    }
    return render(request, 'core/config.html', context)


@login_required
@require_POST
def material_add_view(request):
    form = MaterialForm(request.POST, prefix='material')
    if form.is_valid():
        form.save()
        messages.success(request, f'Material "{form.instance.name}" added.')
    else:
        messages.error(request, _first_error(form))
    return redirect('config')


@login_required
@require_POST
def price_add_view(request):
    form = MaterialPriceForm(request.POST, prefix='price')
    if form.is_valid():
        price = form.save(commit=False)
        price.created_by = request.user
        price.save()
        messages.success(request, f'Price for {price.material} added and waiting for approval.')
    else:
        messages.error(request, _first_error(form))
    return redirect('config')


@login_required
@require_POST
def price_review_view(request, pk):
    if not can_review_prices(request.user):
        raise PermissionDenied
    price = get_object_or_404(MaterialPrice, pk=pk, status=MaterialPrice.Status.PENDING)
    decision = request.POST.get('decision')
    if decision not in (MaterialPrice.Status.APPROVED, MaterialPrice.Status.DECLINED):
        messages.error(request, 'Unknown decision.')
        return redirect('config')
    price.status = decision
    price.reviewed_by = request.user
    price.reviewed_at = timezone.now()
    price.save()
    messages.success(request, f'Price for {price.material} {decision}.')
    return redirect('config')


@login_required
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


def _first_error(form):
    for errors in form.errors.values():
        return errors[0]
    return 'Please check the form.'
