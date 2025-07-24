from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory, ModelForm, ModelMultipleChoiceField, FileField, ChoiceField, FileInput
from django.core.validators import FileExtensionValidator
from .models import Test, Question, Reponse, Module, Groupe, Planning, Cours, Aide, Utilisateur, Resultat, Notification
import uuid
from datetime import date
import zipfile
from io import TextIOWrapper
import csv
import openpyxl
from django.core.validators import FileExtensionValidator
import pdfplumber




from django import forms
from django.forms import inlineformset_factory
from .models import Test, Question, Reponse, Module
from django.core.validators import FileExtensionValidator

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['titre', 'description', 'module', 'duree', 'bareme']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du test',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du test (optionnel)'
            }),
            'module': forms.Select(attrs={
                'class': 'form-control',
                'required': 'required'
            }),
            'duree': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Durée en minutes',
                'required': 'required'
            }),
            'bareme': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Barème total',
                'required': 'required'
            }),
        }

    def __init__(self, *args, **kwargs):
        # **CORRECTION : Extraire l'utilisateur si fourni**
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Pré-remplir le champ bareme à 20 si aucune valeur n'est fournie
        if not self.initial.get('bareme') and not self.data.get('bareme'):
            self.initial['bareme'] = 20
        # Configurer les querysets
        self.fields['module'].queryset = Module.objects.all()
        self.fields['module'].empty_label = "Sélectionnez un module"

    def save(self, commit=True):
        test = super().save(commit=False)
        
        # **CORRECTION : Assigner l'instructeur si disponible**
        if self.user and not test.instructeur:
            test.instructeur = self.user
            # Stocker temporairement pour éviter l'erreur de validation
            test._instructeur_temp = self.user
        
        if commit:
            test.save()
        
        return test

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['enonce', 'type_question', 'niveau_difficulte', 'ponderation', 'image', 'explication', 'module']
        widgets = {
            'enonce': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Énoncé de la question',
                'required': 'required'
            }),
            'type_question': forms.Select(attrs={
                'class': 'form-control',
                'required': 'required'
            }),
            'niveau_difficulte': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ponderation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.5,
                'step': 0.5,
                'placeholder': 'Pondération (points)',
                'required': 'required'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'explication': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Explication (optionnel)'
            }),
            'module': forms.Select(attrs={
                'class': 'form-control',
                'required': 'required'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir les choix pour les champs
        self.fields['type_question'].choices = [
            ('', 'Sélectionnez le type'),
            ('QCM', 'QCM (Questionnaire à Choix Multiple)'),
            ('QRL', 'QRL (Question à Réponse Libre)')
        ]
        self.fields['niveau_difficulte'].choices = [
            ('', 'Sélectionnez le niveau'),
            ('facile', 'Facile'),
            ('moyen', 'Moyen'),
            ('difficile', 'Difficile')
        ]
        
        # Correction pour la pondération : définir une valeur par défaut uniquement pour les nouvelles questions
        if not self.instance.pk:  # Nouvelle question
            if 'ponderation' not in self.data and not self.initial.get('ponderation'):
                self.fields['ponderation'].initial = 1.0
        else:  # Question existante
            # S'assurer que la valeur de la base de données est utilisée
            if self.instance.ponderation:
                self.fields['ponderation'].initial = self.instance.ponderation

class ReponseForm(forms.ModelForm):
    class Meta:
        model = Reponse
        fields = ['texte', 'est_correcte', 'explication']
        widgets = {
            'texte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Texte de la réponse',
                'required': 'required'
            }),
            'est_correcte': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'explication': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Explication de la réponse (optionnel)'
            })
        }



# **NOUVEAU : Formset pour les nouvelles réponses lors de la création**
# Utilisation d'inlineformset_factory pour avoir la méthode save()
ReponseFormSet = inlineformset_factory(
    Question,
    Reponse,
    fields=['texte', 'est_correcte', 'explication'],
    extra=2,  # Affiche 2 champs de réponse par défaut
    min_num=2,
    max_num=10,
    can_delete=True,
    validate_min=True,
    widgets={
        'texte': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Saisissez la réponse...'
        }),
        'est_correcte': forms.CheckboxInput(attrs={
            'class': 'form-check-input me-2'
        }),
        'explication': forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 2,
            'placeholder': 'Explication optionnelle...'
        })
    }
)

