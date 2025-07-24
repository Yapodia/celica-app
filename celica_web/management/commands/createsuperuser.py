# celica_web/management/commands/createsuperuser.py
import uuid
from django.contrib.auth.management.commands import createsuperuser
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model

class Command(createsuperuser.Command):
    help = 'Créer un superutilisateur avec email, matricule et un username unique généré automatiquement.'

    def handle(self, *args, **options):
        # Récupérer les champs demandés
        email = options.get('email')
        matricule = options.get('matricule')
        password = options.get('password')

        # Entrée interactive si les champs ne sont pas fournis
        if not email:
            email = self.get_input_data('email', "Email: ")
        if not matricule:
            matricule = self.get_input_data('matricule', "Matricule: ")
        if not password:
            password = self.get_input_data('password', "Password: ", True)
            password2 = self.get_input_data('password', "Password (again): ", True)
            if password != password2:
                raise CommandError("Les mots de passe ne correspondent pas.")

        # Générer un username unique (nécessaire car username est requis par AbstractUser)
        username = f"superuser_{uuid.uuid4().hex[:30]}"

        # Créer le superutilisateur
        User = get_user_model()
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                matricule=matricule,
                password=password,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS(f"Superutilisateur créé avec succès : {email} (Username: {username})"))
        except Exception as e:
            raise CommandError(f"Erreur lors de la création du superutilisateur : {str(e)}")

    def get_input_data(self, field, prompt, hidden=False):
        value = None
        while not value:
            if hidden:
                import getpass
                value = getpass.getpass(prompt)
            else:
                value = input(prompt).strip()
            if not value:
                self.stdout.write(self.style.ERROR(f"{field.capitalize()} est requis."))
        return value