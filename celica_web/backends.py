# celica_web/authentication.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # print(f"Authentification avec email={username}, password={password}")
        if not username or not password:
            # print("Email ou mot de passe manquant.")
            return None

        try:
            # Rechercher l'utilisateur par email (username contient l'email)
            user = User.objects.filter(email=username).first()
            if user is None:
                # print("Utilisateur non trouvé.")
                return None

            # print(f"Utilisateur trouvé: {user.email}")
            # Vérifier le mot de passe pour tous les utilisateurs (superutilisateur ou non)
            if user.check_password(password):
                # print("Authentification réussie.")
                return user
            else:
                # print("Échec de l'authentification : mot de passe incorrect.")
                return None
        except Exception as e:
            # print(f"Erreur inattendue lors de l'authentification : {str(e)}")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            # print(f"Utilisateur avec ID {user_id} non trouvé.")
            return None