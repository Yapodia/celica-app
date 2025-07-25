# Generated by Django 5.2.1 on 2025-07-01 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celica_web', '0021_add_instructeurs_to_groupe'),
    ]

    operations = [
        migrations.AddField(
            model_name='planning',
            name='groupes',
            field=models.ManyToManyField(blank=True, help_text='Groupes concernés par ce planning', related_name='plannings_groupes', to='celica_web.groupe'),
        ),
    ]
