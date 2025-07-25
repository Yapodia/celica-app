# Generated by Django 5.1.7 on 2025-07-11 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celica_web', '0029_securityviolation'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilisateur',
            name='doit_changer_mot_de_passe',
            field=models.BooleanField(default=False, help_text="L'utilisateur doit changer son mot de passe à la prochaine connexion"),
        ),
    ]
