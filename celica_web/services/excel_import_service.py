"""
Service d'import Excel pour les tests et questions
Gère l'import de fichiers Excel avec validation et traitement des erreurs
"""

import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from celica_web.models import Test, Question, Reponse, Module

logger = logging.getLogger(__name__)

class ExcelImportService:
    """Service pour l'import de tests depuis des fichiers Excel"""
    
    # Colonnes attendues pour l'onglet Test
    TEST_COLUMNS = {
        'titre': 'Titre du test',
        'description': 'Description',
        'duree': 'Durée (minutes)',
        'bareme': 'Barème total',
        'randomize': 'Mélanger les questions'
    }
    
    # Colonnes attendues pour l'onglet Questions
    QUESTION_COLUMNS = {
        'type': 'Type',
        'enonce': 'Énoncé',
        'niveau': 'Niveau',
        'points': 'Points',
        'reponse_1': 'Réponse 1',
        'reponse_2': 'Réponse 2',
        'reponse_3': 'Réponse 3',
        'reponse_4': 'Réponse 4',
        'reponse_5': 'Réponse 5',
        'explication': 'Explication'
    }
    
    # Types de questions valides
    VALID_QUESTION_TYPES = ['QCM', 'QRL']
    
    # Niveaux de difficulté valides
    VALID_DIFFICULTY_LEVELS = ['facile', 'moyen', 'difficile']
    
    def __init__(self, user: User):
        self.user = user
        self.errors = []
        self.warnings = []
        self.imported_count = 0
        
    def import_test_from_excel(self, file_path: str, module: Module) -> Tuple[bool, Test, List[str]]:
        """
        Importe un test complet depuis un fichier Excel
        
        Args:
            file_path: Chemin vers le fichier Excel
            module: Module de destination
            
        Returns:
            Tuple (success, test_instance, messages)
        """
        try:
            # Lire les onglets du fichier Excel
            test_info = self._read_test_info(file_path)
            questions_data = self._read_questions_data(file_path)
            
            # Valider les données
            self._validate_test_info(test_info)
            self._validate_questions_data(questions_data)
            
            # Créer le test
            test = self._create_test(test_info, module)
            
            # Créer les questions
            self._create_questions(questions_data, test)
            
            # Vérifier la cohérence finale
            self._validate_final_consistency(test, test_info)
            
            return True, test, self.errors + self.warnings
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import Excel: {str(e)}")
            self.errors.append(f"Erreur critique: {str(e)}")
            return False, None, self.errors
    
    def _read_test_info(self, file_path: str) -> Dict:
        """Lit les informations du test depuis l'onglet 'Test'"""
        try:
            # Essayer de lire l'onglet 'Test'
            test_df = pd.read_excel(file_path, sheet_name='Test', header=None)
            
            # Convertir en dictionnaire
            test_info = {}
            for _, row in test_df.iterrows():
                if pd.notna(row[0]) and pd.notna(row[1]):
                    key = str(row[0]).strip().lower()
                    value = row[1]
                    
                    # Nettoyer les clés
                    if 'titre' in key:
                        test_info['titre'] = str(value).strip()
                    elif 'description' in key:
                        test_info['description'] = str(value).strip()
                    elif 'durée' in key or 'duree' in key:
                        test_info['duree'] = int(value) if pd.notna(value) else 30
                    elif 'barème' in key or 'bareme' in key:
                        test_info['bareme'] = float(value) if pd.notna(value) else 0
                    elif 'mélanger' in key or 'randomize' in key:
                        test_info['randomize'] = str(value).lower() in ['oui', 'yes', 'true', '1']
            
            return test_info
            
        except Exception as e:
            logger.warning(f"Impossible de lire l'onglet Test: {str(e)}")
            # Retourner des valeurs par défaut
            return {
                'titre': 'Test importé',
                'description': 'Test importé depuis Excel',
                'duree': 30,
                'bareme': 0,
                'randomize': True
            }
    
    def _read_questions_data(self, file_path: str) -> List[Dict]:
        """Lit les questions depuis l'onglet 'Questions'"""
        try:
            # Essayer de lire l'onglet 'Questions'
            questions_df = pd.read_excel(file_path, sheet_name='Questions')
            
            questions_data = []
            for index, row in questions_df.iterrows():
                if pd.isna(row.get('Type', '')) or str(row['Type']).strip() == '':
                    continue
                
                # Récupérer le nom du module (colonne 'Module' ou 'module')
                module_nom = str(row.get('Module', '') or row.get('module', '')).strip()
                
                question_data = {
                    'type': str(row.get('Type', 'QCM')).strip(),
                    'enonce': str(row.get('Énoncé', '')).strip(),
                    'niveau': str(row.get('Niveau', 'moyen')).strip(),
                    'points': float(row.get('Points', 1.0)),
                    'explication': str(row.get('Explication', '')).strip(),
                    'reponses': [],
                    'module_nom': module_nom
                }
                
                # Traiter les réponses
                for i in range(1, 6):
                    reponse_key = f'Réponse {i}'
                    if reponse_key in row and pd.notna(row[reponse_key]):
                        reponse_text = str(row[reponse_key]).strip()
                        if reponse_text:
                            # Détecter si c'est une réponse correcte (contient ✓)
                            est_correcte = '✓' in reponse_text
                            texte_clean = reponse_text.replace('✓', '').strip()
                            
                            question_data['reponses'].append({
                                'texte': texte_clean,
                                'est_correcte': est_correcte
                            })
                
                questions_data.append(question_data)
            
            return questions_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des questions: {str(e)}")
            raise ValidationError(f"Impossible de lire les questions: {str(e)}")
    
    def _validate_test_info(self, test_info: Dict):
        """Valide les informations du test"""
        if not test_info.get('titre'):
            self.errors.append("Le titre du test est obligatoire")
        
        if test_info.get('duree', 0) <= 0:
            self.errors.append("La durée doit être supérieure à 0")
        elif test_info.get('duree', 0) > 180:
            self.warnings.append("La durée semble élevée (> 180 minutes)")
        
        if test_info.get('bareme', 0) < 0:
            self.errors.append("Le barème ne peut pas être négatif")
    
    def _validate_questions_data(self, questions_data: List[Dict]):
        """Valide les données des questions"""
        if not questions_data:
            self.errors.append("Aucune question trouvée dans le fichier")
            return
        
        total_points = 0
        
        for i, question_data in enumerate(questions_data, 1):
            # Validation du type
            if question_data['type'] not in self.VALID_QUESTION_TYPES:
                self.errors.append(f"Question {i}: Type invalide '{question_data['type']}'. Types valides: {', '.join(self.VALID_QUESTION_TYPES)}")
            
            # Validation de l'énoncé
            if not question_data['enonce']:
                self.errors.append(f"Question {i}: L'énoncé est obligatoire")
            
            # Validation du niveau
            if question_data['niveau'] not in self.VALID_DIFFICULTY_LEVELS:
                self.warnings.append(f"Question {i}: Niveau '{question_data['niveau']}' non reconnu. Utilisation du niveau 'moyen'")
                question_data['niveau'] = 'moyen'
            
            # Validation des points
            if question_data['points'] <= 0:
                self.errors.append(f"Question {i}: Les points doivent être supérieurs à 0")
            elif question_data['points'] > 10:
                self.warnings.append(f"Question {i}: Les points semblent élevés (> 10)")
            
            total_points += question_data['points']
            
            # Validation des réponses
            self._validate_question_responses(question_data, i)
        
        # Validation du total des points
        if total_points == 0:
            self.errors.append("Le total des points est égal à 0")
    
    def _validate_question_responses(self, question_data: Dict, question_index: int):
        """Valide les réponses d'une question"""
        reponses = question_data['reponses']
        
        if question_data['type'] == 'QCM':
            if len(reponses) < 2:
                self.errors.append(f"Question {question_index}: Un QCM doit avoir au moins 2 réponses")
            elif len(reponses) > 6:
                self.warnings.append(f"Question {question_index}: Un QCM avec plus de 6 réponses peut être confus")
            
            # Vérifier qu'il y a exactement une réponse correcte
            correct_count = sum(1 for r in reponses if r['est_correcte'])
            if correct_count == 0:
                self.errors.append(f"Question {question_index}: Un QCM doit avoir exactement une réponse correcte")
            elif correct_count > 1:
                self.errors.append(f"Question {question_index}: Un QCM ne peut avoir qu'une seule réponse correcte")
        
        elif question_data['type'] == 'QRL':
            if len(reponses) == 0:
                self.errors.append(f"Question {question_index}: Une QRL doit avoir au moins une réponse correcte")
            elif len(reponses) > 5:
                self.warnings.append(f"Question {question_index}: Une QRL avec plus de 5 réponses correctes peut être excessive")
            
            # Vérifier qu'il y a au moins une réponse correcte
            correct_count = sum(1 for r in reponses if r['est_correcte'])
            if correct_count == 0:
                self.errors.append(f"Question {question_index}: Une QRL doit avoir au moins une réponse correcte")
    
    def _create_test(self, test_info: Dict, module: Module) -> Test:
        """Crée le test dans la base de données"""
        test = Test.objects.create(
            titre=test_info['titre'],
            description=test_info.get('description', ''),
            module=module,
            instructeur=self.user,
            duree=test_info['duree'],
            bareme=test_info['bareme'],
            randomize_questions=test_info.get('randomize', True),
            actif=True
        )
        
        logger.info(f"Test créé: {test.titre} (ID: {test.id})")
        return test
    
    def _create_questions(self, questions_data: List[Dict], test: Test):
        """Crée les questions dans la base de données"""
        for i, question_data in enumerate(questions_data, 1):
            try:
                # Chercher le module par son nom si fourni, sinon utiliser test.module
                module_obj = test.module
                if question_data.get('module_nom'):
                    try:
                        module_obj = Module.objects.get(intitule__iexact=question_data['module_nom'])
                    except Module.DoesNotExist:
                        self.errors.append(f"Question {i}: Module '{question_data['module_nom']}' introuvable.")
                        continue
                # Créer la question
                question = Question.objects.create(
                    enonce=question_data['enonce'],
                    type_question=question_data['type'],
                    niveau_difficulte=question_data['niveau'],
                    ponderation=question_data['points'],
                    module=module_obj,
                    test=test,
                    instructeur=self.user,
                    explication=question_data.get('explication', ''),
                    ordre=i,
                    actif=True
                )
                
                # Créer les réponses
                for j, reponse_data in enumerate(question_data['reponses'], 1):
                    Reponse.objects.create(
                        question=question,
                        texte=reponse_data['texte'],
                        est_correcte=reponse_data['est_correcte'],
                        ordre=j
                    )
                
                self.imported_count += 1
                logger.info(f"Question {i} créée: {question.enonce[:50]}...")
                
            except Exception as e:
                self.errors.append(f"Erreur lors de la création de la question {i}: {str(e)}")
                logger.error(f"Erreur création question {i}: {str(e)}")
    
    def _validate_final_consistency(self, test: Test, test_info: Dict):
        """Valide la cohérence finale du test"""
        # Vérifier que le barème correspond au total des points
        total_points = sum(q.ponderation for q in test.questions.all())
        
        if test_info.get('bareme', 0) > 0 and abs(total_points - test_info['bareme']) > 0.01:
            self.warnings.append(f"Le barème total ({test_info['bareme']}) ne correspond pas à la somme des points ({total_points})")
        # Ne jamais modifier test.bareme automatiquement ici
        
        # Vérifier le nombre de questions
        question_count = test.questions.count()
        if question_count == 0:
            self.errors.append("Aucune question n'a été créée")
        elif question_count < 3:
            self.warnings.append(f"Le test ne contient que {question_count} question(s), ce qui peut être insuffisant")
    
    def get_import_summary(self) -> Dict:
        """Retourne un résumé de l'import"""
        return {
            'imported_count': self.imported_count,
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }


