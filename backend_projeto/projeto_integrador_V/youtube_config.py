# projeto_integrador_V/youtube_config.py
import os
from django.conf import settings

CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, "client_secret.json")


TOKEN_PICKLE_FILE = os.path.join(settings.BASE_DIR, "token.pickle")

# Escopo necessário para upload de vídeos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


REDIRECT_URI = 'x'
