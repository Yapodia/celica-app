#!/usr/bin/env python3
"""
Script d'initialisation des données de journalisation et surveillance
pour le tableau de bord administrateur
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celica_app.settings')
django.setup()

from celica_web.models import Test, Utilisateur, TestEventLog, SecurityViolation, Module
from django.utils import timezone

def init_logging_data():
    """Initialise les données de journalisation pour le tableau de bord"""
    print("🚀 INITIALISATION DES DONNÉES DE JOURNALISATION")
    print("=" * 60)
    
    # 1. Vérifier/créer les données de base
    print("\n1. Vérification des données de base...")
    
    # Récupérer ou créer un utilisateur de test
    try:
        user = Utilisateur.objects.filter(role='apprenant').first()
        if not user:
            user = Utilisateur.objects.create_user(
                email='test@example.com',
                matricule='TEST001',
                password='testpass123',
                first_name='Test',
                last_name='User',
                role='apprenant'
            )
            print(f"✅ Utilisateur créé: {user.email}")
        else:
            print(f"✅ Utilisateur existant: {user.email}")
    except Exception as e:
        print(f"❌ Erreur création utilisateur: {e}")
        return
    
    # Récupérer ou créer un module
    try:
        module = Module.objects.filter(status='actif').first()
        if not module:
            module = Module.objects.create(
                intitule='Module Test',
                description='Module pour les tests de journalisation',
                categorie='Test',
                status='actif'
            )
            print(f"✅ Module créé: {module.intitule}")
        else:
            print(f"✅ Module existant: {module.intitule}")
    except Exception as e:
        print(f"❌ Erreur création module: {e}")
        return
    
    # Récupérer ou créer un test
    try:
        test = Test.objects.filter(module=module).first()
        if not test:
            test = Test.objects.create(
                titre='Test de Journalisation',
                description='Test pour démontrer la journalisation',
                module=module,
                instructeur=user,
                duree=30,
                bareme=20
            )
            print(f"✅ Test créé: {test.titre}")
        else:
            print(f"✅ Test existant: {test.titre}")
    except Exception as e:
        print(f"❌ Erreur création test: {e}")
        return
    
    # 2. Créer des événements de test récents
    print("\n2. Création d'événements de test...")
    
    event_types = [
        'test_start', 'test_end', 'question_view', 'question_answer',
        'page_focus', 'page_blur', 'auto_save', 'manual_save'
    ]
    
    # Créer des événements sur les 7 derniers jours
    for day in range(7):
        date = timezone.now() - timedelta(days=day)
        
        # 2-5 événements par jour
        num_events = random.randint(2, 5)
        
        for i in range(num_events):
            # Heure aléatoire dans la journée
            hour = random.randint(9, 18)
            minute = random.randint(0, 59)
            event_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            event_type = random.choice(event_types)
            
            TestEventLog.objects.create(
                test=test,
                utilisateur=user,
                event_type=event_type,
                event_data={
                    'demo': True,
                    'day': day,
                    'event_num': i
                },
                timestamp=event_time,
                ip_address='127.0.0.1',
                user_agent='Demo Script'
            )
        
        print(f"   📅 Jour {day+1}: {num_events} événements créés")
    
    # 3. Créer des violations de sécurité
    print("\n3. Création de violations de sécurité...")
    
    violation_types = [
        'copy_paste', 'keyboard_shortcut', 'right_click', 'print',
        'navigation', 'dev_tools', 'tab_switch', 'fullscreen_exit'
    ]
    
    # Créer des violations sur les 3 derniers jours
    for day in range(3):
        date = timezone.now() - timedelta(days=day)
        
        # 1-3 violations par jour
        num_violations = random.randint(1, 3)
        
        for i in range(num_violations):
            hour = random.randint(10, 17)
            minute = random.randint(0, 59)
            violation_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            violation_type = random.choice(violation_types)
            
            SecurityViolation.objects.create(
                utilisateur=user,
                violation=f"Violation de type {violation_type} détectée",
                violation_type=violation_type,
                url=f'/test/passer/{test.id}/',
                timestamp=violation_time,
                ip_address='127.0.0.1',
                user_agent='Demo Script'
            )
        
        print(f"   🚨 Jour {day+1}: {num_violations} violations créées")
    
    # 4. Créer des événements de violation dans TestEventLog
    print("\n4. Création d'événements de violation...")
    
    violations = SecurityViolation.objects.all()
    for violation in violations:
        TestEventLog.objects.create(
            test=test,
            utilisateur=user,
            event_type='violation_detected',
            event_data={
                'violation_type': violation.violation_type,
                'violation_id': violation.id,
                'demo': True
            },
            timestamp=violation.timestamp,
            ip_address='127.0.0.1',
            user_agent='Demo Script'
        )
    
    print(f"   📝 {violations.count()} événements de violation créés")
    
    # 5. Afficher les statistiques finales
    print("\n5. Statistiques finales...")
    
    total_events = TestEventLog.objects.count()
    total_violations = SecurityViolation.objects.count()
    events_30_days = TestEventLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).count()
    violations_30_days = SecurityViolation.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    print(f"📊 Total événements: {total_events}")
    print(f"📊 Total violations: {total_violations}")
    print(f"📊 Événements (30j): {events_30_days}")
    print(f"📊 Violations (30j): {violations_30_days}")
    
    # 6. Afficher les types d'événements les plus fréquents
    print("\n6. Types d'événements les plus fréquents:")
    from django.db.models import Count
    event_stats = TestEventLog.objects.values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    for stat in event_stats:
        print(f"   - {stat['event_type']}: {stat['count']}")
    
    # 7. Afficher les types de violations les plus fréquents
    print("\n7. Types de violations les plus fréquents:")
    violation_stats = SecurityViolation.objects.values('violation_type').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    for stat in violation_stats:
        print(f"   - {stat['violation_type']}: {stat['count']}")
    
    print("\n✅ Initialisation terminée avec succès!")
    print("\n📋 Prochaines étapes:")
    print("   1. Accéder au tableau de bord: http://127.0.0.1:8000/login/admindashboard/")
    print("   2. Vérifier la section 'Journalisation et surveillance'")
    print("   3. Cliquer sur 'Détails' pour voir les statistiques")
    print("   4. Cliquer sur 'Voir détails' dans 'Activité récente'")
    print("\n🔧 Pour nettoyer les données de test:")
    print("   python manage.py shell")
    print("   >>> from celica_web.models import TestEventLog, SecurityViolation")
    print("   >>> TestEventLog.objects.filter(event_data__demo=True).delete()")
    print("   >>> SecurityViolation.objects.filter(user_agent='Demo Script').delete()")

if __name__ == '__main__':
    try:
        init_logging_data()
    except KeyboardInterrupt:
        print("\n\n⏹️ Initialisation interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc() 