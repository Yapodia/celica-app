"""
Utilitaires pour le tirage aléatoire de questions depuis la banque
"""

import random
from django.db.models import Q, Sum
from ..models import Question, Reponse


def effectuer_tirage_aleatoire_questions(test, nombre_questions, filtres=None, options=None):
    """
    Effectue un tirage aléatoire de questions depuis la banque pour un test
    
    Args:
        test: Instance du test
        nombre_questions: Nombre de questions à tirer
        filtres: Dict avec les filtres optionnels (module, niveau, type, ponderation_max)
        options: Dict avec les options (equilibrer_types, equilibrer_difficultes, eviter_doublons, optimiser_bareme)
    
    Returns:
        tuple: (success, questions_selectionnees, message, statistiques)
    """
    
    # Initialiser les filtres et options par défaut
    filtres = filtres or {}
    options = options or {}
    
    # Calculer la pondération disponible
    somme_actuelle = test.questions.aggregate(total=Sum('ponderation'))['total'] or 0
    ponderation_disponible = test.bareme - somme_actuelle
    
    if ponderation_disponible <= 0:
        return False, [], "Le barème du test est déjà atteint ou dépassé.", {}
    
    # Base query pour les questions disponibles
    questions_query = Question.objects.all()
    
    # Exclure les questions déjà dans le test si demandé
    if options.get('eviter_doublons', True):
        questions_deja_dans_test = test.questions.values_list('id', flat=True)
        questions_query = questions_query.exclude(id__in=questions_deja_dans_test)
    
    # Appliquer les filtres
    if filtres.get('module_filter_aleatoire') and filtres['module_filter_aleatoire'] != 'tous':
        questions_query = questions_query.filter(module_id=filtres['module_filter_aleatoire'])
    
    if filtres.get('niveau_filter_aleatoire') and filtres['niveau_filter_aleatoire'] != 'tous':
        questions_query = questions_query.filter(niveau_difficulte=filtres['niveau_filter_aleatoire'])
    
    if filtres.get('type_question_filter_aleatoire') and filtres['type_question_filter_aleatoire'] != 'tous':
        questions_query = questions_query.filter(type_question=filtres['type_question_filter_aleatoire'])
    
    if filtres.get('ponderation_max_aleatoire'):
        try:
            ponderation_max = float(filtres['ponderation_max_aleatoire'])
            questions_query = questions_query.filter(ponderation__lte=ponderation_max)
        except ValueError:
            pass
    
    # Inclure toutes les questions : banque (test=NULL) + autres tests du même module 
    # mais exclure le test courant pour éviter les doublons
    questions_query = questions_query.filter(
        Q(test__isnull=True) |  # Questions de la banque
        Q(module=test.module)   # Questions du même module dans d'autres tests
    ).exclude(test=test)  # Exclure le test courant
    
    # Récupérer toutes les questions disponibles
    questions_disponibles = list(questions_query.select_related('module').prefetch_related('reponses'))
    
    if not questions_disponibles:
        return False, [], "Aucune question disponible selon les critères sélectionnés.", {}
    
    # Statistiques sur les questions disponibles
    stats = {
        'total_disponibles': len(questions_disponibles),
        'par_type': {},
        'par_niveau': {},
        'ponderation_totale_disponible': sum(q.ponderation for q in questions_disponibles)
    }
    
    for question in questions_disponibles:
        # Stats par type
        stats['par_type'][question.type_question] = stats['par_type'].get(question.type_question, 0) + 1
        # Stats par niveau
        stats['par_niveau'][question.niveau_difficulte] = stats['par_niveau'].get(question.niveau_difficulte, 0) + 1
    
    # Algorithme de sélection
    questions_selectionnees = []
    ponderation_utilisee = 0
    tentatives_max = nombre_questions * 10  # Éviter les boucles infinies
    tentatives = 0
    
    # Stratégies d'équilibrage
    if options.get('equilibrer_types', True) and options.get('equilibrer_difficultes', True):
        # Tri sophistiqué avec équilibrage
        questions_par_categorie = {}
        for question in questions_disponibles:
            cle = f"{question.type_question}_{question.niveau_difficulte}"
            if cle not in questions_par_categorie:
                questions_par_categorie[cle] = []
            questions_par_categorie[cle].append(question)
        
        # Mélanger chaque catégorie
        for cle in questions_par_categorie:
            random.shuffle(questions_par_categorie[cle])
        
        # Sélection équilibrée
        categories = list(questions_par_categorie.keys())
        index_categorie = 0
        
        while len(questions_selectionnees) < nombre_questions and tentatives < tentatives_max:
            tentatives += 1
            
            # Sélectionner la catégorie suivante en rotation
            if categories:
                categorie_actuelle = categories[index_categorie % len(categories)]
                
                if questions_par_categorie[categorie_actuelle]:
                    question_candidate = questions_par_categorie[categorie_actuelle].pop(0)
                    
                    # Vérifier si l'ajout est possible
                    if ponderation_utilisee + question_candidate.ponderation <= ponderation_disponible:
                        questions_selectionnees.append(question_candidate)
                        ponderation_utilisee += question_candidate.ponderation
                        
                        # Si optimisation pour le barème, vérifier si on est proche du maximum
                        if options.get('optimiser_bareme', True):
                            if ponderation_utilisee >= ponderation_disponible * 0.95:  # 95% du barème
                                break
                
                index_categorie += 1
                
                # Nettoyer les catégories vides
                categories = [c for c in categories if questions_par_categorie[c]]
    
    else:
        # Sélection aléatoire simple
        questions_melangees = questions_disponibles.copy()
        random.shuffle(questions_melangees)
        
        for question in questions_melangees:
            if len(questions_selectionnees) >= nombre_questions:
                break
            
            if ponderation_utilisee + question.ponderation <= ponderation_disponible:
                questions_selectionnees.append(question)
                ponderation_utilisee += question.ponderation
                
                # Si optimisation pour le barème
                if options.get('optimiser_bareme', True):
                    if ponderation_utilisee >= ponderation_disponible * 0.95:
                        break
    
    # Construire le message de résultat
    if not questions_selectionnees:
        message = "Aucune question n'a pu être sélectionnée avec les critères choisis."
        return False, [], message, stats
    
    # Statistiques finales
    stats_finales = {
        'questions_selectionnees': len(questions_selectionnees),
        'ponderation_utilisee': ponderation_utilisee,
        'ponderation_disponible': ponderation_disponible,
        'taux_utilisation': (ponderation_utilisee / ponderation_disponible * 100) if ponderation_disponible > 0 else 0,
        'repartition_types': {},
        'repartition_niveaux': {}
    }
    
    for question in questions_selectionnees:
        # Répartition par type
        stats_finales['repartition_types'][question.type_question] = stats_finales['repartition_types'].get(question.type_question, 0) + 1
        # Répartition par niveau
        stats_finales['repartition_niveaux'][question.niveau_difficulte] = stats_finales['repartition_niveaux'].get(question.niveau_difficulte, 0) + 1
    
    if len(questions_selectionnees) == nombre_questions:
        message = f"Tirage réussi ! {len(questions_selectionnees)} questions sélectionnées pour {ponderation_utilisee:.1f} points."
    else:
        message = f"Tirage partiel : {len(questions_selectionnees)} questions sur {nombre_questions} demandées, pour {ponderation_utilisee:.1f} points."
    
    return True, questions_selectionnees, message, {**stats, 'selection': stats_finales}


