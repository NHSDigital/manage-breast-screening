# Generated by Django 5.1.7 on 2025-03-31 09:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clinics', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clinic',
            old_name='setting_id',
            new_name='setting',
        ),
        migrations.RenameField(
            model_name='clinicslot',
            old_name='clinic_id',
            new_name='clinic',
        ),
        migrations.RenameField(
            model_name='setting',
            old_name='provider_id',
            new_name='provider',
        ),
    ]
