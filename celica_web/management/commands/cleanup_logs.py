from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from celica_web.models import TestEventLog, SecurityViolation, Notification
from django.db import models

class Command(BaseCommand):
    help = 'Nettoie automatiquement les anciens logs et notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours à conserver (défaut: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait supprimé sans le faire'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(f"🧹 Nettoyage des données de plus de {days} jours...")
        self.stdout.write(f"📅 Date limite: {cutoff_date.strftime('%d/%m/%Y %H:%M')}")

        # 1. Nettoyer les événements de test
        test_events = TestEventLog.objects.filter(timestamp__lt=cutoff_date)
        test_events_count = test_events.count()
        
        if dry_run:
            self.stdout.write(f"📝 Événements de test à supprimer: {test_events_count}")
        else:
            test_events.delete()
            self.stdout.write(f"✅ {test_events_count} événements de test supprimés")

        # 2. Nettoyer les violations de sécurité (garder plus longtemps)
        security_cutoff = timezone.now() - timedelta(days=days * 2)  # 60 jours par défaut
        violations = SecurityViolation.objects.filter(timestamp__lt=security_cutoff)
        violations_count = violations.count()
        
        if dry_run:
            self.stdout.write(f"🚨 Violations de sécurité à supprimer: {violations_count}")
        else:
            violations.delete()
            self.stdout.write(f"✅ {violations_count} violations de sécurité supprimées")

        # 3. Nettoyer les notifications expirées
        expired_notifications = Notification.objects.filter(
            models.Q(date_expiration__lt=timezone.now()) |
            models.Q(date_envoi__lt=cutoff_date, est_lue=True)
        )
        notifications_count = expired_notifications.count()
        
        if dry_run:
            self.stdout.write(f"🔔 Notifications à supprimer: {notifications_count}")
        else:
            expired_notifications.delete()
            self.stdout.write(f"✅ {notifications_count} notifications supprimées")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 Mode test - Aucune donnée supprimée"))
        else:
            self.stdout.write(self.style.SUCCESS("🎉 Nettoyage terminé avec succès!")) 