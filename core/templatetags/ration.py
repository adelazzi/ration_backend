from decimal import Decimal

from django import template

register = template.Library()

TONES = ['sand', 'stone', 'cement']
EXTRA_TONES = ['extra-1', 'extra-2', 'extra-3']


@register.filter
def material_tone(material):
    """CSS tone for a material, so sand/stone/cement keep the same colour everywhere."""
    name = material.name.lower()
    if 'sand' in name:
        return 'sand'
    if 'stone' in name or 'gravel' in name:
        return 'stone'
    if 'cement' in name:
        return 'cement'
    return EXTRA_TONES[material.pk % len(EXTRA_TONES)]


@register.simple_tag
def recipe_segments(mix):
    """Ingredients of a mix with their share of the batch in measures (wheelbarrows/pockets)."""
    ingredients = list(mix.ingredients.all())
    total = sum((i.quantity for i in ingredients), Decimal('0'))
    if not total:
        return []
    return [
        {
            'material': i.material,
            'quantity': i.quantity,
            'unit': i.unit,
            'percent': f'{i.quantity / total * 100:.2f}',
            'tone': material_tone(i.material),
        }
        for i in ingredients
    ]


@register.filter
def decimal(value):
    """Turn a saved number string (from an estimate snapshot) back into a Decimal."""
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value))
    except ArithmeticError:
        return None


@register.filter
def money(value, currency='ZAR'):
    if value is None:
        return ''
    currency = (currency or 'ZAR').upper()
    symbol = 'R' if currency == 'ZAR' else currency
    return f'{symbol} {value:,.2f}'


@register.filter
def unit_label(unit):
    return 'm³' if unit == 'm3' else unit


@register.filter
def measure(quantity, unit):
    """'3 wheelbarrows', '1 bag', '2.5 wheelbarrows'."""
    text = f'{quantity.normalize():f}' if isinstance(quantity, Decimal) else str(quantity)
    if quantity != 1 and unit and not unit.endswith('s'):
        unit = f'{unit}s'
    return f'{text} {unit}'
