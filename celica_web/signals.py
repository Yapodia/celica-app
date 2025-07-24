from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from celica_web.models import Utilisateur

@receiver(post_save, sender=Utilisateur)
def assign_user_to_group(sender, instance, created, **kwargs):
    """
    Signal pour ajouter automatiquement un utilisateur au groupe correspondant
    en fonction de son rôle (apprenant ou instructeur).
    """
    # Si l'utilisateur est créé ou son rôle est mis à jour
    if instance.role == 'apprenant':
        group, _ = Group.objects.get_or_create(name='Apprenant')
        instance.groups.add(group)
    elif instance.role == 'instructeur':
        group, _ = Group.objects.get_or_create(name='Instructeur')
        instance.groups.add(group)