from django.db import migrations

SEEDED_MIXES = ['Batch 1', 'Batch 2', 'Batch 3', 'Batch 4 (optimum)']


def to_both(apps, schema_editor):
    apps.get_model('core', 'MixRatio').objects.filter(name__in=SEEDED_MIXES, block_type='F').update(block_type='B')


class Migration(migrations.Migration):
    dependencies = [('core', '0003_mix_block_type_both')]

    operations = [migrations.RunPython(to_both, migrations.RunPython.noop)]
