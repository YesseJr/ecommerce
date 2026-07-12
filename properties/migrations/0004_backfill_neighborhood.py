from django.db import migrations


def backfill_neighborhood(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    for prop in Property.objects.all():
        if prop.neighborhood or not prop.address:
            continue
        part = prop.address.split(',')[0].strip()
        if prop.city and part.lower().endswith(prop.city.lower()):
            part = part[:-(len(prop.city))].strip()
        if part:
            prop.neighborhood = part[:100]
            prop.save(update_fields=['neighborhood'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0003_property_neighborhood'),
    ]

    operations = [
        migrations.RunPython(backfill_neighborhood, noop_reverse),
    ]
