from decimal import Decimal

from django.db import migrations

MATERIALS = [
    ('Sand', 'wheelbarrow'),
    ('Stone 13mm', 'wheelbarrow'),
    ('Cement 50kg', 'bag'),
]

# From the "Optimum Mix Ratios" sheet: (name, strength MPa, blocks per batch, {material: quantity}).
MIXES = [
    ('Batch 1', '4.8', 22, {'Sand': '3', 'Cement 50kg': '1'}),
    ('Batch 2', '5.2', 35, {'Sand': '3', 'Stone 13mm': '2', 'Cement 50kg': '1'}),
    ('Batch 3', '6.2', 35, {'Sand': '2.5', 'Stone 13mm': '2.5', 'Cement 50kg': '1'}),
    ('Batch 4 (optimum)', '7.6', 28, {'Sand': '2', 'Stone 13mm': '2', 'Cement 50kg': '1'}),
]


def seed(apps, schema_editor):
    Material = apps.get_model('core', 'Material')
    MixRatio = apps.get_model('core', 'MixRatio')
    MixIngredient = apps.get_model('core', 'MixIngredient')

    materials = {}
    for name, unit in MATERIALS:
        materials[name], _ = Material.objects.get_or_create(name=name, defaults={'base_unit': unit})

    for name, strength, blocks, ingredients in MIXES:
        if MixRatio.objects.filter(name=name).exists():
            continue
        mix = MixRatio.objects.create(
            name=name, block_type='F', strength_mpa=Decimal(strength), blocks_per_batch=blocks,
        )
        for material_name, quantity in ingredients.items():
            material = materials[material_name]
            MixIngredient.objects.create(
                mix=mix, material=material, quantity=Decimal(quantity), unit=material.base_unit,
            )


class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
