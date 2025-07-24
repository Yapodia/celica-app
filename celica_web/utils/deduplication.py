"""
Utilitaires pour la déduplication des questions dans la banque
"""

from django.db.models import Q
from ..models import Question, Reponse


def verifier_question_existante(enonce, module, type_question, instructeur=None, tolerance=0.8):
    """
    Vérifie si une question similaire existe déjà dans la banque
    
    Args:
        enonce: Énoncé de la question à vérifier
        module: Module de la question
        type_question: Type de question (QCM/QRL)
        instructeur: Instructeur qui crée la question (optionnel)
        tolerance: Seuil de similarité (0.0 à 1.0)
    
    Returns:
        tuple: (existe, question_similaire, score_similarite)
    """
    from difflib import SequenceMatcher
    
    # Normaliser l'énoncé
    enonce_normalise = enonce.strip().lower()
    
    # Chercher les questions existantes dans le même module et du même type
    questions_existantes = Question.objects.filter(
        module=module,
        type_question=type_question,
        test__isnull=True  # Questions de la banque uniquement
    )
    
    # Si un instructeur est spécifié, prioriser ses questions
    if instructeur:
        questions_instructeur = questions_existantes.filter(instructeur=instructeur)
        if questions_instructeur.exists():
            questions_existantes = questions_instructeur
    
    meilleure_similarite = 0.0
    question_la_plus_similaire = None
    
    for question in questions_existantes:
        # Calculer la similarité
        similarite = SequenceMatcher(None, enonce_normalise, question.enonce.strip().lower()).ratio()
        
        if similarite > meilleure_similarite:
            meilleure_similarite = similarite
            question_la_plus_similaire = question
    
    # Vérifier si la similarité dépasse le seuil
    existe = meilleure_similarite >= tolerance
    
    return existe, question_la_plus_similaire, meilleure_similarite


def creer_question_sans_doublon(enonce, type_question, niveau_difficulte, ponderation, 
                               module, instructeur, explication='', test=None):
    """
    Crée une question en vérifiant qu'elle n'existe pas déjà
    
    Args:
        enonce: Énoncé de la question
        type_question: Type de question (QCM/QRL)
        niveau_difficulte: Niveau de difficulté
        ponderation: Pondération de la question
        module: Module de la question
        instructeur: Instructeur qui crée la question
        explication: Explication de la question (optionnel)
        test: Test associé (optionnel)
    
    Returns:
        tuple: (question_creée, était_doublon, message)
    """
    # Vérifier si une question similaire existe
    existe, question_similaire, score = verifier_question_existante(
        enonce, module, type_question, instructeur
    )
    
    if existe:
        message = f"Question similaire trouvée (similarité: {score:.1%}). "
        if question_similaire:
            message += f"Question existante: '{question_similaire.enonce[:50]}...'"
        return None, True, message
    
    # Créer la nouvelle question
    question = Question.objects.create(
        enonce=enonce,
        type_question=type_question,
        niveau_difficulte=niveau_difficulte,
        ponderation=ponderation,
        module=module,
        test=test,
        instructeur=instructeur,
        explication=explication
    )
    
    return question, False, "Question créée avec succès"


def ajouter_reponses_sans_doublon(question, reponses_data):
    """
    Ajoute des réponses à une question en évitant les doublons
    
    Args:
        question: Question à laquelle ajouter les réponses
        reponses_data: Liste de dictionnaires avec 'texte' et 'est_correcte'
    
    Returns:
        int: Nombre de réponses ajoutées
    """
    reponses_ajoutees = 0
    textes_existants = set()
    
    for reponse_data in reponses_data:
        texte = reponse_data.get('texte', '').strip()
        est_correcte = reponse_data.get('est_correcte', False)
        
        if not texte:
            continue
        
        # Normaliser le texte pour la comparaison
        texte_normalise = texte.lower().strip()
        
        # Vérifier si cette réponse existe déjà
        if texte_normalise in textes_existants:
            continue
        
        # Vérifier si une réponse similaire existe déjà dans la base
        reponse_existante = question.reponses.filter(
            texte__iexact=texte
        ).first()
        
        if reponse_existante:
            continue
        
        # Créer la nouvelle réponse
        Reponse.objects.create(
            question=question,
            texte=texte,
            est_correcte=est_correcte
        )
        
        textes_existants.add(texte_normalise)
        reponses_ajoutees += 1
    
    return reponses_ajoutees


def nettoyer_doublons_questions(queryset=None):
    """
    Nettoie les doublons existants dans le queryset fourni (par défaut banque)
    Args:
        queryset: Queryset de questions à analyser (None = banque)
    Returns:
        dict: Statistiques du nettoyage
    """
    from difflib import SequenceMatcher
    from .models import Question

    stats = {
        'questions_analysées': 0,
        'doublons_trouvés': 0,
        'questions_supprimées': 0,
        'erreurs': []
    }

    # Utiliser le queryset fourni ou la banque par défaut
    if queryset is None:
        queryset = Question.objects.filter(test__isnull=True).order_by('module', 'type_question')
    else:
        queryset = queryset.order_by('module', 'type_question')

    # Grouper par module et type
    groupes = {}
    for question in queryset:
        key = (question.module, question.type_question)
        if key not in groupes:
            groupes[key] = []
        groupes[key].append(question)

    # Analyser chaque groupe
    for (module, type_question), questions in groupes.items():
        stats['questions_analysées'] += len(questions)
        questions_a_supprimer = set()
        for i, question1 in enumerate(questions):
            if question1.id in questions_a_supprimer:
                continue
            for j, question2 in enumerate(questions[i+1:], i+1):
                if question2.id in questions_a_supprimer:
                    continue
                similarite = SequenceMatcher(
                    None,
                    question1.enonce.strip().lower(),
                    question2.enonce.strip().lower()
                ).ratio()
                if similarite > 0.9:
                    stats['doublons_trouvés'] += 1
                    if question1.date_creation <= question2.date_creation:
                        questions_a_supprimer.add(question2.id)
                    else:
                        questions_a_supprimer.add(question1.id)
        for question_id in questions_a_supprimer:
            try:
                question = Question.objects.get(id=question_id)
                question.delete()
                stats['questions_supprimées'] += 1
            except Exception as e:
                stats['erreurs'].append(f"Erreur suppression question {question_id}: {str(e)}")
    return stats


def suggerer_questions_similaires(enonce, module, type_question, limite=5):
    """
    Suggère des questions similaires existantes
    
    Args:
        enonce: Énoncé de la question
        module: Module de la question
        type_question: Type de question
        limite: Nombre maximum de suggestions
    
    Returns:
        list: Liste des questions suggérées avec leur score de similarité
    """
    from difflib import SequenceMatcher
    
    # Récupérer les questions existantes
    questions_existantes = Question.objects.filter(
        module=module,
        type_question=type_question,
        test__isnull=True
    )
    
    suggestions = []
    enonce_normalise = enonce.strip().lower()
    
    for question in questions_existantes:
        similarite = SequenceMatcher(None, enonce_normalise, question.enonce.strip().lower()).ratio()
        
        if similarite > 0.3:  # Seuil minimum de similarité
            suggestions.append({
                'question': question,
                'similarite': similarite
            })
    
    # Trier par similarité décroissante et limiter
    suggestions.sort(key=lambda x: x['similarite'], reverse=True)
    return suggestions[:limite] 