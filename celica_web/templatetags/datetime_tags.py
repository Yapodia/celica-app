from django import template
from django.utils import timezone
from django.conf import settings

register = template.Library()

@register.filter
def localtime_fr(value):
    """
    Convertit une datetime UTC vers l'heure locale française et la formate
    Usage: {{ user.last_login|localtime_fr }}
    """
    if value is None:
        return ""
    
    # Convertir vers l'heure locale
    local_time = timezone.localtime(value)
    
    # Formater selon les conventions françaises
    return local_time.strftime('%d/%m/%Y %H:%M')

@register.filter
def localtime_short(value):
    """
    Affiche seulement l'heure locale
    Usage: {{ planning.date_debut|localtime_short }}
    """
    if value is None:
        return ""
    
    local_time = timezone.localtime(value)
    return local_time.strftime('%H:%M')

@register.filter
def date_fr(value):
    """
    Affiche seulement la date au format français
    Usage: {{ planning.date_debut|date_fr }}
    """
    if value is None:
        return ""
    
    local_time = timezone.localtime(value)
    return local_time.strftime('%d/%m/%Y')

@register.filter
def time_since_local(value):
    """
    Affiche le temps écoulé depuis une date en heure locale
    Usage: {{ user.last_login|time_since_local }}
    """
    if value is None:
        return ""
    
    now = timezone.now()
    diff = now - value
    
    if diff.days > 0:
        return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return "à l'instant"

@register.filter
def is_today(value):
    """
    Vérifie si une date est aujourd'hui
    Usage: {% if planning.date_debut|is_today %}Aujourd'hui{% endif %}
    """
    if value is None:
        return False
    
    now = timezone.localtime(timezone.now())
    local_time = timezone.localtime(value)
    
    return local_time.date() == now.date()

@register.filter
def is_past(value):
    """
    Vérifie si une date est dans le passé
    Usage: {% if planning.date_debut|is_past %}Passé{% endif %}
    """
    if value is None:
        return False
    
    now = timezone.now()
    return value < now

@register.simple_tag
def current_time_fr():
    """
    Affiche l'heure actuelle locale
    Usage: {% current_time_fr %}
    """
    now = timezone.localtime(timezone.now())
    return now.strftime('%d/%m/%Y %H:%M')

@register.simple_tag
def timezone_name():
    """
    Affiche le nom du fuseau horaire configuré
    Usage: {% timezone_name %}
    """
    return settings.TIME_ZONE 