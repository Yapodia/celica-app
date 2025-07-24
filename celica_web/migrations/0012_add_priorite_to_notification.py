# Generated manually to add missing 'priorite' field to Notification model

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('celica_web', '0011_add_code_field_to_groupe'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='priorite',
            field=models.CharField(
                choices=[('basse', 'Basse'), ('normale', 'Normale'), ('haute', 'Haute'), ('critique', 'Critique')],
                default='normale',
                max_length=20
            ),
        ),
    ] 