class ExcelImportValidator:
    """Classe pour valider les fichiers Excel avant import"""
    
    @staticmethod
    def validate_file_structure(file_path: str) -> Tuple[bool, List[str]]:
        """
        Valide la structure du fichier Excel
        
        Returns:
            Tuple (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Vérifier que le fichier peut être lu
            excel_file = pd.ExcelFile(file_path)
            
            # Vérifier les onglets requis
            required_sheets = ['Questions']
            missing_sheets = [sheet for sheet in required_sheets if sheet not in excel_file.sheet_names]
            
            if missing_sheets:
                errors.append(f"Onglets manquants: {', '.join(missing_sheets)}")
            
            # Vérifier l'onglet Questions
            if 'Questions' in excel_file.sheet_names:
                questions_df = pd.read_excel(file_path, sheet_name='Questions')
                
                # Vérifier les colonnes requises
                required_columns = ['Type', 'Énoncé', 'Points']
                missing_columns = [col for col in required_columns if col not in questions_df.columns]
                
                if missing_columns:
                    errors.append(f"Colonnes manquantes dans l'onglet Questions: {', '.join(missing_columns)}")
                
                # Vérifier qu'il y a des données
                if len(questions_df) == 0:
                    errors.append("L'onglet Questions est vide")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Erreur lors de la validation du fichier: {str(e)}")
            return False, errors 