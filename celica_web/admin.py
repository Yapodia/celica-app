from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import (
    Utilisateur, Module, Test, Question, Reponse, Resultat, 
    Planning, Groupe, Notification, Cours, Statistiques, Aide, APropos, SecurityViolation, TestEventLog
)

# Enregistrement du modèle Utilisateur avec une interface personnalisée
class UtilisateurAdmin(UserAdmin):
    list_display = ('email', 'matricule', 'role', 'statut', 'last_name', 'first_name', 'doit_changer_mot_de_passe')
    list_filter = ('role', 'statut', 'specialite', 'niveau', 'doit_changer_mot_de_passe')
    search_fields = ('email', 'matricule', 'last_name', 'first_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'matricule')}),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'role', 'statut', 'specialite', 'niveau', 'doit_changer_mot_de_passe')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'matricule', 'password1', 'password2', 'role'),
        }),
    )
    # Ajout du champ doit_changer_mot_de_passe dans les champs éditables en ligne
    list_editable = ('statut', 'doit_changer_mot_de_passe')

# Admin pour Module
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('intitule', 'categorie', 'status', 'created_at', 'instructeur_principal')
    list_filter = ('status', 'categorie', 'created_at')
    search_fields = ('intitule', 'description', 'categorie')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('intitule', 'description', 'categorie')
        }),
        ('Configuration', {
            'fields': ('status', 'instructeur_principal')
        }),
        ('Relations', {
            'fields': ('groupes',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('groupes',)

# Admin pour Test
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = (
        'titre', 
        'module', 
        'instructeur', 
        'duree', 
        'bareme',
        'get_status_display',
        'date_creation'
    )
    list_filter = (
        'module', 
        'instructeur', 
        'date_creation'
    )
    search_fields = ('titre', 'description', 'module__intitule')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'description', 'module', 'instructeur')
        }),
        ('Configuration', {
            'fields': ('duree', 'bareme', 'actif')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status_display(self, obj):
        """Méthode pour afficher le statut dans l'admin"""
        return obj.status
    get_status_display.short_description = 'Statut'
    #get_status_display.admin_order_field = 'actif'

# Admin pour Question
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('enonce_court', 'type_question', 'niveau_difficulte', 'module', 'test', 'ponderation')
    list_filter = ('type_question', 'niveau_difficulte', 'module', 'test')
    search_fields = ('enonce', 'module__intitule', 'test__titre')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Question', {
            'fields': ('enonce', 'type_question', 'niveau_difficulte', 'ponderation', 'image')
        }),
        ('Relations', {
            'fields': ('module', 'test', 'instructeur')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def enonce_court(self, obj):
        """Affiche une version courte de l'énoncé"""
        return obj.enonce[:50] + '...' if len(obj.enonce) > 50 else obj.enonce
    enonce_court.short_description = 'Énoncé'

# Admin pour Reponse
@admin.register(Reponse)
class ReponseAdmin(admin.ModelAdmin):
    list_display = ('texte_court', 'question', 'est_correcte', 'date_creation')
    list_filter = ('est_correcte', 'question__type_question', 'date_creation')
    search_fields = ('texte', 'question__enonce')
    readonly_fields = ('date_creation',)
    
    def texte_court(self, obj):
        """Affiche une version courte du texte de réponse"""
        return obj.texte[:30] + '...' if len(obj.texte) > 30 else obj.texte
    texte_court.short_description = 'Texte'

@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ('test', 'apprenant', 'score', 'appreciation', 'date_passation', 'temps_ecoule')
    list_filter = ('appreciation', 'test', 'date_passation')
    search_fields = ('apprenant__email', 'test__titre', 'apprenant__last_name', 'apprenant__first_name')
    readonly_fields = ('date_passation',)
    
    fieldsets = (
        ('Résultat', {
            'fields': ('test', 'apprenant', 'score', 'appreciation', 'temps_ecoule')
        }),
        ('Métadonnées', {
            'fields': ('date_passation',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Planning)
class PlanningAdmin(admin.ModelAdmin):
    list_display = ('titre', 'groupe', 'date_debut', 'date_fin', 'statut', 'date_creation')  # CORRECTION : Supprimé 'test'
    list_filter = ('statut', 'date_debut', 'date_fin', 'date_creation')  # CORRECTION : Supprimé 'lieu', 'salle'
    search_fields = ('titre', 'groupe__nom', 'description')  # CORRECTION : Utilisé 'titre' au lieu de 'test__titre'
    readonly_fields = ('date_creation', 'date_modification')  # CORRECTION : Ajouté 'date_modification'
    
    fieldsets = (
        ('Planning', {
            'fields': ('titre', 'description', 'groupe', 'date_debut', 'date_fin', 'statut')  # CORRECTION : Supprimé 'test'
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),  # CORRECTION : Ajouté 'date_modification'
            'classes': ('collapse',)
        }),
    )

@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'date_creation')  # CORRECTION : Garder seulement les champs existants
    search_fields = ('nom', 'description')
    readonly_fields = ('date_creation', 'date_modification')  # CORRECTION : Ajouté 'date_modification'
    # filter_horizontal = ('instructeurs', 'apprenants')  # CORRECTION : Supprimé car les champs n'existent pas
    
    fieldsets = (
        ('Groupe', {
            'fields': ('nom', 'description', 'code', 'capacite_max', 'actif')  # CORRECTION : Champs du modèle
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),  # CORRECTION : Ajouté 'date_modification'
            'classes': ('collapse',)
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'utilisateur', 'type_notice', 'date_envoi', 'est_lue')
    list_filter = ('type_notice', 'est_lue', 'date_envoi')
    search_fields = ('titre', 'message', 'utilisateur__email', 'utilisateur__last_name')
    readonly_fields = ('date_envoi',)
    
    fieldsets = (
        ('Notification', {
            'fields': ('titre', 'message', 'type_notice', 'utilisateur')
        }),
        ('État', {
            'fields': ('est_lue',)
        }),
        ('Relations', {
            'fields': ('test', 'resultat')
        }),
        ('Métadonnées', {
            'fields': ('date_envoi',),
            'classes': ('collapse',)
        }),
    )

# Admin pour Cours
@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ['titre', 'module', 'instructeur', 'status', 'created_at', 'date_cloture']  # CORRECTION : Ajouté 'status'
    list_filter = ('status', 'module', 'instructeur', 'created_at', 'date_cloture')  # CORRECTION : Ajouté 'status'
    search_fields = ('titre', 'description', 'module__intitule')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Cours', {
            'fields': ('titre', 'description', 'module', 'instructeur')
        }),
        ('Contenu', {
            'fields': ('contenu', 'fichier', 'status')  # CORRECTION : Ajouté 'status'
        }),
        ('Dates', {
            'fields': ('date_cloture',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Statistiques)
class StatistiquesAdmin(admin.ModelAdmin):
    list_display = ('test', 'taux_reussite', 'periode_debut', 'periode_fin')  # CORRECTION : Supprimé 'moyenne', 'mediane', 'date_creation'
    list_filter = ('periode_debut', 'periode_fin', 'test')  # CORRECTION : Supprimé 'date_creation'
    search_fields = ('test__titre',)
    # readonly_fields = ('date_creation',)  # CORRECTION : Supprimé car le champ n'existe pas
    
    fieldsets = (
        ('Statistiques', {
            'fields': ('test', 'taux_reussite')  # CORRECTION : Supprimé 'moyenne', 'mediane'
        }),
        ('Période', {
            'fields': ('periode_debut', 'periode_fin')
        }),
    )

@admin.register(Aide)
class AideAdmin(admin.ModelAdmin):
    list_display = ('titre', 'categorie', 'module', 'date_creation', 'date_modification')
    list_filter = ('categorie', 'module', 'date_creation')
    search_fields = ('titre', 'contenu')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Aide', {
            'fields': ('titre', 'contenu', 'categorie', 'module')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

@admin.register(APropos)
class AProposAdmin(admin.ModelAdmin):
    list_display = ('nom_application', 'version', 'organisme', 'contact_email', 'date_mise_a_jour')  # CORRECTION : Ajouté tous les champs principaux
    search_fields = ('nom_application', 'version', 'organisme', 'description', 'contact_email')  # CORRECTION : Ajouté plus de champs de recherche
    readonly_fields = ('date_mise_a_jour', 'date_creation')  # CORRECTION : Ajouté 'date_creation'
    
    fieldsets = (
        ('Application', {
            'fields': ('nom_application', 'version', 'organisme', 'description')  # CORRECTION : Ajouté les champs de base
        }),
        ('Contact', {
            'fields': ('contact_email', 'contact_telephone', 'adresse', 'site_web')  # CORRECTION : Section contact
        }),
        ('Informations légales', {
            'fields': ('mentions_legales', 'politique_confidentialite'),  # CORRECTION : Section légale
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_mise_a_jour'),  # CORRECTION : Ajouté 'date_creation'
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Limite à une seule instance d'À propos"""
        if APropos.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression de l'instance unique"""
        return False

    def get_model_perms(self, request):
        """Personnalise les permissions du modèle"""
        perms = super().get_model_perms(request)
        if APropos.objects.exists():
            perms['add'] = False
        return perms


# Site d'administration personnalisé
class CustomAdminSite(admin.AdminSite):
    site_header = 'Administration CelicaWeb'
    site_title = 'CelicaWeb Admin'
    index_title = 'Tableau de bord administrateur'
    
    def each_context(self, request):
        context = super().each_context(request)
        context['site_header'] = self.site_header
        context['site_title'] = self.site_title
        context['index_title'] = self.index_title
        return context

    def login(self, request, extra_context=None):
        response = super().login(request, extra_context)
        if request.user.is_authenticated and request.user.is_superuser:
            try:
                return HttpResponseRedirect(reverse('celica_web:admin_dashboard'))
            except:
                return response
        return response

# Créer l'instance du site admin personnalisé
admin_site = CustomAdminSite(name='custom_admin')

# Enregistrer le modèle Utilisateur avec l'admin par défaut
admin.site.register(Utilisateur, UtilisateurAdmin)

@admin.register(SecurityViolation)
class SecurityViolationAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'violation_type', 'violation', 'timestamp', 'ip_address']
    list_filter = ['violation_type', 'timestamp', 'utilisateur__role']
    search_fields = ['utilisateur__email', 'utilisateur__first_name', 'utilisateur__last_name', 'violation']
    readonly_fields = ['timestamp', 'ip_address', 'user_agent']
    ordering = ['-timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('utilisateur')

@admin.register(TestEventLog)
class TestEventLogAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'test', 'event_type', 'question_number', 'timestamp', 'session_id']
    list_filter = ['event_type', 'timestamp', 'test', 'utilisateur__role']
    search_fields = ['utilisateur__email', 'test__titre', 'session_id']
    readonly_fields = ['timestamp', 'ip_address', 'user_agent', 'event_data']
    ordering = ['-timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('utilisateur', 'test')
    
    def has_add_permission(self, request):
        return False  # Les événements sont créés automatiquement
    
    def has_change_permission(self, request, obj=None):
        return False  # Les événements ne doivent pas être modifiés