class ImportQuestionsForm(forms.Form):
    """Formulaire pour l'importation de questions depuis un fichier"""
    fichier = forms.FileField(
        label="Fichier à importer",
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls'])],
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text="Formats supportés : CSV, Excel (.xlsx, .xls)"
    )
    
    module = forms.ModelChoiceField(
        queryset=Module.objects.all(),
        label="Module de destination",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    remplacer_existantes = forms.BooleanField(
        label="Remplacer les questions existantes",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Cochez pour remplacer les questions déjà présentes"
    )

class SelectQuestionsForm(forms.Form):
    """Formulaire pour la sélection de questions existantes"""
    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label="Questions à sélectionner"
    )
    
    module_filtre = forms.ModelChoiceField(
        queryset=Module.objects.all(),
        required=False,
        empty_label="Tous les modules",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'module_filter'
        }),
        label="Filtrer par module"
    )

    def __init__(self, *args, **kwargs):
        # Exclure les questions déjà dans le test
        test = kwargs.pop('test', None)
        super().__init__(*args, **kwargs)
        
        if test:
            # Exclure les questions déjà associées au test
            self.fields['questions'].queryset = Question.objects.exclude(
                test=test
            ).select_related('module')

class TestPreviewForm(forms.Form):
    """Formulaire pour l'aperçu du test (lecture seule)"""
    def __init__(self, test, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test = test
        
        # Ajouter les questions comme champs de lecture seule
        for i, question in enumerate(test.question_set.all()):
            field_name = f'question_{question.id}'
            
            if question.type_question == 'QCM':
                # Pour les QCM, utiliser des checkboxes
                choices = [(r.id, r.texte) for r in question.reponse_set.all()]
                self.fields[field_name] = forms.MultipleChoiceField(
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple(attrs={
                        'disabled': True,
                        'class': 'form-check-input'
                    }),
                    label=question.enonce,
                    required=False
                )
            else:
                # Pour les QRL, utiliser des radios
                choices = [(r.id, r.texte) for r in question.reponse_set.all()]
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect(attrs={
                        'disabled': True,
                        'class': 'form-check-input'
                    }),
                    label=question.enonce,
                    required=False
                )

# **NOUVEAU : Formulaire pour l'édition rapide de questions**
class QuickEditQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['enonce', 'type_question', 'ponderation', 'explication']
        widgets = {
            'enonce': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'type_question': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ponderation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.5,
                'step': 0.5
            }),
            'explication': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            })
        }

# **NOUVEAU : Formset pour l'édition rapide des réponses**
QuickEditReponseFormSet = inlineformset_factory(
    Question,
    Reponse,
    fields=['texte', 'est_correcte', 'explication'],
    extra=0,
    can_delete=True,
    widgets={
        'texte': forms.TextInput(attrs={'class': 'form-control'}),
        'est_correcte': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        'explication': forms.Textarea(attrs={'class': 'form-control', 'rows': 1})
    }
)

# **NOUVEAU : Validation personnalisée pour s'assurer qu'un QCM a au moins une réponse correcte**
def validate_qcm_responses(question_form, reponse_formset):
    """Valide qu'une question QCM a au moins une réponse correcte"""
    if not question_form.is_valid():
        return False
    
    type_question = question_form.cleaned_data.get('type_question')
    
    if type_question == 'QCM':
        correct_responses = 0
        for form in reponse_formset:
            if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('est_correcte', False):
                    correct_responses += 1
        
        if correct_responses == 0:
            question_form.add_error(None, "Une question QCM doit avoir au moins une réponse correcte.")
            return False
    
    return True

# **NOUVEAU : Fonction utilitaire pour préparer les données d'aperçu**
def prepare_test_preview_data(test):
    """Prépare les données pour l'aperçu du test"""
    questions_data = []
    
    for question in test.question_set.all().prefetch_related('reponse_set'):
        reponses = []
        for reponse in question.reponse_set.all():
            reponses.append({
                'id': reponse.id,
                'texte': reponse.texte,
                'est_correcte': reponse.est_correcte,
                'explication': reponse.explication
            })
        
        questions_data.append({
            'id': question.id,
            'enonce': question.enonce,
            'type_question': question.type_question,
            'image': question.image.url if question.image else None,
            'explication': question.explication,
            'ponderation': question.ponderation,
            'reponses': reponses
        })
    
    return {
        'test': {
            'id': test.id,
            'titre': test.titre,
            'description': test.description,
            'module': test.module.intitule if test.module else '',
            'duree': test.duree,
            'bareme': test.bareme
        },
        'questions': questions_data,
        'total_questions': len(questions_data),
        'total_points': sum(q['ponderation'] for q in questions_data)
    }