def ajouter_questions_tirage_au_test(test, questions_selectionnees, user):
    """
    Ajoute les questions sélectionnées par tirage aléatoire au test en créant des copies
    
    Args:
        test: Instance du test
        questions_selectionnees: Liste des questions à ajouter
        user: Utilisateur qui effectue l'action
    
    Returns:
        tuple: (success, nb_ajoutees, message)
    """
    questions_ajoutees = 0
    erreurs = []
    
    for question_originale in questions_selectionnees:
        try:
            # Créer une copie de la question
            nouvelle_question = Question.objects.create(
                enonce=question_originale.enonce,
                type_question=question_originale.type_question,
                niveau_difficulte=question_originale.niveau_difficulte,
                ponderation=question_originale.ponderation,
                explication=question_originale.explication,
                module=test.module,  # Associer au module du test
                test=test,  # Associer directement au test
                instructeur=user
            )
            
            # Copier les réponses pour les QCM
            if question_originale.type_question == 'QCM':
                for reponse_originale in question_originale.reponses.all():
                    Reponse.objects.create(
                        question=nouvelle_question,
                        texte=reponse_originale.texte,
                        est_correcte=reponse_originale.est_correcte
                    )
            
            questions_ajoutees += 1
            
        except Exception as e:
            erreurs.append(f"Question '{question_originale.enonce[:50]}...': {str(e)}")
    
    # Construire le message de résultat
    if questions_ajoutees == len(questions_selectionnees):
        message = f"✅ Toutes les {questions_ajoutees} questions ont été ajoutées avec succès au test."
        success = True
    elif questions_ajoutees > 0:
        message = f"⚠️ {questions_ajoutees} questions sur {len(questions_selectionnees)} ont été ajoutées. Erreurs: {'; '.join(erreurs[:3])}"
        success = True
    else:
        message = f"❌ Aucune question n'a pu être ajoutée. Erreurs: {'; '.join(erreurs[:3])}"
        success = False
    
    return success, questions_ajoutees, message 