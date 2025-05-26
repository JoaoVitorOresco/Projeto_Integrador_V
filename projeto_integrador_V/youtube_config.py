# projeto_integrador_V/youtube_config.py
import os
from django.conf import settings

CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, "client_secret.json")


TOKEN_PICKLE_FILE = os.path.join(settings.BASE_DIR, "token.pickle")


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Esta deve ser EXATAMENTE a mesma URI de redirecionamento configurada no Google Cloud Console
# e na sua view de callback do Django.

REDIRECT_URI = 'x' #URL para Callback
