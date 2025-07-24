from django.core.management.base import BaseCommand
from django.db import transaction
from celica_web.models import Utilisateur


class Command(BaseCommand):
    help = 'Nettoie les utilisateurs avec des rôles ou statuts obsolètes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les changements',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY RUN - Aucun changement ne sera effectué'))
        
        with transaction.atomic():
            # 1. Nettoyer les utilisateurs avec le rôle 'visiteur'
            visitors = Utilisateur.objects.filter(role='visiteur')
            if visitors.exists():
                self.stdout.write(f"Trouvé {visitors.count()} utilisateur(s) avec le rôle 'visiteur'")
                if not dry_run:
                    visitors.update(role='apprenant')
                    self.stdout.write(self.style.SUCCESS('Utilisateurs "visiteur" convertis en "apprenant"'))
                else:
                    self.stdout.write('SERAIT: Convertir les utilisateurs "visiteur" en "apprenant"')
            else:
                self.stdout.write('Aucun utilisateur avec le rôle "visiteur" trouvé')
            
            # 2. Nettoyer les utilisateurs avec le statut 'en_attente'
            en_attente = Utilisateur.objects.filter(statut='en_attente')
            if en_attente.exists():
                self.stdout.write(f"Trouvé {en_attente.count()} utilisateur(s) avec le statut 'en_attente'")
                if not dry_run:
                    en_attente.update(statut='actif')
                    self.stdout.write(self.style.SUCCESS('Utilisateurs "en_attente" convertis en "actif"'))
                else:
                    self.stdout.write('SERAIT: Convertir les utilisateurs "en_attente" en "actif"')
            else:
                self.stdout.write('Aucun utilisateur avec le statut "en_attente" trouvé')
            
            # 3. Afficher un résumé des utilisateurs par rôle et statut
            self.stdout.write('\n=== RÉSUMÉ DES UTILISATEURS ===')
            for role, _ in Utilisateur._meta.get_field('role').choices:
                count = Utilisateur.objects.filter(role=role).count()
                self.stdout.write(f"Rôle '{role}': {count} utilisateur(s)")
            
            self.stdout.write('\n=== PAR STATUT ===')
            for statut, _ in Utilisateur._meta.get_field('statut').choices:
                count = Utilisateur.objects.filter(statut=statut).count()
                self.stdout.write(f"Statut '{statut}': {count} utilisateur(s)")
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\nNettoyage terminé avec succès!'))
        else:
            self.stdout.write(self.style.WARNING('\nDRY RUN terminé - Aucun changement effectué')) 