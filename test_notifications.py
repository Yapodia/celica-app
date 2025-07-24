#!/usr/bin/env python3
"""
Script de test pour vérifier les notifications de violation de sécurité
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celica_app.settings')
django.setup()

from celica_web.models import Utilisateur, Notification, SecurityViolation, Test
from django.utils import timezone

def test_notifications():
    print("=== TEST DES NOTIFICATIONS ===")
    
    # 1. Vérifier les utilisateurs
    print("\n1. Utilisateurs disponibles:")
    instructeurs = Utilisateur.objects.filter(role='instructeur', statut='actif')
    admins = Utilisateur.objects.filter(role='admin', statut='actif')
    apprenants = Utilisateur.objects.filter(role='apprenant', statut='actif')
    
    print(f"   - Instructeurs: {instructeurs.count()}")
    for instr in instructeurs:
        print(f"     * {instr.email} ({instr.get_full_name()})")
    
    print(f"   - Administrateurs: {admins.count()}")
    for admin in admins:
        print(f"     * {admin.email} ({admin.get_full_name()})")
    
    print(f"   - Apprenants: {apprenants.count()}")
    for app in apprenants[:3]:  # Afficher seulement les 3 premiers
        print(f"     * {app.email} ({app.get_full_name()})")
    
    # 2. Vérifier les tests
    print("\n2. Tests disponibles:")
    tests = Test.objects.all()
    print(f"   - Total tests: {tests.count()}")
    for test in tests[:3]:  # Afficher seulement les 3 premiers
        print(f"     * {test.titre} (ID: {test.id}) - Instructeur: {test.instructeur.email}")
    
    # 3. Vérifier les violations existantes
    print("\n3. Violations de sécurité existantes:")
    violations = SecurityViolation.objects.all()
    print(f"   - Total violations: {violations.count()}")
    for violation in violations[:3]:  # Afficher seulement les 3 premiers
        print(f"     * {violation.utilisateur.email} - {violation.violation} ({violation.violation_type})")
    
    # 4. Vérifier les notifications existantes
    print("\n4. Notifications existantes:")
    notifications = Notification.objects.all()
    print(f"   - Total notifications: {notifications.count()}")
    
    # Notifications par utilisateur
    for user in instructeurs:
        user_notifications = Notification.objects.filter(utilisateur=user, est_lue=False)
        print(f"     * {user.email}: {user_notifications.count()} notifications non lues")
        for notif in user_notifications[:2]:  # Afficher seulement les 2 premières
            print(f"       - {notif.titre} ({notif.type_notice})")
    
    # 5. Créer une notification de test
    print("\n5. Création d'une notification de test:")
    if instructeurs.exists() and admins.exists():
        instructeur_test = instructeurs.first()
        admin_test = admins.first()
        
        # Notification pour l'instructeur
        notif_instr = Notification.objects.create(
            titre="🧪 Test - Violation de sécurité",
            message="Ceci est un test de notification pour vérifier l'affichage.",
            type_notice='urgence',
            priorite='haute',
            utilisateur=instructeur_test,
            date_expiration=timezone.now() + timezone.timedelta(days=1)
        )
        print(f"   ✅ Notification créée pour {instructeur_test.email} (ID: {notif_instr.id})")
        
        # Notification pour l'admin
        notif_admin = Notification.objects.create(
            titre="🧪 Test - Violation de sécurité",
            message="Ceci est un test de notification pour vérifier l'affichage.",
            type_notice='urgence',
            priorite='haute',
            utilisateur=admin_test,
            date_expiration=timezone.now() + timezone.timedelta(days=1)
        )
        print(f"   ✅ Notification créée pour {admin_test.email} (ID: {notif_admin.id})")
        
        # 6. Vérifier les notifications après création
        print("\n6. Notifications après création:")
        for user in [instructeur_test, admin_test]:
            user_notifications = Notification.objects.filter(utilisateur=user, est_lue=False)
            print(f"   * {user.email}: {user_notifications.count()} notifications non lues")
    
    else:
        print("   ❌ Pas assez d'utilisateurs pour créer des notifications de test")
    
    print("\n=== FIN DU TEST ===")

if __name__ == "__main__":
    test_notifications() 