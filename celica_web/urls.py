from django.contrib.auth import views as auth_views
from django.urls import path, include
from . import views
from django.contrib import admin


app_name = 'celica_web'

urlpatterns = [
    # --------------------------------------
    # Pages d'accueil
    # --------------------------------------
    path('', views.visitor_index, name='visitor_index'),
    path('index/', views.index, name='index'),

    # --------------------------------------
    # Authentification
    # --------------------------------------
    path('login/', views.login_view, name='login'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='celicaweb/password_reset.html',
        email_template_name='celicaweb/password_reset_email.html',
        success_url='/password-reset/done/',
        from_email='teninmireillepriscabeba@gmail.com',
    ), name='password_reset'),
    path('custom-password-reset/', views.custom_password_reset, name='custom_password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='celicaweb/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='celicaweb/password_reset_confirm.html',
        success_url='/reset/done/',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='celicaweb/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('logout/', views.logout_view, name='logout'),
    path('apprenantdashboard/', views.apprenant_dashboard, name='apprenant_dashboard'),
    path('instructeur/dashboard/', views.instructeur_dashboard, name='instructeur_dashboard'),
    path('login/admindashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/', admin.site.urls,name='admin'),

    # --------------------------------------
    # Gestion des utilisateurs
    # --------------------------------------
    path('utilisateur/add/', views.utilisateur_add_view, name='utilisateur_add'),
    path('utilisateur/list/', views.gerer_utilisateurs, name='gerer_utilisateurs'),
    path('utilisateur/edit/<int:user_id>/', views.modifier_profil, name='utilisateur_edit'),
    path('utilisateur/delete/<int:user_id>/', views.supprimer_utilisateur, name='utilisateur_delete'),
    path('utilisateur/change-password/<int:user_id>/', views.changer_mot_de_passe, name='utilisateur_changer_mot_de_passe'),
    path('utilisateur/rechercher/', views.rechercher_utilisateur, name='rechercher_utilisateur'),


    # --------------------------------------
    # Gestion des cours (gerer_cours)
    # --------------------------------------
    path('cours/list/', views.all_cours_list, name='cours_list'),
    path('cours/list/apprenant/', views.mes_cours, name='mes_cours'),
    path('cours/detail/<int:pk>/', views.cours_detail, name='cours_detail'),
    path('cours/new/', views.cours_form_new, name='cours_form_new'),
    path('cours/edit/<int:cours_id>/', views.cours_form_edit, name='cours_form_edit'),
    path('cours/import/', views.importer_cours_depuis_pdf, name='cours_import'),
    path('cours/export/<int:pk>/<str:format_fichier>/', views.exporter_cours, name='cours_export'),
    path('cours/delete/<int:pk>/', views.supprimer_cours, name='cours_delete'),

    # --------------------------------------
    # Gestion des tests (gerer_tests)
    # --------------------------------------


    # Dans urls.py, ajouter cette ligne :
    path('test/preview/<int:test_id>/', views.test_preview, name='test_preview'),
    path('test/list/', views.test_list, name='test_list'),
    path('test/duplicate/<int:test_id>/', views.test_duplicate, name='test_duplicate'),

    path('test/add/', views.test_form, name='test_add'),
    path('test/edit/<int:test_id>/', views.test_form, name='test_edit'),
    path('test/delete/<int:test_id>/', views.test_delete, name='test_delete'),
    # URLs pour la gestion des tests
    path('test/form/', views.test_form, name='test_form'),
    path('test/form/<int:test_id>/', views.test_form, name='test_form_edit'),

    path('test/import/', views.importer_test_depuis_fichier, name='test_import'),
    path('test/import-excel/', views.import_test_excel, name='import_test_excel'),
    path('test/download-template/', views.download_excel_template, name='download_excel_template'),
    path('test/preview-excel/', views.preview_excel_import, name='preview_excel_import'),
    path('test/new/', views.test_form, name='test_form_new'),  # URL manquante
    path('test/export/<int:pk>/<str:format_fichier>/', views.exporter_test, name='test_export'),
    path('test/generer/', views.generer_test_automatique, name='generer_test_automatique'),
    path('test/passer/<int:test_id>/', views.passer_test, name='passer_test'),
    path('test/<int:test_id>/add-questions/', views.ajouter_questions_existantes, name='ajouter_questions_existantes'),
    path('test/list/apprenant/', views.apprenant_tests, name='apprenant_tests'),
    # Ajoutez cette ligne dans urlpatterns
    #path('test/duplicate/<int:test_id>/', views.test_duplicate, name='test_duplicate'),
    # --------------------------------------
    # Gestion des questions (gerer_questions)
    # --------------------------------------
    path('question/new/', views.question_form_new, name='question_form'),
    path('question/<int:question_id>/edit/', views.question_form_edit, name='question_form_edit'),
    path('question/list/', views.question_list, name='question_list'),
    path('question/import/', views.importer_questions, name='question_import'),
    path('test/<int:test_id>/import-questions/', views.importer_questions, name='importer_questions'),
    path('question/remplacer/<int:question_id>/<int:test_id>/', views.remplacer_question, name='remplacer_question'),
    # Ajouter cette ligne dans urlpatterns
    path('question/delete/<int:question_id>/', views.supprimer_question, name='supprimer_question'),
    path('test/<int:test_id>/question/<int:question_id>/delete/', views.delete_question_ajax, name='delete_question_ajax'),
    path('question/nettoyer-doublons/', views.nettoyer_doublons_questions, name='nettoyer_doublons_questions'),
    path('ajax/questions-existantes/', views.ajax_questions_existantes, name='ajax_questions_existantes'),

    # --------------------------------------
    # Gestion des notifications (gerer_notifications)
    # --------------------------------------
    path('notification/marquer-lue/<int:notification_id>/', views.marquer_lue, name='marquer_lue'),
    path('notification/add/', views.notification_form, name='notification_add'),
    path('notification/new/', views.notification_form, name='notification_form_new'),
    path('notification/edit/<int:notification_id>/', views.notification_form_edit, name='notification_form_edit'),
    path('notification/list/', views.notification_list, name='notification_list'),
    path('notification/delete/<int:id>/', views.supprimer_notification, name='supprimer_notification'),
    path('notification/mes-notifications/', views.lister_notifications, name='lister_notifications'),
    path('notification/marquer-lue/<int:notification_id>/', views.marquer_notification_lue, name='marquer_notification_lue'),

    # --------------------------------------
    # Gestion des modules (gerer_modules)
    # --------------------------------------
    path('module/list/', views.module_list, name='module_list'),
    path('module/new/', views.module_form, name='module_form_new'),
    path('module/edit/<int:module_id>/', views.module_form, name='module_form_edit'),
    path('module/delete/<int:module_id>/', views.supprimer_module, name='module_delete'),

    # --------------------------------------
    # Gestion des résultats
    # --------------------------------------
    path('resultats/list/<int:test_id>/', views.test_resultats, name='test_resultats'),
    path('resultats/mes-resultats/', views.mes_resultats, name='mes_resultats'),
    path('resultats/test-termine/<int:resultat_id>/', views.resultat_test_termine, name='resultat_test_termine'),
    path('resultats/detail/<int:resultat_id>/', views.resultat_detail_instructeur, name='resultat_detail_instructeur'),
    path('resultats/apprenants/', views.resultats_apprenants, name='resultats_apprenants'),
    path('resultats/add/<int:test_id>/', views.resultat_form, name='resultat_add'),
    path('resultats/export/<int:pk>/<str:format_fichier>/', views.exporter_resultat, name='resultat_export'),

    # --------------------------------------
    # Gestion des plannings
    # --------------------------------------
    path('planning/list/', views.planning_list, name='planning_list'),
    path('planning/add/', views.planning_form, name='planning_add'),
    path('planning/edit/<int:planning_id>/', views.planning_form, name='planning_edit'),
    path('planning/delete/<int:planning_id>/', views.supprimer_planning, name='planning_delete'),
    path('planning/export/<int:pk>/<str:format_fichier>/', views.exporter_planning, name='planning_export'),
    path('planning/list/apprenant/', views.apprenant_plannings, name='apprenant_plannings'),
    path('planning/list/instructeur/', views.consulter_plannings_instructeur, name='consulter_plannings_instructeur'),

    # --------------------------------------
    # Gestion des groupes
    # --------------------------------------
    path('groupe/list/', views.groupe_list, name='groupe_list'),
    path('groupe/add/', views.groupe_form, name='groupe_add'),
    path('groupe/edit/<int:groupe_id>/', views.groupe_form, name='groupe_edit'),
    path('groupe/delete/<int:groupe_id>/', views.supprimer_groupe, name='groupe_delete'),
    path('groupe/<int:groupe_id>/gerer-membres/', views.groupe_gerer_membres, name='groupe_gerer_membres'),

    # --------------------------------------
    # Gestion des statistiques
    # --------------------------------------
    path('statistiques/list/', views.consulter_statistiques, name='consulter_statistiques'),
    path('statistiques/export/<int:pk>/<str:format_fichier>/', views.exporter_statistiques, name='statistiques_export'),

    # --------------------------------------
    # Gestion de l'aide et à propos
    # --------------------------------------
    path('aide/list/', views.consulter_aide, name='consulter_aide'),
    path('aide/rechercher/', views.rechercher_aide, name='rechercher_aide'),
    path('a-propos/', views.consulter_a_propos, name='consulter_a_propos'),
    
    # --------------------------------------
    # Diagnostic et débogage (admin/instructeur uniquement)
    # --------------------------------------
    path('diagnostic/plannings/', views.diagnostic_plannings, name='diagnostic_plannings'),
    path('test/terminated/', views.test_terminated, name='test_terminated'),
    path('test/security-violation/', views.security_violation, name='security_violation'),
    
    # --------------------------------------
    # Journalisation des événements de test
    # --------------------------------------
    path('log-test-event/', views.log_test_event, name='log_test_event'),
    path('test/<int:test_id>/event-logs/', views.test_event_logs, name='test_event_logs'),
    path('test/<int:test_id>/user/<int:user_id>/events/', views.user_test_events, name='user_test_events'),
    path('journalisation-surveillance/', views.journalisation_surveillance, name='journalisation_surveillance'),
    
    # --------------------------------------
    # Gestion des violations de sécurité
    # --------------------------------------
    path('violation/delete/<int:violation_id>/', views.supprimer_violation, name='supprimer_violation'),
    path('violation/delete-all/', views.supprimer_toutes_violations, name='supprimer_toutes_violations'),
    
    # --------------------------------------
    # Gestion des événements de test
    # --------------------------------------
    path('events/delete-all/', views.supprimer_tous_evenements, name='supprimer_tous_evenements'),
]