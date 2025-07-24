from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
import csv
from io import TextIOWrapper, BytesIO
import openpyxl
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import random
import pdfplumber
from django.core.files.base import ContentFile
import tempfile
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
import numpy as np
from django.apps import apps

# Gestionnaire d'utilisateurs personnalisé
class UtilisateurManager(BaseUserManager):
    def create_user(self, email, matricule, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        if not matricule:
            raise ValueError("Le matricule est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, matricule=matricule, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, matricule, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, matricule, password, **extra_fields)

    def rechercher(self, mot_cle):
        return self.filter(
            Q(last_name__icontains=mot_cle) |
            Q(first_name__icontains=mot_cle) |
            Q(email__icontains=mot_cle) |
            Q(matricule__icontains=mot_cle)
        )

class CoursManager(models.Manager):
    def rechercher(self, mot_cle):
        return self.filter(titre__icontains=mot_cle)

class TestManager(models.Manager):
    def rechercher(self, mot_cle):
        return self.filter(titre__icontains=mot_cle)

class QuestionManager(models.Manager):
    def rechercher(self, mot_cle):
        return self.filter(enonce__icontains=mot_cle)

# Modèle Utilisateur
class Utilisateur(AbstractUser):
    ROLES = (
        ('admin', 'Administrateur'),
        ('instructeur', 'Instructeur'),
        ('apprenant', 'Apprenant'),
    )
    STATUTS = (
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
    )

    NIVEAU_CHOICES = (
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    )
    SPECIALITE_CHOICES = (
        ('RSI', 'RSI'),
        ('CNS', 'CNS'),
        ('ELB', 'ELB'),
        ('AUTRE', 'AUTRE')
    )

    email = models.EmailField(unique=True)
    matricule = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default='apprenant')
    statut = models.CharField(max_length=10, choices=STATUTS, default='actif')
    specialite = models.CharField(max_length=20, choices=SPECIALITE_CHOICES, default='AUTRE')
    
    niveau = models.CharField(max_length=50, choices=NIVEAU_CHOICES, blank=True, null=True)

    date_naissance = models.DateField(null=True, blank=True)
    qualifications = models.TextField(max_length=500, blank=True, null=True)
    derniere_connexion = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    groupes = models.ManyToManyField('Groupe', related_name='groupes_apprenant', blank=True)
    doit_changer_mot_de_passe = models.BooleanField(default=False, help_text="L'utilisateur doit changer son mot de passe à la prochaine connexion")

    objects = UtilisateurManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['matricule']

    class Meta:
        indexes = [
            models.Index(fields=['last_name', 'first_name', 'email']),
            models.Index(fields=['role']),
        ]
        permissions = [
            ("gerer_utilisateurs", "Peut gérer les utilisateurs"),
            ("gerer_notifications", "Peut gérer les notifications"),
            ("consulter_notifications", "Peut consulter les notifications"),
            ("acceder_aide", "Peut accéder à l'aide"),
            ("gerer_tests", "Peut gérer les tests"),
            ("gerer_questions", "Peut gérer les questions"),
            ("gerer_cours", "Peut gérer les cours"),
            ("gerer_modules", "Peut gérer les modules"),
            ("gerer_plannings", "Peut gérer les plannings"),
            ("gerer_groupes", "Peut gérer les groupes"),
            ("passer_tests", "Peut passer des tests"),
            ("consulter_resultats", "Peut consulter les résultats"),
            ("consulter_cours", "Peut consulter les cours"),
        ]

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.email})"

    def clean(self):
        if self.role not in dict(self.ROLES):
            raise ValidationError(f"Le rôle doit être l'un des suivants : {', '.join(r[0] for r in self.ROLES)}")
        if self.date_naissance and self.date_naissance > timezone.now().date():
            raise ValidationError("La date de naissance ne peut pas être dans le futur.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def s_authentifier(self, email, mot_de_passe):
        if self.email != email:
            return False
        if not self.is_superuser and self.statut != 'actif':
            return False
        if self.check_password(mot_de_passe):
            try:
                self.last_login = timezone.now()
                self.save()
                return True
            except Exception as e:
                # print(f"Erreur lors de la mise à jour de last_login: {e}")
                return True
        return False

    def modifier_profil(self, nom, prenom, email):
        self.last_name = nom
        self.first_name = prenom
        self.email = email
        self.save()

    def changer_mot_de_passe(self, nouveau_mot_de_passe):
        self.set_password(nouveau_mot_de_passe)
        self.save()

    def consulter_aide(self):
        return Aide.objects.all()

    def consulter_a_propos(self):
        return APropos.objects.first()

    def rechercher_global(self, mot_cle, entite):
        if entite == "utilisateur" and self.has_perm('celica_web.gerer_utilisateurs'):
            return Utilisateur.objects.rechercher(mot_cle)
        elif entite == "test" and self.has_perm('celica_web.gerer_tests'):
            return Test.objects.rechercher(mot_cle).filter(module__groupes__instructeurs=self).select_related('module')
        elif entite == "question" and self.has_perm('celica_web.gerer_questions'):
            return Question.objects.rechercher(mot_cle).filter(test__module__groupes__instructeurs=self).select_related('test')
        elif entite == "cours" and (self.has_perm('celica_web.gerer_cours') or self.role == "apprenant"):
            if self.role == "instructeur":
                return Cours.objects.rechercher(mot_cle).filter(instructeur=self).select_related('module')
            else:
                return Cours.objects.rechercher(mot_cle).filter(module__groupes__apprenants=self).select_related('module')
        return []

class Administrateur(Utilisateur):
    class Meta:
        proxy = True

    def gerer_utilisateurs(self):
        if not self.has_perm('celica_web.gerer_utilisateurs'):
            raise PermissionError("Seul un administrateur peut gérer les utilisateurs")
        return Utilisateur.objects.all()

    def gerer_plannings(self):
        if not self.has_perm('celica_web.gerer_plannings'):
            raise PermissionError("Seul un administrateur peut gérer les plannings")
        return Planning.objects.all()

    def gerer_modules(self):
        if not self.has_perm('celica_web.gerer_modules'):
            raise PermissionError("Seul un administrateur peut gérer les modules")
        return Module.objects.all()

    def gerer_groupes(self):
        if not self.has_perm('celica_web.gerer_groupes'):
            raise PermissionError("Seul un administrateur peut gérer les groupes")
        return Groupe.objects.all()

    def consulter_statistiques_globales(self, filtres):
        if not self.has_perm('celica_web.gerer_utilisateurs'):
            raise PermissionError("Seul un administrateur peut consulter les statistiques globales")
        return Statistiques.objects.filter(**filtres)

class Instructeur(Utilisateur):
    class Meta:
        proxy = True

    def gerer_tests(self):
        if not self.has_perm('celica_web.gerer_tests'):
            raise PermissionError("Seul un instructeur peut gérer les tests")
        return Test.objects.filter(module__groupes__instructeurs=self).select_related('module')

    def gerer_questions(self):
        if not self.has_perm('celica_web.gerer_questions'):
            raise PermissionError("Seul un instructeur peut gérer les questions")
        return Question.objects.filter(test__module__groupes__instructeurs=self).select_related('test')

    def gerer_cours(self):
        if not self.has_perm('celica_web.gerer_cours'):
            raise PermissionError("Seul un instructeur peut gérer les cours")
        return Cours.objects.filter(instructeur=self).select_related('module')

    def consulter_resultats_apprenants(self):
        if not self.has_perm('celica_web.gerer_tests'):
            raise PermissionError("Seul un instructeur peut consulter les résultats des apprenants")
        return Resultat.objects.filter(test__module__groupes__instructeurs=self).select_related('test', 'apprenant')

    def filtrer_statistiques(self, criteres):
        if not self.has_perm('celica_web.gerer_tests'):
            raise PermissionError("Seul un instructeur peut filtrer les statistiques")
        return Statistiques.objects.filter(**criteres)

class Apprenant(Utilisateur):
    class Meta:
        proxy = True

    def passer_test(self, test):
        if not self.has_perm('celica_web.passer_tests'):
            raise PermissionError("Seul un apprenant peut passer un test")
        resultat = Resultat.objects.create(
            test=test, apprenant=self, score=0, appreciation="En cours"
        )
        Notification.creer_notification(
            titre=f"Nouveau résultat pour {test.titre}",
            message=f"Votre résultat pour le test {test.titre} a été publié.",
            type_notice="resultat",
            utilisateur=self,
            resultat=resultat
        )
        return resultat

    def consulter_resultats(self):
        if not self.has_perm('celica_web.consulter_resultats'):
            raise PermissionError("Seul un apprenant peut consulter ses résultats")
        return Resultat.objects.filter(apprenant=self).select_related('test')

    def consulter_cours(self):
        if not self.has_perm('celica_web.consulter_cours'):
            raise PermissionError("Seul un apprenant peut consulter ses cours")
        return Cours.objects.filter(module__groupes__apprenants=self).select_related('module')
    
# Modèle Module
class Module(models.Model):
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('maintenance', 'En maintenance'),
    ]

    intitule = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    categorie = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='actif')
    instructeur_principal = models.ForeignKey(
        Utilisateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'role__in': ['instructeur', 'admin']},
        related_name='modules_principaux'
    )
    groupes = models.ManyToManyField('Groupe', related_name='modules', blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("gerer_modules", "Peut gérer les modules"),
            ("consulter_modules", "Peut consulter les modules"),
        ]
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ['intitule']

    def __str__(self):
        return self.intitule

    def clean(self):
        if not self.intitule or len(self.intitule.strip()) < 3:
            raise ValidationError("L'intitulé doit contenir au moins 3 caractères.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

# Modèle Groupe
class Groupe(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(
        max_length=20, 
        unique=True,
        blank=True,  # MODIFICATION: Permettre vide temporairement
        help_text="Code unique du groupe"
    )
    capacite_max = models.PositiveIntegerField(default=30)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    # Relation pour les instructeurs du groupe
    instructeurs = models.ManyToManyField(
        Utilisateur,
        related_name='groupes_instructeur',
        limit_choices_to={'role': 'instructeur'},
        blank=True,
        help_text="Instructeurs assignés à ce groupe"
    )

    class Meta:
        permissions = [
            ("gerer_groupes", "Peut gérer les groupes"),
            ("consulter_groupes", "Peut consulter les groupes"),
        ]
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def clean(self):
        if not self.nom or len(self.nom.strip()) < 2:
            raise ValidationError("Le nom du groupe doit contenir au moins 2 caractères.")
        
        if self.capacite_max <= 0:
            raise ValidationError("La capacité maximale doit être positive.")

    def save(self, *args, **kwargs):
        # Générer un code unique si pas de code ou code par défaut
        if not self.code or self.code == 'GRP-000':
            self.code = self.generer_code_unique()
        
        self.clean()
        super().save(*args, **kwargs)

    def generer_code_unique(self):
        """Génère un code unique pour le groupe"""
        import random
        
        # Essayer d'abord avec le nom du groupe
        if self.nom:
            # Prendre les 3 premières lettres du nom
            base_code = ''.join([c.upper() for c in self.nom if c.isalpha()])[:3]
            if len(base_code) < 3:
                base_code = base_code.ljust(3, 'X')
        else:
            base_code = 'GRP'
        
        # Chercher un numéro disponible
        counter = 1
        while True:
            nouveau_code = f"{base_code}-{counter:03d}"
            
            # Vérifier que le code n'existe pas (exclure le groupe actuel)
            if self.pk:
                exists = Groupe.objects.filter(code=nouveau_code).exclude(pk=self.pk).exists()
            else:
                exists = Groupe.objects.filter(code=nouveau_code).exists()
            
            if not exists:
                return nouveau_code
            
            counter += 1
            
            # Sécurité : si on dépasse 999, utiliser un nombre aléatoire
            if counter > 999:
                random_num = random.randint(1000, 9999)
                nouveau_code = f"{base_code}-{random_num}"
                
                if self.pk:
                    exists = Groupe.objects.filter(code=nouveau_code).exclude(pk=self.pk).exists()
                else:
                    exists = Groupe.objects.filter(code=nouveau_code).exists()
                
                if not exists:
                    return nouveau_code

    def nombre_apprenants(self):
        """Retourne le nombre d'apprenants dans ce groupe"""
        return self.apprenants.count()

    def places_disponibles(self):
        """Retourne le nombre de places disponibles"""
        return max(0, self.capacite_max - self.nombre_apprenants())

    def est_plein(self):
        """Vérifie si le groupe est plein"""
        return self.nombre_apprenants() >= self.capacite_max

    @property
    def apprenants(self):
        """Propriété pour accéder facilement aux apprenants du groupe"""
        return self.groupes_apprenant.filter(role='apprenant')

    def get_apprenants(self):
        """Retourne tous les apprenants du groupe"""
        return self.groupes_apprenant.filter(role='apprenant')

    def get_instructeurs(self):
        """Retourne tous les instructeurs du groupe"""
        return self.groupes_apprenant.filter(role='instructeur')

    def ajouter_apprenant(self, utilisateur):
        """Ajoute un apprenant au groupe"""
        if utilisateur.role != 'apprenant':
            raise ValidationError("Seul un apprenant peut être ajouté à un groupe.")
        
        if self.est_plein():
            raise ValidationError("Le groupe est plein.")
        
        self.groupes_apprenant.add(utilisateur)

    def retirer_apprenant(self, utilisateur):
        """Retire un apprenant du groupe"""
        self.groupes_apprenant.remove(utilisateur)

    @classmethod
    def creer_groupe_avec_code_unique(cls, nom, **kwargs):
        """Crée un groupe avec un code unique généré automatiquement"""
        groupe = cls(nom=nom, **kwargs)
        groupe.save()  # Le code sera généré automatiquement
        return groupe

# Modèle Test
class Test(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='tests')
    instructeur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role__in': ['instructeur', 'admin']},
        related_name='tests_crees'
    )
    duree = models.PositiveIntegerField(help_text="Durée en minutes")
    bareme = models.FloatField(help_text="Barème total du test", default=20)
    randomize_questions = models.BooleanField(
        default=True, 
        help_text="Mélanger l'ordre des questions pour chaque apprenant"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TestManager()

    @property
    def status(self):
        return "Actif" if self.actif else "Inactif"

    class Meta:
        permissions = [
            ("gerer_tests", "Peut gérer les tests"),
            ("passer_tests", "Peut passer des tests"),
        ]
        verbose_name = "Test"
        verbose_name_plural = "Tests"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} - {self.module.intitule}"

    def clean(self):
        if not self.titre or len(self.titre.strip()) < 3:
            raise ValidationError("Le titre doit contenir au moins 3 caractères.")
        
        if self.duree <= 0:
            raise ValidationError("La durée doit être positive.")
        
        if self.bareme <= 0:
            raise ValidationError("Le barème doit être positif.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def exporter(self, format_fichier):
        """Exporte le test dans le format spécifié"""
        format_fichier = format_fichier.lower()
        
        if format_fichier == 'pdf':
            return self._exporter_pdf()
        elif format_fichier == 'csv':
            return self._exporter_csv()
        elif format_fichier == 'json':
            return self._exporter_json()
        else:
            raise ValueError(f"Format '{format_fichier}' non supporté. Formats disponibles : pdf, csv, json")
    
    def _exporter_pdf(self):
        """Exporte le test en PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # En-tête du test
        story.append(Paragraph(f"<b>{self.titre}</b>", styles['Title']))
        story.append(Spacer(1, 12))
        
        if self.description:
            story.append(Paragraph(f"<b>Description :</b> {self.description}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        story.append(Paragraph(f"<b>Module :</b> {self.module.intitule}", styles['Normal']))
        story.append(Paragraph(f"<b>Instructeur :</b> {self.instructeur.get_full_name() or self.instructeur.email}", styles['Normal']))
        story.append(Paragraph(f"<b>Durée :</b> {self.duree} minutes", styles['Normal']))
        story.append(Paragraph(f"<b>Barème :</b> {self.bareme} points", styles['Normal']))
        story.append(Paragraph(f"<b>Date de création :</b> {self.date_creation.strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 24))
        
        # Questions
        questions = self.questions.prefetch_related('reponses').order_by('ordre', 'id')
        for i, question in enumerate(questions, 1):
            story.append(Paragraph(f"<b>Question {i} ({question.ponderation} pts) :</b>", styles['Heading2']))
            story.append(Paragraph(question.enonce, styles['Normal']))
            story.append(Spacer(1, 6))
            
            if question.type_question == 'QCM':
                story.append(Paragraph("<b>Réponses :</b>", styles['Normal']))
                for j, reponse in enumerate(question.reponses.all().order_by('ordre', 'id'), 1):
                    marqueur = "✓" if reponse.est_correcte else "○"
                    story.append(Paragraph(f"  {j}. {marqueur} {reponse.texte}", styles['Normal']))
            else:
                story.append(Paragraph("<i>(Question à réponse libre)</i>", styles['Normal']))
            
            if question.explication:
                story.append(Paragraph(f"<b>Explication :</b> {question.explication}", styles['Normal']))
            
            story.append(Spacer(1, 12))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _exporter_csv(self):
        """Exporte le test en CSV"""
        buffer = BytesIO()
        writer = csv.writer(TextIOWrapper(buffer, encoding='utf-8', newline=''))
        
        # En-tête du fichier
        writer.writerow(['Test:', self.titre])
        writer.writerow(['Module:', self.module.intitule])
        writer.writerow(['Instructeur:', self.instructeur.get_full_name() or self.instructeur.email])
        writer.writerow(['Durée (min):', self.duree])
        writer.writerow(['Barème:', self.bareme])
        writer.writerow(['Date création:', self.date_creation.strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        
        # En-têtes des colonnes
        writer.writerow(['Numéro', 'Énoncé', 'Type', 'Difficulté', 'Pondération', 'Réponses', 'Réponses correctes', 'Explication'])
        
        # Questions
        questions = self.questions.prefetch_related('reponses').order_by('ordre', 'id')
        for i, question in enumerate(questions, 1):
            reponses_texte = []
            reponses_correctes = []
            
            if question.type_question == 'QCM':
                for reponse in question.reponses.all().order_by('ordre', 'id'):
                    reponses_texte.append(reponse.texte)
                    if reponse.est_correcte:
                        reponses_correctes.append(reponse.texte)
            
            writer.writerow([
                i,
                question.enonce,
                question.get_type_question_display(),
                question.get_niveau_difficulte_display(),
                question.ponderation,
                ' | '.join(reponses_texte),
                ' | '.join(reponses_correctes),
                question.explication or ''
            ])
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _exporter_json(self):
        """Exporte le test en JSON"""
        import json
        
        test_data = {
            'test': {
                'id': self.id,
                'titre': self.titre,
                'description': self.description,
                'module': {
                    'id': self.module.id,
                    'intitule': self.module.intitule,
                    'description': self.module.description
                },
                'instructeur': {
                    'id': self.instructeur.id,
                    'nom': self.instructeur.get_full_name() or self.instructeur.email,
                    'email': self.instructeur.email
                },
                'duree': self.duree,
                'bareme': float(self.bareme),
                'actif': self.actif,
                'date_creation': self.date_creation.isoformat(),
                'date_modification': self.date_modification.isoformat()
            },
            'questions': []
        }
        
        questions = self.questions.prefetch_related('reponses').order_by('ordre', 'id')
        for i, question in enumerate(questions, 1):
            question_data = {
                'numero': i,
                'id': question.id,
                'enonce': question.enonce,
                'type_question': question.type_question,
                'niveau_difficulte': question.niveau_difficulte,
                'ponderation': float(question.ponderation),
                'explication': question.explication,
                'ordre': question.ordre,
                'reponses': []
            }
            
            if question.type_question == 'QCM':
                for reponse in question.reponses.all().order_by('ordre', 'id'):
                    reponse_data = {
                        'id': reponse.id,
                        'texte': reponse.texte,
                        'est_correcte': reponse.est_correcte,
                        'explication': reponse.explication,
                        'ordre': reponse.ordre
                    }
                    question_data['reponses'].append(reponse_data)
            
            test_data['questions'].append(question_data)
        
        json_str = json.dumps(test_data, ensure_ascii=False, indent=2)
        return json_str.encode('utf-8')

# Modèle Question
class Question(models.Model):
    TYPE_CHOICES = [
        ('QCM', 'Question à choix multiples'),
        ('QRL', 'Question à réponse libre'),
    ]

    NIVEAU_CHOICES = [
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile'),
    ]

    enonce = models.TextField(help_text="Énoncé de la question")
    type_question = models.CharField(max_length=10, choices=TYPE_CHOICES, default='QCM')
    niveau_difficulte = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='moyen')
    ponderation = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1)],
        help_text="Points attribués à cette question"
    )
    image = models.ImageField(
        upload_to='questions/images/', 
        null=True, 
        blank=True,
        help_text="Image d'illustration (optionnel)"
    )
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE,
        related_name='questions',
        null=True,  # CORRECTION: Permettre NULL temporairement
        blank=True,
        help_text="Module auquel appartient cette question"
    )
    test = models.ForeignKey(
        Test, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='questions',
        help_text="Test spécifique (optionnel)"
    )
    instructeur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['instructeur', 'admin']},
        related_name='questions_creees',
        null=True,  # CORRECTION: Permettre NULL temporairement aussi
        blank=True,
        help_text="Instructeur qui a créé cette question"
    )
    #date_creation = models.DateTimeField(default=timezone.now)
    explication = models.TextField(blank=True, null=True, help_text="Explication de la question")
    #actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    #date_modification = models.DateTimeField(auto_now=True)
    #nombre_utilisations = models.IntegerField(default=0)
    ordre = models.IntegerField(default=1)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True, verbose_name="Actif")
    #active = models.BooleanField(default=True, verbose_name="Active (alias)")
    nombre_utilisations = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de fois que cette question a été utilisée"
    )
    @property
    def active(self):
        return self.actif
    objects = QuestionManager()

    class Meta:
        permissions = [
            ("gerer_questions", "Peut gérer les questions"),
            ("consulter_questions", "Peut consulter les questions"),
        ]
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['type_question', 'niveau_difficulte']),
            models.Index(fields=['module', 'test']),
            models.Index(fields=['instructeur', 'actif']),
        ]

    def __str__(self):
        module_nom = self.module.intitule if self.module else "Aucun module"
        return f"{self.enonce[:50]}... ({self.type_question}) - {module_nom}"

    def clean(self):
        """Validation personnalisée"""
        if not self.enonce or len(self.enonce.strip()) < 10:
            raise ValidationError("L'énoncé doit contenir au moins 10 caractères.")
        
        if self.ponderation <= 0:
            raise ValidationError("La pondération doit être positive.")
        
        # Validation de la cohérence test/module
        if self.test and self.module and self.test.module != self.module:
            raise ValidationError("Le test sélectionné doit appartenir au même module que la question.")
        
        # Validation de l'instructeur
        if self.instructeur and self.instructeur.role not in ['instructeur', 'admin']:
            raise ValidationError("Seul un instructeur ou un admin peut créer une question.")
        
        # VALIDATION STRICTE UNIVERSELLE DE LA PONDÉRATION
        # Cette validation s'applique à TOUS les points d'entrée (formulaires, scripts, admin, etc.)
        if self.test and self.ponderation > 0:
            # Calculer la somme actuelle des pondérations des autres questions du test
            somme_actuelle = self.test.questions.aggregate(
                total=Sum('ponderation')
            )['total'] or 0
            
            # Si c'est une modification (question existante), exclure sa propre pondération actuelle
            if self.pk:  # Question existante
                question_existante = Question.objects.get(pk=self.pk)
                somme_actuelle -= question_existante.ponderation
            
            # Calculer la somme totale après ajout/modification
            somme_totale = somme_actuelle + self.ponderation
            barème = self.test.bareme
            
            # Refuser catégoriquement si ça dépasse le barème
            if somme_totale > barème:
                excédent = somme_totale - barème
                raise ValidationError(
                    f"Impossible d'ajouter cette question. "
                    f"La somme des pondérations ({somme_totale}) dépasserait le barème du test ({barème}) de {excédent} points. "
                    f"Veuillez réduire la pondération de cette question ou augmenter le barème du test."
                )

    def save(self, *args, **kwargs):
        """Validation avant sauvegarde"""
        # Si pas de module mais un test, utiliser le module du test
        if self.test and not self.module:
            self.module = self.test.module
        
        # Assigner des valeurs par défaut si nécessaire
        if not self.instructeur:
            # Essayer de récupérer l'instructeur du test
            if self.test and self.test.instructeur:
                self.instructeur = self.test.instructeur
        
        # Validation uniquement si les champs obligatoires sont présents
        if self.module and self.instructeur:
            self.clean()
        
        super().save(*args, **kwargs)

    def nombre_reponses(self):
        """Retourne le nombre de réponses pour cette question"""
        return self.reponses.count()

    def reponses_correctes(self):
        """Retourne les réponses correctes"""
        return self.reponses.filter(est_correcte=True)

    def nombre_reponses_correctes(self):
        """Retourne le nombre de réponses correctes"""
        return self.reponses_correctes().count()

    def est_valide(self):
        """Vérifie si la question est valide (a au moins une réponse correcte)"""
        if self.type_question == 'QCM':
            return self.nombre_reponses_correctes() >= 1 and self.nombre_reponses() >= 2
        else:  # QRL
            return True  # Les questions à réponse libre sont toujours valides

    def difficulte_display(self):
        """Retourne l'affichage de la difficulté"""
        return dict(self.NIVEAU_CHOICES).get(self.niveau_difficulte, self.niveau_difficulte)

    def enonce_court(self):
        """Retourne une version courte de l'énoncé pour l'affichage"""
        if len(self.enonce) <= 100:
            return self.enonce
        return self.enonce[:100] + "..."

    def peut_etre_supprimee(self):
        """Vérifie si la question peut être supprimée"""
        # Une question ne peut pas être supprimée si elle est utilisée dans des résultats
        return not hasattr(self, 'resultats') or not self.resultats.exists()

    def dupliquer(self, nouveau_test=None, nouvel_instructeur=None, nouveau_module=None):
        """Crée une copie de la question"""
        nouvelle_question = Question(
            enonce=self.enonce,
            type_question=self.type_question,
            niveau_difficulte=self.niveau_difficulte,
            ponderation=self.ponderation,
            module=nouveau_module or self.module,
            test=nouveau_test or self.test,
            instructeur=nouvel_instructeur or self.instructeur,
            active=self.active
        )
        nouvelle_question.save()
        
        # Dupliquer les réponses
        for reponse in self.reponses.all():
            Reponse.objects.create(
                texte=reponse.texte,
                est_correcte=reponse.est_correcte,
                question=nouvelle_question,
                explication=reponse.explication,
                ordre=reponse.ordre
            )
        
        return nouvelle_question

    def incrementer_utilisation(self):
        """Incrémente le compteur d'utilisation"""
        self.nombre_utilisations += 1
        self.save(update_fields=['nombre_utilisations'])

    def desactiver(self):
        """Désactive la question"""
        self.actif = False
        self.save(update_fields=['actif'])

    def activer(self):
        """Active la question"""
        self.actif = True
        self.save(update_fields=['actif'])

    def get_reponses_melangees(self):
        """Retourne les réponses dans un ordre aléatoire"""
        reponses = list(self.reponses.all())
        random.shuffle(reponses)
        return reponses

    def get_difficulte_color(self):
        """Retourne une couleur CSS selon la difficulté"""
        colors = {
            'facile': 'green',
            'moyen': 'orange', 
            'difficile': 'red'
        }
        return colors.get(self.niveau_difficulte, 'gray')

    def get_type_icon(self):
        """Retourne une icône selon le type de question"""
        icons = {
            'QCM': '☑️',
            'QRL': '✍️'
        }
        return icons.get(self.type_question, '❓')

    @classmethod
    def questions_par_module(cls, module):
        """Retourne toutes les questions d'un module"""
        return cls.objects.filter(module=module, actif=True)

    @classmethod
    def questions_par_difficulte(cls, niveau):
        """Retourne les questions d'un niveau de difficulté"""
        return cls.objects.filter(niveau_difficulte=niveau, actif=True)

    @classmethod
    def questions_aleatoires(cls, nombre=10, module=None, niveau=None):
        """Retourne un nombre aléatoire de questions"""
        queryset = cls.objects.filter(actif=True)
        
        if module:
            queryset = queryset.filter(module=module)
        
        if niveau:
            queryset = queryset.filter(niveau_difficulte=niveau)
        
        return queryset.order_by('?')[:nombre]

# Modèle Reponse
class Reponse(models.Model):
    texte = models.TextField(help_text="Texte de la réponse")
    est_correcte = models.BooleanField(default=False, help_text="Cette réponse est-elle correcte ?")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reponses')
    explication = models.TextField(
        blank=True, 
        null=True, 
        help_text="Explication pour cette réponse (optionnel)"
    )
    ordre = models.PositiveIntegerField(default=1, help_text="Ordre d'affichage")
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"

    def __str__(self):
        status = "✓" if self.est_correcte else "✗"
        return f"{status} {self.texte[:30]}..."

    def clean(self):
        if not self.texte or len(self.texte.strip()) < 1:
            raise ValidationError("Le texte de la réponse ne peut pas être vide.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

# Modèle Resultat
class Resultat(models.Model):
    APPRECIATION_CHOICES = [
        ('excellent', 'Excellent (18-20)'),
        ('tres_bien', 'Très bien (16-17)'),
        ('bien', 'Bien (14-15)'),
        ('assez_bien', 'Assez bien (12-13)'),
        ('passable', 'Passable (10-11)'),
        ('insuffisant', 'Insuffisant (0-9)'),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='resultats')
    apprenant = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'apprenant'},
        related_name='resultats'
    )
    score = models.FloatField(help_text="Score obtenu")
    note_sur_20 = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Note ramenée sur 20",
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    appreciation = models.CharField(max_length=20, choices=APPRECIATION_CHOICES)
    temps_ecoule = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Temps écoulé en minutes"
    )
    temps_passe = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Temps passé sur le test en minutes"
    )
    date_passation = models.DateTimeField(default=timezone.now)
    commentaires = models.TextField(blank=True, null=True)
    details_reponses = models.JSONField(
        blank=True, 
        null=True, 
        help_text="Détails des réponses données par l'apprenant"
    )

    class Meta:
        unique_together = ('test', 'apprenant')
        permissions = [
            ("consulter_resultats", "Peut consulter les résultats"),
            ("modifier_resultats", "Peut modifier les résultats"),
        ]
        verbose_name = "Résultat"
        verbose_name_plural = "Résultats"
        ordering = ['-date_passation']

    def __str__(self):
        return f"{self.apprenant.last_name} - {self.test.titre} - {self.score}/{self.test.bareme}"

    def clean(self):
        if self.score < 0:
            raise ValidationError("Le score ne peut pas être négatif.")
        
        if self.test and self.score > self.test.bareme:
            raise ValidationError("Le score ne peut pas dépasser le barème du test.")

    def save(self, *args, **kwargs):
        if self.test and self.test.bareme > 0:
            self.note_sur_20 = (self.score / self.test.bareme) * 20
        
        if not self.temps_passe and self.temps_ecoule:
            self.temps_passe = self.temps_ecoule
        
        if self.note_sur_20 is not None:
            if self.note_sur_20 >= 18:
                self.appreciation = 'excellent'
            elif self.note_sur_20 >= 16:
                self.appreciation = 'tres_bien'
            elif self.note_sur_20 >= 14:
                self.appreciation = 'bien'
            elif self.note_sur_20 >= 12:
                self.appreciation = 'assez_bien'
            elif self.note_sur_20 >= 10:
                self.appreciation = 'passable'
            else:
                self.appreciation = 'insuffisant'
        
        super().save(*args, **kwargs)

    def exporter(self, format_fichier):
        """Exporte le résultat dans le format spécifié"""
        format_fichier = format_fichier.lower()
        
        if format_fichier == 'pdf':
            return self._exporter_pdf()
        elif format_fichier == 'csv':
            return self._exporter_csv()
        elif format_fichier == 'json':
            return self._exporter_json()
        else:
            raise ValueError(f"Format '{format_fichier}' non supporté. Formats disponibles : pdf, csv, json")
    
    def _exporter_pdf(self):
        """Exporte le résultat en PDF avec les détails complets"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # En-tête du document
        story.append(Paragraph("RAPPORT DÉTAILLÉ DU RÉSULTAT", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Informations générales du test
        story.append(Paragraph(f"<b>Test :</b> {self.test.titre}", styles['Heading2']))
        story.append(Paragraph(f"<b>Module :</b> {self.test.module.intitule}", styles['Normal']))
        story.append(Paragraph(f"<b>Instructeur :</b> {self.test.instructeur.get_full_name() or self.test.instructeur.email}", styles['Normal']))
        story.append(Paragraph(f"<b>Barème total :</b> {self.test.bareme} points", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Informations de l'apprenant
        story.append(Paragraph(f"<b>Apprenant :</b> {self.apprenant.get_full_name() or self.apprenant.email}", styles['Heading2']))
        story.append(Paragraph(f"<b>Email :</b> {self.apprenant.email}", styles['Normal']))
        story.append(Paragraph(f"<b>Date de passation :</b> {self.date_passation.strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        if self.temps_passe:
            story.append(Paragraph(f"<b>Temps passé :</b> {self.temps_passe} minutes", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Résultats généraux
        story.append(Paragraph("<b>RÉSULTATS GÉNÉRAUX</b>", styles['Heading2']))
        story.append(Spacer(1, 6))
        
        # Calcul du pourcentage
        pourcentage = (self.score / self.test.bareme) * 100 if self.test.bareme > 0 else 0
        
        story.append(Paragraph(f"<b>Score obtenu :</b> {self.score}/{self.test.bareme} points", styles['Normal']))
        story.append(Paragraph(f"<b>Pourcentage :</b> {pourcentage:.1f}%", styles['Normal']))
        story.append(Paragraph(f"<b>Note sur 20 :</b> {self.note_sur_20:.1f}/20", styles['Normal']))
        story.append(Paragraph(f"<b>Appréciation :</b> {self.get_appreciation_display()}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Détails des réponses
        story.append(Paragraph("<b>DÉTAILS DES RÉPONSES</b>", styles['Heading2']))
        story.append(Spacer(1, 6))
        
        # Récupérer les questions du test
        questions = self.test.questions.prefetch_related('reponses').order_by('ordre', 'id')
        
        # Utiliser les détails des réponses stockés dans le modèle
        if self.details_reponses:
            details_reponses = self.details_reponses
        else:
            # Fallback si pas de détails stockés
            details_reponses = []
            for question in questions:
                reponses_correctes = []
                if question.type_question == 'QCM':
                    reponses_correctes = [r.texte for r in question.reponses.filter(est_correcte=True)]
                elif question.type_question == 'QRL':
                    reponse_correcte = question.reponses.filter(est_correcte=True).first()
                    reponses_correctes = [reponse_correcte.texte] if reponse_correcte else []
                
                details_reponses.append({
                    'question_id': question.id,
                    'question_enonce': question.enonce,
                    'question_type': question.type_question,
                    'reponse_donnee': 'Non disponible (réponse non stockée)',
                    'reponse_donnee_affichage': 'Non disponible',
                    'reponses_correctes': reponses_correctes,
                    'score_obtenu': 0,
                    'score_max': question.ponderation
                })
        
        # Afficher chaque question avec les détails
        for i, detail in enumerate(details_reponses, 1):
            story.append(Paragraph(f"<b>Question {i} ({detail['score_max']} pts) :</b>", styles['Heading3']))
            story.append(Paragraph(detail['question_enonce'], styles['Normal']))
            story.append(Spacer(1, 6))
            
            # Réponse donnée par l'apprenant
            story.append(Paragraph(f"<b>Votre réponse :</b> {detail['reponse_donnee_affichage']}", styles['Normal']))
            
            # Réponses correctes
            if detail['reponses_correctes']:
                reponses_correctes_texte = ', '.join(detail['reponses_correctes'])
                story.append(Paragraph(f"<b>Réponse(s) correcte(s) :</b> {reponses_correctes_texte}", styles['Normal']))
            
            # Score obtenu pour cette question
            story.append(Paragraph(f"<b>Score obtenu :</b> {detail['score_obtenu']}/{detail['score_max']} points", styles['Normal']))
            
            story.append(Spacer(1, 12))
        
        # Commentaires si présents
        if self.commentaires:
            story.append(Paragraph("<b>COMMENTAIRES</b>", styles['Heading2']))
            story.append(Spacer(1, 6))
            story.append(Paragraph(self.commentaires, styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Pied de page avec informations de génération
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<i>Rapport généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')} par CelicaWeb</i>", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _exporter_csv(self):
        """Exporte le résultat en CSV"""
        buffer = BytesIO()
        writer = csv.writer(TextIOWrapper(buffer, encoding='utf-8', newline=''))
        
        # En-tête du fichier
        writer.writerow(['Rapport détaillé du résultat'])
        writer.writerow([])
        writer.writerow(['Test:', self.test.titre])
        writer.writerow(['Module:', self.test.module.intitule])
        writer.writerow(['Instructeur:', self.test.instructeur.get_full_name() or self.test.instructeur.email])
        writer.writerow(['Barème total:', self.test.bareme])
        writer.writerow([])
        writer.writerow(['Apprenant:', self.apprenant.get_full_name() or self.apprenant.email])
        writer.writerow(['Email:', self.apprenant.email])
        writer.writerow(['Date de passation:', self.date_passation.strftime('%d/%m/%Y %H:%M')])
        if self.temps_passe:
            writer.writerow(['Temps passé (min):', self.temps_passe])
        writer.writerow([])
        
        # Résultats généraux
        pourcentage = (self.score / self.test.bareme) * 100 if self.test.bareme > 0 else 0
        writer.writerow(['RÉSULTATS GÉNÉRAUX'])
        writer.writerow(['Score obtenu', f"{self.score}/{self.test.bareme}"])
        writer.writerow(['Pourcentage', f"{pourcentage:.1f}%"])
        writer.writerow(['Note sur 20', f"{self.note_sur_20:.1f}/20"])
        writer.writerow(['Appréciation', self.get_appreciation_display()])
        writer.writerow([])
        
        # Détails des réponses
        writer.writerow(['DÉTAILS DES RÉPONSES'])
        writer.writerow(['Question', 'Type', 'Pondération', 'Réponse donnée', 'Réponse(s) correcte(s)', 'Score obtenu'])
        
        # Récupérer les questions et détails
        questions = self.test.questions.prefetch_related('reponses').order_by('ordre', 'id')
        
        if self.details_reponses:
            details_reponses = self.details_reponses
        else:
            details_reponses = []
            for question in questions:
                reponses_correctes = []
                if question.type_question == 'QCM':
                    reponses_correctes = [r.texte for r in question.reponses.filter(est_correcte=True)]
                elif question.type_question == 'QRL':
                    reponse_correcte = question.reponses.filter(est_correcte=True).first()
                    reponses_correctes = [reponse_correcte.texte] if reponse_correcte else []
                
                details_reponses.append({
                    'question_id': question.id,
                    'question_enonce': question.enonce,
                    'question_type': question.type_question,
                    'reponse_donnee': 'Non disponible',
                    'reponse_donnee_affichage': 'Non disponible',
                    'reponses_correctes': reponses_correctes,
                    'score_obtenu': 0,
                    'score_max': question.ponderation
                })
        
        for i, detail in enumerate(details_reponses, 1):
            reponses_correctes_texte = ' | '.join(detail['reponses_correctes']) if detail['reponses_correctes'] else 'Aucune'
            writer.writerow([
                f"Question {i}: {detail['question_enonce'][:50]}...",
                detail['question_type'],
                detail['score_max'],
                detail['reponse_donnee_affichage'],
                reponses_correctes_texte,
                f"{detail['score_obtenu']}/{detail['score_max']}"
            ])
        
        # Commentaires
        if self.commentaires:
            writer.writerow([])
            writer.writerow(['COMMENTAIRES'])
            writer.writerow([self.commentaires])
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _exporter_json(self):
        """Exporte le résultat en JSON"""
        import json
        
        # Calcul du pourcentage
        pourcentage = (self.score / self.test.bareme) * 100 if self.test.bareme > 0 else 0
        
        resultat_data = {
            'resultat': {
                'id': self.id,
                'test': {
                    'id': self.test.id,
                    'titre': self.test.titre,
                    'description': self.test.description,
                    'module': {
                        'id': self.test.module.id,
                        'intitule': self.test.module.intitule
                    },
                    'instructeur': {
                        'id': self.test.instructeur.id,
                        'nom': self.test.instructeur.get_full_name() or self.test.instructeur.email,
                        'email': self.test.instructeur.email
                    },
                    'bareme': float(self.test.bareme),
                    'duree': self.test.duree
                },
                'apprenant': {
                    'id': self.apprenant.id,
                    'nom': self.apprenant.get_full_name() or self.apprenant.email,
                    'email': self.apprenant.email,
                    'matricule': self.apprenant.matricule
                },
                'score': float(self.score),
                'note_sur_20': float(self.note_sur_20) if self.note_sur_20 else None,
                'pourcentage': round(pourcentage, 1),
                'appreciation': self.appreciation,
                'appreciation_display': self.get_appreciation_display(),
                'temps_passe': self.temps_passe,
                'temps_ecoule': self.temps_ecoule,
                'date_passation': self.date_passation.isoformat(),
                'commentaires': self.commentaires,
                'details_reponses': self.details_reponses
            },
            'metadata': {
                'export_date': timezone.now().isoformat(),
                'version': '1.0',
                'format': 'CelicaWeb Result Export'
            }
        }
        
        json_str = json.dumps(resultat_data, ensure_ascii=False, indent=2)
        return json_str.encode('utf-8')

# Modèle Planning
class Planning(models.Model):
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
        ('reporte', 'Reporté'),
    ]

    titre = models.CharField(max_length=200, help_text="Titre du planning")
    description = models.TextField(blank=True, null=True)
    date_debut = models.DateTimeField(help_text="Date et heure de début")
    date_fin = models.DateTimeField(help_text="Date et heure de fin")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifie')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True, blank=True, related_name='plannings')
    groupe = models.ForeignKey(
        'Groupe', 
        on_delete=models.CASCADE, 
        related_name='plannings',
        null=True,  # CORRECTION: Permettre NULL temporairement
        blank=True,
        help_text="Groupe concerné par ce planning"
    )
    # groupes = models.ManyToManyField(
    #     'Groupe',
    #     related_name='plannings_groupes',
    #     blank=True,
    #     help_text="Groupes concernés par ce planning"
    # )
    instructeur_responsable = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role__in': ['instructeur', 'admin']},
        related_name='plannings_responsable',
        null=True,
        blank=True,
        help_text="Instructeur responsable du planning"
    )
    materiel_requis = models.TextField(blank=True, null=True)
    lieu = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Lieu où se déroule la session"
    )
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("gerer_plannings", "Peut gérer les plannings"),
            ("consulter_plannings", "Peut consulter les plannings"),
        ]
        verbose_name = "Planning"
        verbose_name_plural = "Plannings"
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['statut', 'groupe']),
        ]

    def __str__(self):
        groupe_nom = self.groupe.nom if self.groupe else "Aucun groupe"
        return f"{self.titre} - {groupe_nom} ({self.date_debut.strftime('%d/%m/%Y %H:%M')})"

    def clean(self):
        """Validation personnalisée"""
        if not self.titre or len(self.titre.strip()) < 3:
            raise ValidationError("Le titre doit contenir au moins 3 caractères.")
        
        if self.date_fin <= self.date_debut:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")
        
        if self.date_debut < timezone.now() and not self.pk:
            raise ValidationError("La date de début ne peut pas être dans le passé pour un nouveau planning.")
        
        # Validation de l'instructeur responsable
        if self.instructeur_responsable and self.instructeur_responsable.role not in ['instructeur', 'admin']:
            raise ValidationError("L'instructeur responsable doit avoir le rôle 'instructeur' ou 'admin'.")

    def save(self, *args, **kwargs):
        """Validation avant sauvegarde"""
        self.clean()
        super().save(*args, **kwargs)

    def duree_minutes(self):
        """Calcule la durée en minutes"""
        if self.date_fin and self.date_debut:
            delta = self.date_fin - self.date_debut
            return int(delta.total_seconds() / 60)
        return 0

    def duree_formatee(self):
        """Retourne la durée au format HH:MM"""
        minutes = self.duree_minutes()
        heures = minutes // 60
        minutes_restantes = minutes % 60
        return f"{heures:02d}:{minutes_restantes:02d}"

    def est_en_cours(self):
        """Vérifie si le planning est actuellement en cours"""
        maintenant = timezone.now()
        return self.date_debut <= maintenant <= self.date_fin

    def est_termine(self):
        """Vérifie si le planning est terminé"""
        return timezone.now() > self.date_fin

    def peut_etre_modifie(self):
        """Vérifie si le planning peut encore être modifié"""
        return self.statut in ['planifie', 'reporte'] and not self.est_en_cours()

    def marquer_en_cours(self):
        """Marque le planning comme en cours"""
        if self.est_en_cours():
            self.statut = 'en_cours'
            self.save()

    def marquer_termine(self):
        """Marque le planning comme terminé"""
        if self.est_termine():
            self.statut = 'termine'
            self.save()

    def get_participants(self):
        """Retourne la liste des participants (apprenants du groupe)"""
        if self.groupe:
            return self.groupe.groupes_apprenant.filter(role='apprenant')
        return Utilisateur.objects.none()

    def nombre_participants(self):
        """Retourne le nombre de participants"""
        return self.get_participants().count()

    def peut_commencer(self):
        """Vérifie si le planning peut commencer"""
        maintenant = timezone.now()
        return (
            self.statut == 'planifie' and
            self.date_debut <= maintenant and
            self.groupe is not None and
            self.instructeur_responsable is not None
        )

    def get_statut_display_with_icon(self):
        """Retourne le statut avec une icône"""
        icons = {
            'planifie': '📅',
            'en_cours': '▶️',
            'termine': '✅',
            'annule': '❌',
            'reporte': '⏰',
        }
        return f"{icons.get(self.statut, '📋')} {self.get_statut_display()}"

    @classmethod
    def plannings_du_jour(cls, date=None):
        """Retourne les plannings d'une date donnée (aujourd'hui par défaut)"""
        if date is None:
            date = timezone.now().date()
        
        return cls.objects.filter(
            date_debut__date=date
        ).select_related('groupe', 'instructeur_responsable', 'test')

    @classmethod
    def plannings_semaine(cls, date_debut=None):
        """Retourne les plannings de la semaine"""
        if date_debut is None:
            date_debut = timezone.now().date()
        
        date_fin = date_debut + timezone.timedelta(days=6)
        
        return cls.objects.filter(
            date_debut__date__range=[date_debut, date_fin]
        ).select_related('groupe', 'instructeur_responsable', 'test')

    def conflits_horaires(self):
        """Vérifie s'il y a des conflits horaires"""
        conflits = Planning.objects.filter(
            Q(instructeur_responsable=self.instructeur_responsable) |
            Q(groupe=self.groupe)
        ).filter(
            Q(date_debut__lt=self.date_fin, date_fin__gt=self.date_debut)
        ).exclude(pk=self.pk if self.pk else None)
        
        return conflits

