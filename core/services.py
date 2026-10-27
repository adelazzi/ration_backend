import math
from decimal import Decimal

from .models import MaterialPrice, MixRatio

# "Divide the cost of one cubic metre sand/stone by 16 to get 1 wheelbarrow price."
WHEELBARROWS_PER_M3 = Decimal('16')


def price_per_base_unit(price):
    """Price of one base unit of the material, converting m³ prices to wheelbarrows."""
    if price.unit == 'm3' and price.material.base_unit == 'wheelbarrow':
        return price.price / WHEELBARROWS_PER_M3
    return price.price


def latest_approved_prices():
    """Map material_id -> most recent approved MaterialPrice (business rule 1)."""
    prices = {}
    approved = MaterialPrice.objects.filter(status=MaterialPrice.Status.APPROVED).order_by(
        'material_id', '-reviewed_at', '-created_at'
    )
    for price in approved.select_related('material'):
        prices.setdefault(price.material_id, price)
    return prices


def estimate_block(block, prices=None):
    """Cost of producing one ProjectBlock line with every active mix of the same block type.

    Returns a list of options sorted cheapest first. Options with a missing price
    have total=None and are listed last.
    """
    if prices is None:
        prices = latest_approved_prices()

    mixes = (
        MixRatio.objects.filter(is_active=True, block_type=block.block_type)
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
            'below_strength': below_strength,
        })

    options.sort(key=lambda o: (o['total'] is None, o['total'] or 0))
    priced = [o for o in options if o['total'] is not None and not o['below_strength']]
    if priced:
        priced[0]['cheapest'] = True
    return options
