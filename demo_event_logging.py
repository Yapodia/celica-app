#!/usr/bin/env python3
"""
Script de démonstration du système de journalisation des événements de test
"""

import os
import sys
import django
from datetime import datetime, timedelta
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celica_app.settings')
django.setup()

from celica_web.models import Test, Utilisateur, TestEventLog, SecurityViolation, Module
from django.utils import timezone

def demo_event_logging():
    """Démonstration complète du système de journalisation"""
    print("🎬 DÉMONSTRATION DU SYSTÈME DE JOURNALISATION")
    print("=" * 60)
    
    # 1. Créer des données de démonstration
    print("\n1. Création des données de démonstration...")
    
    # Créer un utilisateur de démonstration
    user, created = Utilisateur.objects.get_or_create(
        email='demo@example.com',
        defaults={
            'username': 'demouser',
            'first_name': 'Demo',
            'last_name': 'User',
            'matricule': 'DEMO001',
            'role': 'apprenant'
        }
    )
    
    # Créer un module de démonstration
    module, created = Module.objects.get_or_create(
        intitule='Démonstration',
        defaults={'categorie': 'Demo', 'status': 'actif'}
    )
    
    # Créer un test de démonstration
    test, created = Test.objects.get_or_create(
        titre='Test de Démonstration - Journalisation',
        defaults={
            'module': module,
            'instructeur': user,
            'duree': 45,
            'bareme': 20
        }
    )
    
    print(f"✅ Utilisateur: {user.email}")
    print(f"✅ Test: {test.titre}")
    
    # 2. Simuler une session de test complète
    print("\n2. Simulation d'une session de test...")
    
    session_id = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    start_time = timezone.now()
    
    # Événements de début de test
    print("📝 Enregistrement des événements de début...")
    TestEventLog.log_event(
        test=test,
        utilisateur=user,
        event_type='test_start',
        event_data={
            'session_id': session_id,
            'user_agent': 'Demo Script',
            'screen_resolution': '1920x1080',
            'window_size': '1200x800'
        },
        session_id=session_id,
        ip_address='127.0.0.1',
        user_agent='Demo Script'
    )
    
    # Simuler la navigation entre les questions
    for question_num in range(1, 6):
        print(f"📝 Question {question_num}...")
        
        # Visualisation de la question
        TestEventLog.log_event(
            test=test,
            utilisateur=user,
            event_type='question_view',
            event_data={'question_text': f'Question {question_num}'},
            question_number=question_num,
            session_id=session_id,
            ip_address='127.0.0.1'
        )
        
        # Réponse à la question
        TestEventLog.log_event(
            test=test,
            utilisateur=user,
            event_type='question_answer',
            event_data={'answer': f'Réponse {question_num}', 'is_correct': True},
            question_number=question_num,
            session_id=session_id,
            ip_address='127.0.0.1'
        )
        
        # Simuler quelques événements de focus
        if question_num % 2 == 0:
            TestEventLog.log_event(
                test=test,
                utilisateur=user,
                event_type='page_blur',
                event_data={'duration_ms': 5000},
                question_number=question_num,
                session_id=session_id,
                ip_address='127.0.0.1'
            )
            
            TestEventLog.log_event(
                test=test,
                utilisateur=user,
                event_type='page_focus',
                event_data={'time_away_ms': 5000},
                question_number=question_num,
                session_id=session_id,
                ip_address='127.0.0.1'
            )
    
    # 3. Simuler des violations de sécurité
    print("\n3. Simulation de violations de sécurité...")
    
    violations = [
        {
            'type': 'copy_attempt',
            'description': 'Tentative de copier-coller détectée',
            'details': {'target': 'question_text', 'selection': 'texte sélectionné'}
        },
        {
            'type': 'right_click',
            'description': 'Clic droit détecté',
            'details': {'x': 150, 'y': 200}
        },
        {
            'type': 'keyboard_shortcut',
            'description': 'Raccourci clavier Ctrl+C détecté',
            'details': {'key': 'c', 'ctrl': True}
        }
    ]
    
    for i, violation in enumerate(violations, 1):
        print(f"🚨 Violation {i}: {violation['type']}")
        
        # Créer la violation de sécurité
        security_violation = SecurityViolation.log_violation(
            utilisateur=user,
            violation=violation['description'],
            violation_type=violation['type'],
            url=f'/test/passer/{test.id}/',
            ip_address='127.0.0.1',
            user_agent='Demo Script'
        )
        
        # Créer l'événement correspondant
        TestEventLog.log_event(
            test=test,
            utilisateur=user,
            event_type='violation_detected',
            event_data={
                'violation_type': violation['type'],
                'violation_id': security_violation.id,
                'details': violation['details']
            },
            session_id=session_id,
            ip_address='127.0.0.1'
        )
    
    # 4. Simuler des événements de fin de test
    print("\n4. Finalisation du test...")
    
    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds()
    
    TestEventLog.log_event(
        test=test,
        utilisateur=user,
        event_type='test_end',
        event_data={
            'total_duration_ms': int(duration * 1000),
            'questions_answered': 5,
            'violations_count': 3,
            'score': 15
        },
        session_id=session_id,
        ip_address='127.0.0.1'
    )
    
    # 5. Afficher les statistiques
    print("\n5. Statistiques de la session...")
    
    # Compter les événements par type
    event_counts = {}
    for event_type, _ in TestEventLog.EVENT_TYPES:
        count = TestEventLog.objects.filter(
            test=test,
            event_type=event_type
        ).count()
        if count > 0:
            event_counts[event_type] = count
    
    print("📊 Événements enregistrés:")
    for event_type, count in event_counts.items():
        print(f"   - {event_type}: {count}")
    
    # Statistiques de la session
    session_events = TestEventLog.objects.filter(
        test=test,
        session_id=session_id
    ).order_by('timestamp')
    
    print(f"\n📈 Statistiques de la session '{session_id}':")
    print(f"   - Total événements: {session_events.count()}")
    print(f"   - Durée du test: {duration:.1f} secondes")
    print(f"   - Violations détectées: {len(violations)}")
    
    # 6. Afficher la timeline des événements
    print("\n6. Timeline des événements:")
    print("-" * 40)
    
    for event in session_events[:10]:  # Afficher les 10 premiers
        timestamp = event.timestamp.strftime('%H:%M:%S')
        description = event.get_event_description()
        print(f"{timestamp} - {description}")
    
    if session_events.count() > 10:
        print(f"... et {session_events.count() - 10} autres événements")
    
    # 7. Démonstration des fonctionnalités avancées
    print("\n7. Fonctionnalités avancées...")
    
    # Recherche d'événements de violation
    violation_events = TestEventLog.objects.filter(
        test=test,
        event_type='violation_detected'
    ).select_related('utilisateur')
    
    print(f"🔍 Événements de violation trouvés: {violation_events.count()}")
    for event in violation_events:
        print(f"   - {event.timestamp.strftime('%H:%M:%S')}: {event.event_data.get('violation_type', 'unknown')}")
    
    # Analyse des patterns de focus
    focus_events = TestEventLog.objects.filter(
        test=test,
        event_type__in=['page_focus', 'page_blur']
    ).count()
    
    print(f"👁️ Événements de focus: {focus_events}")
    
    # 8. Nettoyage (optionnel)
    print("\n8. Nettoyage...")
    
    # Demander si l'utilisateur veut nettoyer
    response = input("Voulez-vous supprimer les données de démonstration ? (o/N): ")
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        TestEventLog.objects.filter(test=test).delete()
        SecurityViolation.objects.filter(utilisateur=user).delete()
        test.delete()
        user.delete()
        print("✅ Données de démonstration supprimées")
    else:
        print("✅ Données de démonstration conservées")
        print(f"   - Test ID: {test.id}")
        print(f"   - Session ID: {session_id}")
        print(f"   - Utilisateur: {user.email}")
    
    print("\n🎉 Démonstration terminée avec succès!")
    print("\n📋 Prochaines étapes:")
    print("   1. Accéder à l'interface d'administration pour voir les événements")
    print("   2. Utiliser l'interface de consultation des journaux")
    print("   3. Tester avec un vrai utilisateur")
    print("   4. Analyser les patterns de comportement")

if __name__ == '__main__':
    try:
        demo_event_logging()
    except KeyboardInterrupt:
        print("\n\n⏹️ Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc() 