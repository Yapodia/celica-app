from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from celica_web.models import Utilisateur, Test, Cours, Module, Planning, Question, Notification, Resultat

class Command(BaseCommand):
    help = 'Crée des groupes avec des permissions spécifiques'

    def handle(self, *args, **options):
        # Récupérer ou créer les groupes
        apprenant_group, created = Group.objects.get_or_create(name='Apprenant')
        instructeur_group, created = Group.objects.get_or_create(name='Instructeur')

        # Attribuer les permissions au groupe Apprenant
        apprenant_permissions = [
            ('passer_tests', Test),
            ('consulter_resultats', Resultat),
            ('consulter_cours', Cours),
            ('consulter_notifications', Notification),
            ('acceder_aide', Utilisateur),
        ]

        for perm_codename, model in apprenant_permissions:
            content_type = ContentType.objects.get_for_model(model)
            permission = Permission.objects.get(codename=perm_codename, content_type=content_type)
            apprenant_group.permissions.add(permission)
            self.stdout.write(self.style.SUCCESS(f"Permission {perm_codename} ajoutée au groupe Apprenant"))

        # Attribuer les permissions au groupe Instructeur
        instructeur_permissions = [
            ('gerer_cours', Cours),
            ('gerer_tests', Test),
            ('gerer_notifications', Notification),
            ('gerer_modules', Module),
            ('gerer_plannings', Planning),
            ('gerer_questions', Question),
            ('consulter_resultats', Resultat),
        ]

        for perm_codename, model in instructeur_permissions:
            content_type = ContentType.objects.get_for_model(model)
            permission = Permission.objects.get(codename=perm_codename, content_type=content_type)
            instructeur_group.permissions.add(permission)
            self.stdout.write(self.style.SUCCESS(f"Permission {perm_codename} ajoutée au groupe Instructeur"))

        self.stdout.write(self.style.SUCCESS('Groupes mis à jour avec succès et permissions attribuées.'))