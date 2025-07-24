from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('celica_web', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "SELECT 1;",  # Migration vide car nous avons déjà ajouté les colonnes
            reverse_sql="SELECT 1;"
        ),
    ]