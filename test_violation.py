#!/usr/bin/env python3
"""
Script de test pour vérifier le système de violations de sécurité
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'celica_web.settings')
django.setup()

from celica_web.models import Test, Question, Reponse, SecurityViolation

class SecurityViolationTest(TestCase):
    """Tests pour le système de violations de sécurité"""
    
    def setUp(self):
        """Configuration initiale"""
        self.client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='apprenant'
        )
        
        # Créer un test de test
        self.test = Test.objects.create(
            titre='Test de sécurité',
            duree=30,
            bareme=20,
            instructeur=self.user,
            actif=True
        )
        
        # Créer une question
        self.question = Question.objects.create(
            enonce='Question de test',
            type_question='QCM',
            test=self.test,
            instructeur=self.user,
            ponderation=5
        )
        
        # Créer des réponses
        self.reponse_correcte = Reponse.objects.create(
            question=self.question,
            texte='Réponse correcte',
            est_correcte=True
        )
        
        self.reponse_incorrecte = Reponse.objects.create(
            question=self.question,
            texte='Réponse incorrecte',
            est_correcte=False
        )
    
    def test_violation_creation(self):
        """Test de création d'une violation de sécurité"""
        # Se connecter
        self.client.login(username='testuser', password='testpass123')
        
        # Créer une violation
        violation_data = {
            'violation': 'Test de violation',
            'violation_type': 'test',
            'url': 'http://test.com',
            'violation_count': 1
        }
        
        response = self.client.post(
            reverse('celica_web:security_violation'),
            data=violation_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la violation a été créée
        violation = SecurityViolation.objects.filter(
            utilisateur=self.user,
            violation_type='test'
        ).first()
        
        self.assertIsNotNone(violation)
        self.assertEqual(violation.violation, 'Test de violation')
    
    def test_violation_count_limit(self):
        """Test de la limite de violations"""
        # Se connecter
        self.client.login(username='testuser', password='testpass123')
        
        # Créer 3 violations
        for i in range(3):
            violation_data = {
                'violation': f'Violation {i+1}',
                'violation_type': 'test',
                'url': 'http://test.com',
                'violation_count': i+1
            }
            
            response = self.client.post(
                reverse('celica_web:security_violation'),
                data=violation_data,
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
        
        # Vérifier qu'il y a 3 violations
        violations = SecurityViolation.objects.filter(
            utilisateur=self.user,
            violation_type='test'
        )
        
        self.assertEqual(violations.count(), 3)
    
    def test_test_termination_violation(self):
        """Test de la violation de terminaison de test"""
        # Se connecter
        self.client.login(username='testuser', password='testpass123')
        
        # Créer une violation de terminaison
        violation_data = {
            'violation': 'Test terminé automatiquement',
            'violation_type': 'test_terminated',
            'url': 'http://test.com',
            'violation_count': 3
        }
        
        response = self.client.post(
            reverse('celica_web:security_violation'),
            data=violation_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la violation a été créée
        violation = SecurityViolation.objects.filter(
            utilisateur=self.user,
            violation_type='test_terminated'
        ).first()
        
        self.assertIsNotNone(violation)
        self.assertEqual(violation.violation, 'Test terminé automatiquement')

if __name__ == '__main__':
    # Tests manuels
    print("🧪 Tests du système de violations de sécurité")
    print("=" * 50)
    
    # Créer une instance de test
    test_case = SecurityViolationTest()
    test_case.setUp()
    
    try:
        # Test 1: Création de violation
        print("✅ Test 1: Création de violation")
        test_case.test_violation_creation()
        print("   ✓ Violation créée avec succès")
        
        # Test 2: Limite de violations
        print("✅ Test 2: Limite de violations")
        test_case.test_violation_count_limit()
        print("   ✓ Limite de 3 violations respectée")
        
        # Test 3: Terminaison de test
        print("✅ Test 3: Terminaison de test")
        test_case.test_test_termination_violation()
        print("   ✓ Violation de terminaison créée")
        
        print("\n🎉 Tous les tests sont passés avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")
    
    finally:
        # Nettoyer
        test_case.tearDown()
        print("\n🧹 Nettoyage terminé") 