class ImportCoursForm(forms.Form):
    fichier = forms.FileField(
        label="Fichier PDF",
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Fichier PDF contenant le contenu du cours."
    )
    module = forms.ModelChoiceField(
        queryset=Module.objects.all(),
        label="Module",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        help_text="Sélectionnez le module auquel ce cours sera associé."
    )

    def clean_fichier(self):
        fichier = self.cleaned_data['fichier']
        try:
            with pdfplumber.open(fichier) as pdf:
                text_found = False
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        text_found = True
                        break
                if not text_found:
                    raise forms.ValidationError("Le fichier PDF est vide ou ne contient pas de texte extractible.")
        except Exception as e:
            raise forms.ValidationError(f"Erreur lors de la lecture du fichier PDF : {str(e)}")
        return fichier

    def clean_module(self):
        module = self.cleaned_data['module']
        if not module:
            raise forms.ValidationError("Vous devez sélectionner un module.")
        return module

class ModuleForm(ModelForm):
    CATEGORIE_CHOICES = [
        ('RSI', 'RSI'),
        ('ELB', 'ELB'),
        ('CNS', 'CNS'),
    ]
    categorie = forms.ChoiceField(
        choices=CATEGORIE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Catégorie',
        required=True
    )
    class Meta:
        model = Module
        fields = ['intitule', 'description', 'categorie', 'status', 'instructeur_principal']
        widgets = {
            'intitule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Entrez l'intitulé du module"}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Décrivez le module'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'instructeur_principal': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_intitule(self):
        intitule = self.cleaned_data['intitule']
        if Module.objects.filter(intitule=intitule).exclude(id=self.instance.id if self.instance else None).exists():
            raise forms.ValidationError("Un module avec cet intitulé existe déjà.")
        return intitule

class GroupeForm(forms.ModelForm):
    apprenants = forms.ModelMultipleChoiceField(
        queryset=Utilisateur.objects.filter(role='apprenant'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        required=False,
        label="Apprenants"
    )

    class Meta:
        model = Groupe
        fields = ['nom', 'description', 'capacite_max']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le nom du groupe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Décrivez le groupe'}),
            'capacite_max': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Préremplir les apprenants si on modifie un groupe existant
        if self.instance.pk:
            self.fields['apprenants'].initial = self.instance.apprenants.all()

    def save(self, commit=True):
        groupe = super().save(commit=commit)
        
        if commit:
            # Gérer les apprenants sélectionnés
            apprenants_selectionnes = self.cleaned_data.get('apprenants', [])
            
            # Retirer tous les apprenants actuels du groupe
            apprenants_actuels = groupe.apprenants.all()
            for apprenant in apprenants_actuels:
                groupe.groupes_apprenant.remove(apprenant)
            
            # Ajouter les nouveaux apprenants sélectionnés
            for apprenant in apprenants_selectionnes:
                groupe.groupes_apprenant.add(apprenant)
        
        return groupe

    def clean_nom(self):
        nom = self.cleaned_data['nom']
        if Groupe.objects.filter(nom=nom).exclude(id=self.instance.id if self.instance.id else None).exists():
            raise forms.ValidationError("Un groupe avec ce nom existe déjà.")
        return nom

    def clean(self):
        cleaned_data = super().clean()
        capacite_max = cleaned_data.get('capacite_max')
        apprenants = cleaned_data.get('apprenants', [])
        
        if capacite_max and len(apprenants) > capacite_max:
            raise forms.ValidationError(
                f"Vous avez sélectionné {len(apprenants)} apprenants mais la capacité maximale est de {capacite_max}."
            )
        
        return cleaned_data

class PlanningForm(ModelForm):
    class Meta:
        model = Planning
        fields = ['titre', 'date_debut', 'date_fin', 'test', 'groupe', 'statut']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le titre du planning'}),
            'date_debut': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local',
                'title': 'Heure locale française sera utilisée'
            }),
            'date_fin': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local',
                'title': 'Heure locale française sera utilisée'
            }),
            'test': forms.Select(attrs={'class': 'form-control'}),
            'groupe': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des valeurs par défaut pour planifier rapidement
        from django.utils import timezone
        from datetime import timedelta
        
        # Si c'est un nouveau planning, proposer une heure par défaut
        if not self.instance.pk:
            now = timezone.localtime(timezone.now())
            # Proposer une heure dans les 30 minutes suivantes, arrondie à la demi-heure
            minutes_to_add = 30 - (now.minute % 30) if now.minute % 30 != 0 else 30
            start_time = now + timedelta(minutes=minutes_to_add)
            start_time = start_time.replace(second=0, microsecond=0)
            
            # Définir une durée par défaut de 2 heures
            end_time = start_time + timedelta(hours=2)
            
            # Formatter pour datetime-local (sans timezone info)
            self.fields['date_debut'].widget.attrs['value'] = start_time.strftime('%Y-%m-%dT%H:%M')
            self.fields['date_fin'].widget.attrs['value'] = end_time.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin:
            # Vérifier que la date de fin est postérieure à la date de début
            if date_fin <= date_debut:
                raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
            
            # Vérifier que le planning n'est pas dans le passé (sauf si c'est une modification d'un planning existant)
            from django.utils import timezone
            now = timezone.now()
            if not self.instance.pk and date_debut < now:
                raise forms.ValidationError("Impossible de créer un planning dans le passé.")
            
            # Vérifier la durée minimale (15 minutes)
            duree = date_fin - date_debut
            if duree.total_seconds() < 900:  # 15 minutes
                raise forms.ValidationError("La durée du planning doit être d'au moins 15 minutes.")
                
        return cleaned_data

