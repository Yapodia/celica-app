#!/usr/bin/env python3
"""
Script de test pour le système de journalisation des événements de test
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celica_app.settings')
django.setup()

from celica_web.models import Test, Utilisateur, TestEventLog, SecurityViolation
from django.utils import timezone

def test_event_logging_system():
    """Test complet du système de journalisation"""
    print("🧪 Test du système de journalisation des événements")
    print("=" * 60)
    
    # 1. Vérifier les modèles
    print("\n1. Vérification des modèles...")
    try:
        # Créer un utilisateur de test
        user, created = Utilisateur.objects.get_or_create(
            email='test@example.com',
            defaults={
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'matricule': 'TEST001',
                'role': 'apprenant'
            }
        )
        print(f"✅ Utilisateur de test: {user.email}")
        
        # Créer un test de test
        from celica_web.models import Module
        module, created = Module.objects.get_or_create(
            intitule='Test Module',
            defaults={'categorie': 'Test', 'status': 'actif'}
        )
        
        test, created = Test.objects.get_or_create(
            titre='Test de Journalisation',
            defaults={
                'module': module,
                'instructeur': user,
                'duree': 30,
                'bareme': 20
            }
        )
        print(f"✅ Test de test: {test.titre}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données de test: {e}")
        return False
    
    # 2. Tester la création d'événements
    print("\n2. Test de création d'événements...")
    try:
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Événements de test
        test_events = [
            {
                'event_type': 'test_start',
                'event_data': {'session_id': session_id, 'user_agent': 'Test Script'},
                'question_number': None,
                'session_id': session_id
            },
            {
                'event_type': 'question_view',
                'event_data': {'question_text': 'Question 1'},
                'question_number': 1,
                'session_id': session_id
            },
            {
                'event_type': 'question_answer',
                'event_data': {'answer': 'A', 'is_correct': True},
                'question_number': 1,
                'session_id': session_id
            },
            {
                'event_type': 'page_focus',
                'event_data': {'time_away_ms': 5000},
                'question_number': 1,
                'session_id': session_id
            },
            {
                'event_type': 'question_view',
                'event_data': {'question_text': 'Question 2'},
                'question_number': 2,
                'session_id': session_id
            },
            {
                'event_type': 'question_change',
                'event_data': {'previous_answer': 'A', 'new_answer': 'B'},
                'question_number': 2,
                'session_id': session_id
            },
            {
                'event_type': 'violation_detected',
                'event_data': {'violation_type': 'copy_attempt', 'target': 'question_text'},
                'question_number': 2,
                'session_id': session_id
            },
            {
                'event_type': 'test_end',
                'event_data': {'total_duration_ms': 1800000, 'score': 15},
                'question_number': None,
                'session_id': session_id
            }
        ]
        
        # Créer les événements
        created_events = []
        for event_data in test_events:
            event = TestEventLog.log_event(
                test=test,
                utilisateur=user,
                event_type=event_data['event_type'],
                event_data=event_data['event_data'],
                question_number=event_data['question_number'],
                session_id=event_data['session_id'],
                ip_address='127.0.0.1',
                user_agent='Test Script',
                duration=1000
            )
            created_events.append(event)
            print(f"✅ Événement créé: {event.event_type} - {event.get_event_description()}")
        
        print(f"✅ {len(created_events)} événements créés avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des événements: {e}")
        return False
    
    # 3. Tester les requêtes et statistiques
    print("\n3. Test des requêtes et statistiques...")
    try:
        # Compter les événements par type
        event_counts = {}
        for event_type, _ in TestEventLog.EVENT_TYPES:
            count = TestEventLog.objects.filter(
                test=test,
                event_type=event_type
            ).count()
            if count > 0:
                event_counts[event_type] = count
        
        print("📊 Statistiques des événements:")
        for event_type, count in event_counts.items():
            print(f"   - {event_type}: {count}")
        
        # Événements de violation
        violation_events = TestEventLog.objects.filter(
            test=test,
            event_type__in=['violation_detected', 'copy_attempt', 'paste_attempt', 'right_click', 'keyboard_shortcut']
        ).count()
        print(f"   - Violations totales: {violation_events}")
        
        # Événements par utilisateur
        user_events = TestEventLog.objects.filter(
            test=test,
            utilisateur=user
        ).count()
        print(f"   - Événements utilisateur: {user_events}")
        
        # Événements par session
        session_events = TestEventLog.objects.filter(
            test=test,
            session_id=session_id
        ).count()
        print(f"   - Événements session: {session_events}")
        
    except Exception as e:
        print(f"❌ Erreur lors des requêtes: {e}")
        return False
    
    # 4. Tester les méthodes du modèle
    print("\n4. Test des méthodes du modèle...")
    try:
        # Récupérer le premier événement
        first_event = TestEventLog.objects.filter(test=test).first()
        if first_event:
            print(f"✅ Description: {first_event.get_event_description()}")
            print(f"✅ Couleur: {first_event.get_severity_color()}")
            print(f"✅ Représentation: {str(first_event)}")
        
        # Tester les filtres par sévérité
        danger_events = TestEventLog.objects.filter(test=test)
        danger_events = [e for e in danger_events if e.get_severity_color() == 'danger']
        print(f"✅ Événements critiques: {len(danger_events)}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test des méthodes: {e}")
        return False
    
    # 5. Test de performance
    print("\n5. Test de performance...")
    try:
        import time
        
        # Test de création en lot
        start_time = time.time()
        batch_events = []
        for i in range(100):
            event = TestEventLog.log_event(
                test=test,
                utilisateur=user,
                event_type='auto_save',
                event_data={'batch_number': i},
                session_id=f"batch_test_{i}",
                ip_address='127.0.0.1'
            )
            batch_events.append(event)
        
        end_time = time.time()
        print(f"✅ Création de 100 événements en {end_time - start_time:.2f} secondes")
        
        # Test de requête
        start_time = time.time()
        recent_events = TestEventLog.objects.filter(
            test=test
        ).select_related('utilisateur').order_by('-timestamp')[:50]
        end_time = time.time()
        
        print(f"✅ Requête de 50 événements en {end_time - start_time:.3f} secondes")
        
    except Exception as e:
        print(f"❌ Erreur lors du test de performance: {e}")
        return False
    
    # 6. Nettoyage
    print("\n6. Nettoyage des données de test...")
    try:
        # Supprimer les événements de test
        TestEventLog.objects.filter(test=test).delete()
        print(f"✅ Événements de test supprimés")
        
        # Supprimer le test de test
        test.delete()
        print(f"✅ Test de test supprimé")
        
        # Supprimer l'utilisateur de test
        user.delete()
        print(f"✅ Utilisateur de test supprimé")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False
    
    print("\n🎉 Tous les tests sont passés avec succès!")
    return True

def test_security_violation_integration():
    """Test de l'intégration avec les violations de sécurité"""
    print("\n🔒 Test d'intégration avec les violations de sécurité")
    print("=" * 60)
    
    try:
        # Créer des données de test
        user, created = Utilisateur.objects.get_or_create(
            email='security_test@example.com',
            defaults={
                'username': 'securitytest',
                'first_name': 'Security',
                'last_name': 'Test',
                'matricule': 'SEC001',
                'role': 'apprenant'
            }
        )
        
        from celica_web.models import Module
        module, created = Module.objects.get_or_create(
            intitule='Security Test Module',
            defaults={'categorie': 'Security', 'status': 'actif'}
        )
        
        test, created = Test.objects.get_or_create(
            titre='Test de Sécurité',
            defaults={
                'module': module,
                'instructeur': user,
                'duree': 30,
                'bareme': 20
            }
        )
        
        # Créer des violations de sécurité
        violations = [
            {
                'violation_type': 'copy_paste',
                'violation': 'Tentative de copier-coller détectée',
                'url': '/test/passer/1/'
            },
            {
                'violation_type': 'right_click',
                'violation': 'Clic droit détecté',
                'url': '/test/passer/1/'
            },
            {
                'violation_type': 'keyboard_shortcut',
                'violation': 'Raccourci clavier Ctrl+C détecté',
                'url': '/test/passer/1/'
            }
        ]
        
        created_violations = []
        for violation_data in violations:
            violation = SecurityViolation.log_violation(
                utilisateur=user,
                violation=violation_data['violation'],
                violation_type=violation_data['violation_type'],
                url=violation_data['url'],
                ip_address='127.0.0.1',
                user_agent='Security Test Script'
            )
            created_violations.append(violation)
            print(f"✅ Violation créée: {violation.violation_type} - {violation.violation}")
        
        # Créer des événements correspondants
        session_id = f"security_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        for violation in created_violations:
            event = TestEventLog.log_event(
                test=test,
                utilisateur=user,
                event_type='violation_detected',
                event_data={
                    'violation_type': violation.violation_type,
                    'violation_id': violation.id,
                    'url': violation.url
                },
                session_id=session_id,
                ip_address='127.0.0.1'
            )
            print(f"✅ Événement de violation créé: {event.get_event_description()}")
        
        # Vérifier l'intégration
        violation_events = TestEventLog.objects.filter(
            test=test,
            event_type='violation_detected'
        ).count()
        
        print(f"✅ Événements de violation: {violation_events}")
        print(f"✅ Violations de sécurité: {len(created_violations)}")
        
        # Nettoyage
        TestEventLog.objects.filter(test=test).delete()
        SecurityViolation.objects.filter(utilisateur=user).delete()
        test.delete()
        user.delete()
        
        print("✅ Test d'intégration réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Démarrage des tests du système de journalisation")
    
    # Test principal
    success1 = test_event_logging_system()
    
    # Test d'intégration
    success2 = test_security_violation_integration()
    
    if success1 and success2:
        print("\n🎉 Tous les tests sont passés avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Certains tests ont échoué!")
        sys.exit(1) 