# Modèle Cours
class Cours(models.Model):
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('brouillon', 'Brouillon'),
        ('archive', 'Archivé'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='cours')
    instructeur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role__in': ['instructeur', 'admin']},
        related_name='cours_crees'
    )
    contenu = models.TextField(blank=True, null=True)
    fichier = models.FileField(upload_to='cours/fichiers/', null=True, blank=True, help_text="Fichier du cours (PDF, DOC, etc.)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='brouillon', help_text="Statut du cours")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    date_cloture = models.DateTimeField(null=True, blank=True)

    objects = CoursManager()

    class Meta:
        permissions = [
            ("gerer_cours", "Peut gérer les cours"),
            ("consulter_cours", "Peut consulter les cours"),
        ]
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.titre} - {self.module}"

    def clean(self):
        if not self.titre or len(self.titre.strip()) < 3:
            raise ValidationError("Le titre doit contenir au moins 3 caractères.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def importer_depuis_pdf(cls, fichier, module, instructeur):
        """
        Importe un cours depuis un fichier PDF
        """
        import pdfplumber
        from django.core.files.base import ContentFile
        import tempfile
        import os
        
        # Extraire le texte du PDF
        contenu_texte = ""
        try:
            with pdfplumber.open(fichier) as pdf:
                for page in pdf.pages:
                    texte_page = page.extract_text()
                    if texte_page:
                        contenu_texte += texte_page + "\n"
        except Exception as e:
            # Si l'extraction échoue, continuer avec un contenu par défaut
                            # print(f"Avertissement: Impossible d'extraire le texte du PDF: {str(e)}")
            contenu_texte = f"Cours importé depuis le fichier PDF: {fichier.name}\n\nContenu non extractible automatiquement."
        
        # Générer un titre à partir du nom du fichier
        nom_fichier = fichier.name if hasattr(fichier, 'name') else "cours_importe.pdf"
        
        if nom_fichier:
            # Retirer l'extension et nettoyer le nom
            titre_base = os.path.splitext(nom_fichier)[0]
            titre_base = titre_base.replace('_', ' ').replace('-', ' ').title()
        else:
            titre_base = "Cours importé"
        
        # Si le contenu a été extrait, essayer d'utiliser la première ligne comme titre
        if contenu_texte.strip() and not contenu_texte.startswith("Cours importé depuis"):
            premiere_ligne = contenu_texte.split('\n')[0].strip()
            if len(premiere_ligne) > 5 and len(premiere_ligne) <= 50:
                titre_base = premiere_ligne
            elif len(premiere_ligne) > 50:
                titre_base = premiere_ligne[:50] + "..."
        
        # S'assurer que le titre a au moins 3 caractères
        if len(titre_base.strip()) < 3:
            titre_base = f"Cours {module.intitule}"
        
        # Vérifier l'unicité du titre
        titre_final = titre_base.strip()
        compteur = 1
        while cls.objects.filter(titre=titre_final, module=module).exists():
            titre_final = f"{titre_base} ({compteur})"
            compteur += 1
        
        # Créer une description automatique
        if contenu_texte and len(contenu_texte) > 200:
            description = contenu_texte[:200] + "..."
        elif contenu_texte:
            description = contenu_texte[:100] if len(contenu_texte) > 100 else contenu_texte
        else:
            description = f"Cours importé depuis le fichier {nom_fichier}"
        
        # Créer l'instance du cours
        cours = cls(
            titre=titre_final,
            description=description,
            module=module,
            instructeur=instructeur,
            contenu=contenu_texte,
            status='actif'
        )
        
        # Sauvegarder le fichier de manière fidèle
        try:
            # Revenir au début du fichier
            fichier.seek(0)
            
            # Sauvegarder directement le fichier sans passer par un fichier temporaire
            cours.fichier.save(
                nom_fichier,
                fichier,
                save=False
            )
            
        except Exception as e:
            # Si la sauvegarde du fichier échoue, essayer une méthode alternative
            try:
                fichier.seek(0)
                cours.fichier.save(
                    nom_fichier,
                    ContentFile(fichier.read()),
                    save=False
                )
            except Exception as e2:
                # Si tout échoue, continuer sans fichier
                print(f"Avertissement: Impossible de sauvegarder le fichier: {str(e2)}")
                pass
        
        # Sauvegarder le cours
        cours.save()
        
        return cours

    def exporter(self, format_fichier):
        """Exporte le cours dans le format spécifié"""
        format_fichier = format_fichier.lower()
        
        # Si le format demandé est 'original' et qu'un fichier existe, retourner le fichier original
        if format_fichier == 'original' and self.fichier:
            return self._exporter_original()
        elif format_fichier == 'pdf':
            return self._exporter_pdf()
        elif format_fichier == 'csv':
            return self._exporter_csv()
        elif format_fichier == 'json':
            return self._exporter_json()
        else:
            raise ValueError(f"Format '{format_fichier}' non supporté. Formats disponibles : original, pdf, csv, json")
    
    def _exporter_original(self):
        """Exporte le fichier original du cours sans modification"""
        if not self.fichier:
            raise ValueError("Aucun fichier original à exporter")
        
        # Retourner directement le fichier original
        return self.fichier
    
    def _exporter_pdf(self):
        """Exporte le cours en PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # En-tête du cours
        story.append(Paragraph(f"<b>{self.titre}</b>", styles['Title']))
        story.append(Spacer(1, 12))
        
        if self.description:
            story.append(Paragraph(f"<b>Description :</b> {self.description}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        story.append(Paragraph(f"<b>Module :</b> {self.module.intitule}", styles['Normal']))
        story.append(Paragraph(f"<b>Instructeur :</b> {self.instructeur.get_full_name() or self.instructeur.email}", styles['Normal']))
        story.append(Paragraph(f"<b>Statut :</b> {self.get_status_display()}", styles['Normal']))
        story.append(Paragraph(f"<b>Date de création :</b> {self.created_at.strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        if self.updated_at:
            story.append(Paragraph(f"<b>Dernière modification :</b> {self.updated_at.strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 24))
        
        # Contenu du cours
        if self.contenu:
            story.append(Paragraph("<b>Contenu du cours :</b>", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            # Diviser le contenu en paragraphes
            paragraphes = self.contenu.split('\n')
            for paragraphe in paragraphes:
                if paragraphe.strip():
                    story.append(Paragraph(paragraphe.strip(), styles['Normal']))
                    story.append(Spacer(1, 6))
            
            story.append(Spacer(1, 12))
        
        # Informations sur le fichier attaché
        if self.fichier:
            story.append(Paragraph(f"<b>Fichier attaché :</b> {self.fichier.name}", styles['Normal']))
            story.append(Spacer(1, 6))
        
        # Informations de clôture
        if self.date_cloture:
            story.append(Paragraph(f"<b>Date de clôture :</b> {self.date_cloture.strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _exporter_csv(self):
        """Exporte le cours en CSV"""
        from io import StringIO
        
        # Utiliser StringIO au lieu de BytesIO pour CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # En-tête du fichier
        writer.writerow(['Cours:', self.titre])
        writer.writerow(['Module:', self.module.intitule])
        writer.writerow(['Instructeur:', self.instructeur.get_full_name() or self.instructeur.email])
        writer.writerow(['Statut:', self.get_status_display()])
        writer.writerow(['Date création:', self.created_at.strftime('%d/%m/%Y %H:%M')])
        if self.updated_at:
            writer.writerow(['Dernière modification:', self.updated_at.strftime('%d/%m/%Y %H:%M')])
        if self.date_cloture:
            writer.writerow(['Date clôture:', self.date_cloture.strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        
        # Informations détaillées
        writer.writerow(['Champ', 'Valeur'])
        writer.writerow(['ID', self.id])
        writer.writerow(['Titre', self.titre])
        writer.writerow(['Description', self.description or ''])
        writer.writerow(['Module ID', self.module.id])
        writer.writerow(['Module intitulé', self.module.intitule])
        writer.writerow(['Instructeur ID', self.instructeur.id])
        writer.writerow(['Instructeur email', self.instructeur.email])
        writer.writerow(['Fichier attaché', self.fichier.name if self.fichier else ''])
        writer.writerow(['Statut', self.status])
        
        # Contenu (tronqué pour CSV)
        if self.contenu:
            contenu_resume = self.contenu[:500] + "..." if len(self.contenu) > 500 else self.contenu
            contenu_resume = contenu_resume.replace('\n', ' ').replace('\r', ' ')
            writer.writerow(['Contenu (résumé)', contenu_resume])
        
        # Retourner les données en bytes
        csv_data = output.getvalue()
        output.close()
        return csv_data.encode('utf-8')
    
    def _exporter_json(self):
        """Exporte le cours en JSON"""
        import json
        
        cours_data = {
            'cours': {
                'id': self.id,
                'titre': self.titre,
                'description': self.description,
                'contenu': self.contenu,
                'module': {
                    'id': self.module.id,
                    'intitule': self.module.intitule,
                    'description': self.module.description,
                    'categorie': self.module.categorie
                },
                'instructeur': {
                    'id': self.instructeur.id,
                    'nom': self.instructeur.get_full_name() or self.instructeur.email,
                    'email': self.instructeur.email,
                    'matricule': self.instructeur.matricule
                },
                'fichier': {
                    'nom': self.fichier.name if self.fichier else None,
                    'url': self.fichier.url if self.fichier else None
                },
                'status': self.status,
                'status_display': self.get_status_display(),
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'date_cloture': self.date_cloture.isoformat() if self.date_cloture else None
            },
            'metadata': {
                'export_date': timezone.now().isoformat(),
                'version': '1.0',
                'format': 'CelicaWeb Course Export'
            }
        }
        
        json_str = json.dumps(cours_data, ensure_ascii=False, indent=2)
        return json_str.encode('utf-8')

# Modèle Notification
class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('test', 'Nouveau test'),
        ('resultat', 'Résultat disponible'),
        ('planning', 'Modification de planning'),
        ('cours', 'Nouveau cours'),
        ('urgence', 'Urgent'),
    ]

    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]

    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_notice = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='normale')
    utilisateur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name='notifications_recues',
        null=True,  # CORRECTION: Permettre NULL temporairement
        blank=True,
        help_text="Destinataire de la notification"
    )
    instructeur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='notifications_instructeur',
        null=True,
        blank=True,
        limit_choices_to={'role__in': ['instructeur', 'admin']},
        help_text="Instructeur expéditeur"
    )
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications',
        help_text="Module concerné"
    )
    date_expiration = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date d'expiration de la notification"
    )
    date_envoi = models.DateTimeField(default=timezone.now)
    est_lue = models.BooleanField(default=False)
    test = models.ForeignKey(
        Test, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='notifications',
        help_text="Test concerné"
    )
    resultat = models.ForeignKey(
        'Resultat', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='notifications',
        help_text="Résultat concerné"
    )

    class Meta:
        permissions = [
            ("gerer_notifications", "Peut gérer les notifications"),
            ("consulter_notifications", "Peut consulter les notifications"),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-date_envoi']
        indexes = [
            models.Index(fields=['utilisateur', 'est_lue']),
            models.Index(fields=['type_notice', 'priorite']),
        ]

    def __str__(self):
        return f"{self.titre} - {self.utilisateur.last_name if self.utilisateur else 'Aucun destinataire'}"

    def clean(self):
        if not self.titre or len(self.titre.strip()) < 3:
            raise ValidationError("Le titre doit contenir au moins 3 caractères.")
        
        if not self.message or len(self.message.strip()) < 5:
            raise ValidationError("Le message doit contenir au moins 5 caractères.")
        
        if self.date_expiration and self.date_expiration <= timezone.now():
            raise ValidationError("La date d'expiration doit être dans le futur.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def marquer_comme_lue(self):
        """Marque la notification comme lue"""
        self.est_lue = True
        self.save()

    def est_expiree(self):
        """Vérifie si la notification est expirée"""
        if self.date_expiration:
            return timezone.now() > self.date_expiration
        return False

    def peut_etre_supprimee(self):
        """Vérifie si la notification peut être supprimée"""
        return self.est_lue or self.est_expiree()

    @classmethod
    def creer_notification(cls, titre, message, type_notice='info', utilisateur=None, **kwargs):
        """Méthode utilitaire pour créer une notification"""
        notification = cls(
            titre=titre,
            message=message,
            type_notice=type_notice,
            utilisateur=utilisateur,
            **kwargs
        )
        notification.save()
        return notification

    @classmethod
    def notifier_groupe(cls, titre, message, groupe, type_notice='info', **kwargs):
        """Crée des notifications pour tous les membres d'un groupe"""
        notifications = []
        for apprenant in groupe.groupes_apprenant.filter(role='apprenant'):
            notification = cls.creer_notification(
                titre=titre,
                message=message,
                type_notice=type_notice,
                utilisateur=apprenant,
                **kwargs
            )
            notifications.append(notification)
        return notifications

    @classmethod
    def supprimer_expirees(cls):
        """Supprime toutes les notifications expirées"""
        maintenant = timezone.now()
        return cls.objects.filter(date_expiration__lt=maintenant).delete()

# Modèle Statistiques
class Statistiques(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='statistiques')
    taux_reussite = models.FloatField(help_text="Taux de réussite en pourcentage")
    periode_debut = models.DateTimeField()
    periode_fin = models.DateTimeField()
    nombre_participants = models.PositiveIntegerField(default=0)
    score_moyen = models.FloatField(null=True, blank=True)
    score_median = models.FloatField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Statistique"
        verbose_name_plural = "Statistiques"
        ordering = ['-periode_fin']

    def __str__(self):
        return f"Stats {self.test.titre} ({self.periode_debut.strftime('%d/%m/%Y')} - {self.periode_fin.strftime('%d/%m/%Y')})"

# --- Génération/Mise à jour automatique des statistiques ---
def generer_ou_maj_statistiques(test):
    from django.utils import timezone
    Statistiques = apps.get_model('celica_web', 'Statistiques')
    Resultat = apps.get_model('celica_web', 'Resultat')
    resultats = Resultat.objects.filter(test=test)
    if not resultats.exists():
        return
    notes = [r.note_sur_20 for r in resultats if r.note_sur_20 is not None]
    if not notes:
        return
    taux_reussite = 100 * len([n for n in notes if n >= 10]) / len(notes)
    import numpy as np
    score_moyen = float(np.mean(notes)) if notes else 0
    score_median = float(np.median(notes)) if notes else 0
    nombre_participants = len(notes)
    periode_debut = min(r.date_passation for r in resultats)
    periode_fin = max(r.date_passation for r in resultats)
    stat, created = Statistiques.objects.get_or_create(
        test=test,
        periode_debut=periode_debut,
        periode_fin=periode_fin,
        defaults={
            'taux_reussite': taux_reussite,
            'nombre_participants': nombre_participants,
            'score_moyen': score_moyen,
            'score_median': score_median,
        }
    )
    if not created:
        stat.taux_reussite = taux_reussite
        stat.nombre_participants = nombre_participants
        stat.score_moyen = score_moyen
        stat.score_median = score_median
        stat.periode_debut = periode_debut
        stat.periode_fin = periode_fin
        stat.save()

# Signal pour mettre à jour les stats à chaque ajout/modif de résultat
def maj_stats_post_save(sender, instance, **kwargs):
    generer_ou_maj_statistiques(instance.test)

post_save.connect(maj_stats_post_save, sender=Resultat)

# Modèle Aide
class Aide(models.Model):
    CATEGORIE_CHOICES = [
        ('general', 'Aide générale'),
        ('navigation', 'Navigation'),
        ('tests', 'Gestion des tests'),
        ('cours', 'Gestion des cours'),
        ('resultats', 'Consultation des résultats'),
        ('technique', 'Support technique'),
    ]

    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='general')
    module = models.ForeignKey(
        Module, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='aides',
        help_text="Module spécifique concerné (optionnel)"
    )
    mots_cles = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Mots-clés pour la recherche, séparés par des virgules"
    )
    ordre_affichage = models.PositiveIntegerField(default=1)
    visible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['categorie', 'ordre_affichage']
        verbose_name = "Aide"
        verbose_name_plural = "Aides"

    def __str__(self):
        return f"{self.get_categorie_display()} - {self.titre}"

    def clean(self):
        if not self.titre or len(self.titre.strip()) < 5:
            raise ValidationError("Le titre doit contenir au moins 5 caractères.")
        
        if not self.contenu or len(self.contenu.strip()) < 20:
            raise ValidationError("Le contenu doit contenir au moins 20 caractères.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

# Modèle À Propos
class APropos(models.Model):
    version = models.CharField(max_length=20, help_text="Version de l'application")
    nom_application = models.CharField(max_length=100, default="CelicaWeb")
    description = models.TextField()
    organisme = models.CharField(max_length=200, default="ASECNA")
    contact_email = models.EmailField(
        default='admin@celicaweb.com',
        help_text="Email de contact principal"
    )
    contact_telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    mentions_legales = models.TextField(blank=True, null=True)
    politique_confidentialite = models.TextField(blank=True, null=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "À propos"
        verbose_name_plural = "À propos"

    def __str__(self):
        return f"{self.nom_application} v{self.version}"

    def clean(self):
        if not self.version:
            raise ValidationError("La version est obligatoire.")
        
        if not self.description or len(self.description.strip()) < 50:
            raise ValidationError("La description doit contenir au moins 50 caractères.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        instance, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'version': '1.0.0',
                'description': 'Application de gestion des tests QCM pour la CELICA Maintenance de l\'ASECNA.',
                'contact_email': 'admin@celicaweb.com'
            }
        )
        return instance

# Modèle pour les violations de sécurité
class SecurityViolation(models.Model):
    VIOLATION_TYPES = [
        ('copy_paste', 'Copier-coller'),
        ('keyboard_shortcut', 'Raccourci clavier'),
        ('right_click', 'Clic droit'),
        ('print', 'Impression'),
        ('navigation', 'Navigation externe'),
        ('dev_tools', 'Outils de développement'),
        ('tab_switch', 'Changement d\'onglet'),
        ('screenshot', 'Capture d\'écran'),
        ('fullscreen_exit', 'Sortie plein écran'),
    ]

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='violations_securite')
    violation = models.CharField(max_length=200, help_text="Description de la violation")
    violation_type = models.CharField(max_length=20, choices=VIOLATION_TYPES, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Violation de sécurité"
        verbose_name_plural = "Violations de sécurité"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.utilisateur.email} - {self.violation} ({self.timestamp})"

    @classmethod
    def log_violation(cls, utilisateur, violation, url=None, violation_type=None, ip_address=None, user_agent=None):
        """Méthode utilitaire pour logger une violation"""
        return cls.objects.create(
            utilisateur=utilisateur,
            violation=violation,
            url=url,
            violation_type=violation_type,
            ip_address=ip_address,
            user_agent=user_agent
        )

