# Generated by Django 5.1.7 on 2025-07-11 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celica_web', '0032_alter_utilisateur_statut'),
    ]

    operations = [
        migrations.AlterField(
            model_name='utilisateur',
            name='statut',
            field=models.CharField(choices=[('en_attente', 'En attente'), ('actif', 'Actif'), ('inactif', 'Inactif'), ('suspendu', 'Suspendu')], default='actif', max_length=10),
        ),
    ]
