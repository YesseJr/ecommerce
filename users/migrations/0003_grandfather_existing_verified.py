from django.db import migrations


def grandfather_existing_users(apps, schema_editor):
    """
    Email verification is being enforced at login for the first time.
    Accounts created before this point never had a chance to verify —
    blocking them now would lock out real, already-trusted users.
    Only accounts registered from here forward go through the new flow.
    """
    User = apps.get_model('users', 'User')
    User.objects.filter(is_verified=False).update(is_verified=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_loginactivity'),
    ]

    operations = [
        migrations.RunPython(grandfather_existing_users, noop_reverse),
    ]