# Modèle pour la journalisation détaillée des événements de test
class TestEventLog(models.Model):
    EVENT_TYPES = [
        ('test_start', 'Début de test'),
        ('test_end', 'Fin de test'),
        ('question_view', 'Visualisation de question'),
        ('question_answer', 'Réponse à question'),
        ('question_change', 'Changement de réponse'),
        ('page_focus', 'Focus sur la page'),
        ('page_blur', 'Perte de focus'),
        ('tab_switch', 'Changement d\'onglet'),
        ('window_resize', 'Redimensionnement fenêtre'),
        ('connection_lost', 'Perte de connexion'),
        ('connection_restored', 'Restauration connexion'),
        ('timeout_warning', 'Avertissement timeout'),
        ('violation_detected', 'Violation détectée'),
        ('auto_save', 'Sauvegarde automatique'),
        ('manual_save', 'Sauvegarde manuelle'),
        ('test_pause', 'Pause du test'),
        ('test_resume', 'Reprise du test'),
        ('fullscreen_enter', 'Mode plein écran'),
        ('fullscreen_exit', 'Sortie plein écran'),
        ('copy_attempt', 'Tentative de copie'),
        ('paste_attempt', 'Tentative de collage'),
        ('right_click', 'Clic droit'),
        ('keyboard_shortcut', 'Raccourci clavier'),
        ('dev_tools', 'Outils de développement'),
        ('screenshot_attempt', 'Tentative de capture d\'écran'),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='event_logs')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='test_events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    event_data = models.JSONField(default=dict, blank=True, help_text="Données supplémentaires de l'événement")
    timestamp = models.DateTimeField(auto_now_add=True)
    question_number = models.PositiveIntegerField(null=True, blank=True, help_text="Numéro de la question concernée")
    session_id = models.CharField(max_length=100, blank=True, help_text="ID de session pour grouper les événements")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Durée en millisecondes si applicable")
    
    class Meta:
        verbose_name = "Journal d'événement de test"
        verbose_name_plural = "Journaux d'événements de test"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['test', 'utilisateur', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"{self.utilisateur.email} - {self.get_event_type_display()} - {self.timestamp.strftime('%H:%M:%S')}"

    @classmethod
    def log_event(cls, test, utilisateur, event_type, **kwargs):
        """Méthode utilitaire pour enregistrer un événement"""
        return cls.objects.create(
            test=test,
            utilisateur=utilisateur,
            event_type=event_type,
            event_data=kwargs.get('event_data', {}),
            question_number=kwargs.get('question_number'),
            session_id=kwargs.get('session_id'),
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            duration=kwargs.get('duration')
        )

    def get_event_description(self):
        """Retourne une description lisible de l'événement"""
        descriptions = {
            'test_start': f"Début du test '{self.test.titre}'",
            'test_end': f"Fin du test '{self.test.titre}'",
            'question_view': f"Visualisation de la question {self.question_number}",
            'question_answer': f"Réponse à la question {self.question_number}",
            'question_change': f"Modification de la réponse à la question {self.question_number}",
            'page_focus': "Retour sur la page de test",
            'page_blur': "Sortie de la page de test",
            'tab_switch': "Changement d'onglet détecté",
            'window_resize': "Redimensionnement de la fenêtre",
            'connection_lost': "Perte de connexion détectée",
            'connection_restored': "Connexion restaurée",
            'timeout_warning': "Avertissement de timeout",
            'violation_detected': "Violation de sécurité détectée",
            'auto_save': "Sauvegarde automatique effectuée",
            'manual_save': "Sauvegarde manuelle effectuée",
            'test_pause': "Test mis en pause",
            'test_resume': "Test repris",
            'fullscreen_enter': "Passage en mode plein écran",
            'fullscreen_exit': "Sortie du mode plein écran",
            'copy_attempt': "Tentative de copie détectée",
            'paste_attempt': "Tentative de collage détectée",
            'right_click': "Clic droit détecté",
            'keyboard_shortcut': "Raccourci clavier détecté",
            'dev_tools': "Ouverture des outils de développement",
            'screenshot_attempt': "Tentative de capture d'écran",
        }
        return descriptions.get(self.event_type, f"Événement: {self.get_event_type_display()}")

    def get_severity_color(self):
        """Retourne la couleur de sévérité pour l'affichage"""
        severity_colors = {
            'test_start': 'success',
            'test_end': 'info',
            'question_view': 'secondary',
            'question_answer': 'primary',
            'question_change': 'warning',
            'page_focus': 'success',
            'page_blur': 'warning',
            'tab_switch': 'danger',
            'window_resize': 'secondary',
            'connection_lost': 'danger',
            'connection_restored': 'success',
            'timeout_warning': 'warning',
            'violation_detected': 'danger',
            'auto_save': 'info',
            'manual_save': 'info',
            'test_pause': 'warning',
            'test_resume': 'success',
            'fullscreen_enter': 'info',
            'fullscreen_exit': 'warning',
            'copy_attempt': 'danger',
            'paste_attempt': 'danger',
            'right_click': 'danger',
            'keyboard_shortcut': 'danger',
            'dev_tools': 'danger',
            'screenshot_attempt': 'danger',
        }
        return severity_colors.get(self.event_type, 'secondary')