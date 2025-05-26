# projeto_integrador_V/youtube_config.py
import os
from django.conf import settings

CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, "client_secret.json")


TOKEN_PICKLE_FILE = os.path.join(settings.BASE_DIR, "token.pickle")

# Escopo necessário para upload de vídeos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Esta deve ser EXATAMENTE a mesma URI de redirecionamento configurada no Google Cloud Console
# e na sua view de callback do Django.
# A porta (8001) deve ser a porta onde o seu servidor Django está a ser executado.
REDIRECT_URI = 'http://localhost:8001/oauth2callback/'