class CoursForm(ModelForm):
    class Meta:
        model = Cours
        fields = ['titre', 'description', 'status', 'fichier', 'contenu', 'date_cloture', 'module', 'instructeur']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le titre du cours'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Décrivez le cours'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Entrez le contenu du cours'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'date_cloture': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fichier': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'module': forms.Select(attrs={'class': 'form-control'}),
            'instructeur': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'fichier': 'Seuls les fichiers PDF sont acceptés.'
        }

class AideForm(ModelForm):
    class Meta:
        model = Aide
        fields = ['titre', 'contenu', 'categorie', 'module']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Entrez le titre de l'aide"}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': "Entrez le contenu de l'aide"}),
            'categorie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez la catégorie'}),
            'module': forms.Select(attrs={'class': 'form-control'}),
        }

class UtilisateurForm(ModelForm):
    # Définir l'ordre des champs comme demandé : Nom, Prénom, Matricule, Email, Mot de passe, puis les autres
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le mot de passe'}),
        required=True,
        min_length=8,
        help_text="Le mot de passe doit contenir au moins 8 caractères"
    )
    
    confirm_password = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmez le mot de passe'}),
        required=True,
        min_length=8,
        help_text="Saisissez à nouveau le mot de passe pour confirmation"
    )

    class Meta:
        model = Utilisateur
        # Ordre demandé : Nom, Prénom, Matricule, Email, Mot de passe, puis autres champs
        fields = ['last_name', 'first_name', 'matricule', 'email', 'role', 'statut', 'specialite', 'niveau', 'date_naissance']
        labels = {
            'last_name': 'Nom',
            'first_name': 'Prénom', 
            'matricule': 'Matricule',
            'email': 'Email',
            'role': 'Rôle',
            'statut': 'Statut',
            'specialite': 'Spécialité',
            'niveau': 'Niveau',

            'date_naissance': 'Date de naissance',
        }
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le nom de famille', 'required': True}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le prénom', 'required': True}),
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez le matricule', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Entrez l\'email', 'required': True, 'value': ''}),
            'role': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'specialite': forms.Select(attrs={'class': 'form-control'}),
            'niveau': forms.Select(attrs={'class': 'form-control'}),

            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs obligatoires
        self.fields['last_name'].required = True
        self.fields['first_name'].required = True
        self.fields['matricule'].required = True
        self.fields['email'].required = True
        self.fields['role'].required = True
        
        # Ordre des champs pour l'affichage
        self.field_order = ['last_name', 'first_name', 'matricule', 'email', 'password', 'confirm_password', 'role', 'statut', 'specialite', 'niveau', 'date_naissance']

    def save(self, commit=True):
        import uuid
        user = super().save(commit=False)
        
        # Générer un username unique basé sur l'email
        if not user.username:
            user.username = f"user_{uuid.uuid4().hex[:8]}_{user.email.split('@')[0]}"
        
        # Définir le mot de passe
        user.set_password(self.cleaned_data['password'])
        
        # Définir le matricule s'il n'est pas fourni
        if not user.matricule:
            user.matricule = f"MAT_{uuid.uuid4().hex[:8].upper()}"
        
        if commit:
            user.save()
        return user

    def clean_matricule(self):
        matricule = self.cleaned_data.get('matricule')
        if matricule:
            # Vérifier l'unicité du matricule
            existing_user = Utilisateur.objects.filter(matricule=matricule)
            if self.instance and self.instance.pk:
                existing_user = existing_user.exclude(pk=self.instance.pk)
            if existing_user.exists():
                raise forms.ValidationError("Ce matricule est déjà utilisé.")
        return matricule

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Vérifier l'unicité de l'email
            existing_user = Utilisateur.objects.filter(email=email)
            if self.instance and self.instance.pk:
                existing_user = existing_user.exclude(pk=self.instance.pk)
            if existing_user.exists():
                raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        # Vérifier que les mots de passe correspondent
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data

