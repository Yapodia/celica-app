from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.urls import path, include
from celica_web import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),  # URL pour l'interface d'administration
    path('accounts/', include('django.contrib.auth.urls')),  # URLs pour l'authentification (login/logout)
    path('login/admindashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('', include('celica_web.urls', namespace='celica_web')),  # Inclusion des URLs de l'application celica_web
    #path('admin/', views.admin_dashboard, name='admin_dashboard'),
]

# Ajouter les URLs pour servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)