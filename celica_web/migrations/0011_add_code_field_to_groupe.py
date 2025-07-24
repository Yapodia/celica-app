# Generated manually to add missing 'code' field to Groupe model

from django.db import migrations, models
from django.utils import timezone


def generate_unique_codes(apps, schema_editor):
    """Génère des codes uniques pour les groupes existants"""
    Groupe = apps.get_model('celica_web', 'Groupe')
    
    # Récupérer tous les groupes
    groupes = Groupe.objects.all()
    
    for i, groupe in enumerate(groupes, 1):
        # Générer un code basé sur le nom ou un numéro séquentiel
        if groupe.nom:
            # Prendre les 3 premières lettres du nom
            base_code = ''.join([c.upper() for c in groupe.nom if c.isalpha()])[:3]
            if len(base_code) < 3:
                base_code = base_code.ljust(3, 'X')
        else:
            base_code = 'GRP'
        
        # Créer un code unique
        code_unique = f"{base_code}-{i:03d}"
        
        # Vérifier l'unicité et ajuster si nécessaire
        counter = i
        while Groupe.objects.filter(code=code_unique).exists():
            counter += 1
            code_unique = f"{base_code}-{counter:03d}"
        
        # Assigner le code
        groupe.code = code_unique
        groupe.save()


def reverse_generate_unique_codes(apps, schema_editor):
    """Inverse la génération de codes"""
    Groupe = apps.get_model('celica_web', 'Groupe')
    Groupe.objects.all().update(code='')


class Migration(migrations.Migration):

    dependencies = [
        ('celica_web', '0010_fix_all_extra_fields'),
    ]

    operations = [
        # Ajouter le champ code sans contrainte unique d'abord
        migrations.AddField(
            model_name='groupe',
            name='code',
            field=models.CharField(blank=True, help_text='Code unique du groupe', max_length=20),
        ),
        migrations.AddField(
            model_name='groupe',
            name='date_creation',
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.AddField(
            model_name='groupe',
            name='date_modification',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='groupe',
            name='actif',
            field=models.BooleanField(default=True),
        ),
        # Générer des codes uniques pour les groupes existants
        migrations.RunPython(
            generate_unique_codes,
            reverse_generate_unique_codes
        ),
        # Maintenant ajouter la contrainte unique
        migrations.AlterField(
            model_name='groupe',
            name='code',
            field=models.CharField(blank=True, help_text='Code unique du groupe', max_length=20, unique=True),
        ),
    ] 