class AjouterUtilisateurGroupeForm(forms.Form):
    utilisateur = forms.ModelChoiceField(
        queryset=Utilisateur.objects.all(),
        label='Utilisateur',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, role=None, groupe=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.groupe = groupe
        if role:
            self.fields['utilisateur'].queryset = Utilisateur.objects.filter(role=role)

    def clean_utilisateur(self):
        utilisateur = self.cleaned_data['utilisateur']
        if self.groupe and utilisateur.role == 'apprenant':
            if self.groupe.apprenants.count() >= self.groupe.capacite_max:
                raise forms.ValidationError("La capacité maximale du groupe est atteinte.")
        return utilisateur

class ChangerMotDePasseForm(forms.Form):
    nouveau_mot_de_passe = forms.CharField(
        label='Nouveau mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8
    )
    confirmer_mot_de_passe = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8
    )

    def clean(self):
        cleaned_data = super().clean()
        nouveau = cleaned_data.get('nouveau_mot_de_passe')
        confirmer = cleaned_data.get('confirmer_mot_de_passe')
        if nouveau and confirmer and nouveau != confirmer:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['titre', 'message', 'type_notice', 'priorite', 'utilisateur', 'instructeur', 'module', 'date_expiration', 'test', 'resultat']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'type_notice': forms.Select(attrs={'class': 'form-control'}),
            'priorite': forms.Select(attrs={'class': 'form-control'}),
            'utilisateur': forms.Select(attrs={'class': 'form-control'}),
            'instructeur': forms.Select(attrs={'class': 'form-control'}),
            'module': forms.Select(attrs={'class': 'form-control'}),
            'date_expiration': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'test': forms.Select(attrs={'class': 'form-control'}),
            'resultat': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['utilisateur'].required = False
        self.fields['module'].required = False
        self.fields['date_expiration'].required = False

