import math
from decimal import Decimal

from .models import MaterialPrice, MixBlockType, MixRatio

# "Divide the cost of one cubic metre sand/stone by 16 to get 1 wheelbarrow price."
WHEELBARROWS_PER_M3 = Decimal('16')


def price_per_base_unit(price):
    """Price of one base unit of the material, converting m³ prices to wheelbarrows."""
    if price.unit == 'm3' and price.material.base_unit == 'wheelbarrow':
        return price.price / WHEELBARROWS_PER_M3
    return price.price


def latest_approved_prices(project=None):
    """Map material_id -> the approved MaterialPrice to use (business rule 1).

    Default prices (no project) apply everywhere; when a project is given, its own
    approved prices replace the defaults for the materials they cover.
    """
    approved = (
        MaterialPrice.objects.filter(status=MaterialPrice.Status.APPROVED)
        .select_related('material')
        .order_by('material_id', '-reviewed_at', '-created_at')
    )
    prices = {}
    for price in approved.filter(project__isnull=True):
        prices.setdefault(price.material_id, price)
    if project is not None:
        overrides = {}
        for price in approved.filter(project=project):
            overrides.setdefault(price.material_id, price)
        prices.update(overrides)
    return prices


def estimate_block(block, prices=None):
    """Cost of producing one ProjectBlock line with every active mix usable for its block type.

    Returns a list of options sorted cheapest first. Options with a missing price
    have total=None and are listed last. The mix the manager chose for the block line
    is marked 'selected'; nothing is selected until they choose.
    """
    if prices is None:
        prices = latest_approved_prices(block.project)

    mixes = (
        MixRatio.objects.filter(is_active=True, block_type__in=[block.block_type, MixBlockType.BOTH])
        .prefetch_related('ingredients__material')
    )
    options = []
    for mix in mixes:
        batches = math.ceil(block.quantity / mix.blocks_per_batch)
        lines = []
        total = Decimal('0')
        missing = []
        for ingredient in mix.ingredients.all():
            quantity = ingredient.quantity * batches
            price = prices.get(ingredient.material_id)
            subtotal = None
            if price is None:
                missing.append(ingredient.material.name)
            else:
                unit_price = price_per_base_unit(price)
                subtotal = (quantity * unit_price).quantize(Decimal('0.01'))
                total += subtotal
            lines.append({
                'material': ingredient.material,
                'quantity': quantity,
                'unit': ingredient.unit,
                'unit_price': unit_price.quantize(Decimal('0.01')) if price else None,
                'currency': price.currency if price else None,
                'project_price': bool(price and price.project_id),
                'subtotal': subtotal,
            })
        below_strength = (
            block.required_strength_mpa is not None
            and mix.strength_mpa is not None
            and mix.strength_mpa < block.required_strength_mpa
        )
        has_total = bool(lines) and not missing
        options.append({
            'mix': mix,
            'batches': batches,
            'blocks_produced': batches * mix.blocks_per_batch,
            # Cost per block of one batch, as in the mix ratio sheet (e.g. Batch 1 = R 6,11).
            'cost_per_block': (total / batches / mix.blocks_per_batch).quantize(Decimal('0.01'))
            if has_total else None,
            'lines': lines,
            'missing_prices': missing,
            'total': total if has_total else None,
            'currency': next((line['currency'] for line in lines if line['currency']), None),
            'below_strength': below_strength,
        })

    options.sort(key=lambda o: (o['total'] is None, o['total'] or 0))
    priced = [o for o in options if o['total'] is not None and not o['below_strength']]
    if priced:
        priced[0]['cheapest'] = True

    selected = next((o for o in options if block.mix_id and o['mix'].pk == block.mix_id), None)
    if selected:
        selected['selected'] = True
    return options


def estimate_project(project):
    """Every block line with its mix options, plus the project total from the mixes the manager chose."""
    prices = latest_approved_prices(project)
    lines = []
    for block in project.blocks.select_related('mix').order_by('block_type'):  # full (F) before half (H)
        options = estimate_block(block, prices)
        lines.append({
            'block': block,
            'options': options,
            'best': next((o for o in options if o.get('cheapest')), None),
            'selected': next((o for o in options if o.get('selected')), None),
            'any_priced': any(o['total'] is not None for o in options),
        })

    selected = [line['selected'] for line in lines]
    complete = bool(lines) and all(s is not None and s['total'] is not None for s in selected)
    unchosen = [line['block'] for line in lines if line['selected'] is None]
    currencies = sorted({s['currency'] for s in selected if s and s['currency']})
    total = sum((s['total'] for s in selected if s and s['total'] is not None), Decimal('0'))
    blocks = sum(line['block'].quantity for line in lines)
    return {
        'lines': lines,
        'prices': prices,
        'total': total if complete else None,
        'currency': currencies[0] if len(currencies) == 1 else None,
        'mixed_currencies': len(currencies) > 1,
        'unchosen': unchosen,
        'blocks': blocks,
        'cost_per_block': (total / blocks).quantize(Decimal('0.01')) if complete and blocks else None,
    }
