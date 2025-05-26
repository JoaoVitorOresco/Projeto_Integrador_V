# projeto_integrador_V/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importe as views que acabou de criar.
# Se o seu views.py estiver em projeto_integrador_V/views.py:
from . import views as project_main_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Suas URLs existentes
    path('api/mmpose/', include('api_mmpose.urls')),
    path('api/auth/', include('dj_rest_auth.urls')), # Se estiver a usar dj_rest_auth
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')), # Se estiver a usar dj_rest_auth

    # === Novas URLs para o fluxo de autenticação do YouTube ===
    # Esta URL será visitada para iniciar o processo de autenticação com o Google
    path('google-auth-start/', project_main_views.google_auth_start_view, name='google_auth_start'),
    
    # Esta é a URI de REDIRECIONAMENTO que você deve configurar no Google Cloud Console.
    # O Google redirecionará para esta URL após o utilizador dar consentimento.
    path('oauth2callback/', project_main_views.oauth2callback_view, name='oauth2callback'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