class ResultatForm(forms.ModelForm):
    class Meta:
        model = Resultat
        fields = ['test', 'apprenant', 'score', 'appreciation', 'temps_ecoule', 'temps_passe', 'commentaires']
        widgets = {
            'test': forms.Select(attrs={'class': 'form-control'}),
            'apprenant': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'appreciation': forms.Select(attrs={'class': 'form-control'}),
            'temps_ecoule': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'temps_passe': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'commentaires': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['apprenant'].queryset = Utilisateur.objects.filter(role='apprenant')
        self.fields['temps_passe'].required = False

    def clean_score(self):
        score = self.cleaned_data['score']
        if score < 0 or score > 100:
            raise forms.ValidationError("Le score doit être compris entre 0 et 100.")
        return score

    def clean_temps_passe(self):
        temps_passe = self.cleaned_data.get('temps_passe')
        if temps_passe and temps_passe < 0:
            raise forms.ValidationError("Le temps passé ne peut pas être négatif.")
        return temps_passe

from django import forms
from django.contrib.auth import authenticate
from .models import Utilisateur

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Entrez votre email',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': "L'email est requis.",
            'invalid': "Veuillez entrer une adresse email valide."
        }
    )
    mot_de_passe = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Entrez votre mot de passe',
            'autocomplete': 'current-password'
        }),
        error_messages={
            'required': "Le mot de passe est requis."
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        mot_de_passe = cleaned_data.get('mot_de_passe')

        if email and mot_de_passe:
            # Validation de la longueur du mot de passe
            if len(mot_de_passe) < 6:
                self.add_error('mot_de_passe', "Le mot de passe doit contenir au moins 6 caractères.")
                return cleaned_data
            
            # Vérification de l'existence de l'utilisateur et du mot de passe
            try:
                user = Utilisateur.objects.get(email=email)
                if not user.check_password(mot_de_passe):
                    raise forms.ValidationError("Email ou mot de passe incorrect.")
                
                # Vérifier le statut de l'utilisateur
                if user.statut != 'actif':
                    raise forms.ValidationError("Votre compte est inactif. Veuillez contacter l'administrateur.")
                    
            except Utilisateur.DoesNotExist:
                raise forms.ValidationError("Email ou mot de passe incorrect.")
        
        return cleaned_data
from django import forms
from django.forms import inlineformset_factory
from django.core.validators import FileExtensionValidator
from .models import Question, Test, Reponse

# FormSet pour gérer les réponses
ResponseFormSet = inlineformset_factory(
    Question,
    Reponse,
    fields=['texte', 'est_correcte'],
    extra=1,
    can_delete=True,
    widgets={
        'texte': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texte de la réponse'}),
        'est_correcte': forms.Select(choices=[(True, 'Correcte'), (False, 'Incorrecte')], attrs={'class': 'form-control'})
    }
)

# Formulaire pour la saisie manuelle
# AJOUTEZ ces formulaires manquants à la fin de votre forms.py

class ManualQuestionForm(forms.ModelForm):
    """Formulaire pour la saisie manuelle de questions"""
    class Meta:
        model = Question
        fields = ['enonce', 'type_question', 'ponderation', 'image']
        widgets = {
            'enonce': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Énoncé de la question',
                'required': 'required'
            }),
            'type_question': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'ponderation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.5,
                'step': 0.5,
                'placeholder': 'Pondération (points)',
                'required': 'required'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type_question'].choices = [
            ('', 'Sélectionnez le type'),
            ('QCM', 'QCM (Questionnaire à Choix Multiple)'),
            ('QRL', 'QRL (Question à Réponse Libre)')
        ]
        
        # Correction pour la pondération : définir une valeur par défaut uniquement pour les nouvelles questions
        if not self.instance.pk:  # Nouvelle question
            if 'ponderation' not in self.data and not self.initial.get('ponderation'):
                self.fields['ponderation'].initial = 1.0
        else:  # Question existante
            # S'assurer que la valeur de la base de données est utilisée
            if self.instance.ponderation:
                self.fields['ponderation'].initial = self.instance.ponderation

# Aussi, corriger la classe ImportForm si elle n'existe pas
class ImportForm(forms.Form):
    """Formulaire pour l'importation de questions"""
    fichier = forms.FileField(
        label="Fichier à importer",
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls'])],
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    format_import = forms.ChoiceField(
        choices=[
            ('csv', 'CSV'),
            ('excel', 'Excel')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Format du fichier"
    )

# Formset pour les nouvelles réponses

# Formulaire pour la sélection de questions existantes
class SelectQuestionForm(forms.Form):
    questions = forms.ModelMultipleChoiceField(
        queryset=Question.objects.all(),  # Inclure toutes les questions, le filtrage se fera par module
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Questions existantes",
        help_text="Sélectionnez les questions existantes à ajouter au test."
    )

    def clean_questions(self):
        questions = self.cleaned_data.get('questions', [])
        if not questions:
            raise forms.ValidationError("Veuillez sélectionner au moins une question existante.")
        if len(questions) > 50:
            raise forms.ValidationError("Vous ne pouvez pas ajouter plus de 50 questions à la fois.")
        return questions

class CustomPasswordResetForm(forms.Form):
    """Formulaire personnalisé pour la réinitialisation de mot de passe"""
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre adresse email',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': "L'adresse email est requise.",
            'invalid': "Veuillez entrer une adresse email valide."
        }
    )
    
    nouveau_mot_de_passe = forms.CharField(
        label='Nouveau mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre nouveau mot de passe',
            'minlength': '8'
        }),
        required=False,
        min_length=8,
        help_text="Le mot de passe doit contenir au moins 8 caractères"
    )
    
    confirmer_mot_de_passe = forms.CharField(
        label='Confirmez le nouveau mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez votre nouveau mot de passe'
        }),
        required=False,
        min_length=8
    )
    
    def clean(self):
        cleaned_data = super().clean()
        nouveau_mot_de_passe = cleaned_data.get('nouveau_mot_de_passe')
        confirmer_mot_de_passe = cleaned_data.get('confirmer_mot_de_passe')
        
        # Vérifier que les mots de passe correspondent seulement si les deux sont fournis
        if nouveau_mot_de_passe and confirmer_mot_de_passe:
            if nouveau_mot_de_passe != confirmer_mot_de_passe:
                raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data

