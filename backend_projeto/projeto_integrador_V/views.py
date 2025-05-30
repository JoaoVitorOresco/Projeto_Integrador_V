# projeto_integrador_V/views.py
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.urls import reverse # Para construir URLs de forma dinâmica
from google_auth_oauthlib.flow import Flow
# from google.oauth2.credentials import Credentials # Não é usado diretamente aqui, mas o flow.credentials será deste tipo
import pickle
import os


from . import youtube_config



def google_auth_start_view(request):
    """
    View para iniciar o fluxo de autenticação OAuth2 do Google.
    Redireciona o utilizador para a página de consentimento do Google.
    """
    try:
        flow = Flow.from_client_secrets_file(
            youtube_config.CLIENT_SECRETS_FILE,
            scopes=youtube_config.SCOPES,
            redirect_uri=youtube_config.REDIRECT_URI
        )


        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent' 
        )
        

        request.session['oauth_state'] = state
        return redirect(authorization_url)
    except FileNotFoundError:
        return HttpResponse("Erro: O arquivo 'client_secret.json' não foi encontrado. Verifique o caminho em youtube_config.py.", status=500)
    except Exception as e:
        return HttpResponse(f"Erro ao iniciar a autenticação: {str(e)}", status=500)


def oauth2callback_view(request):
    """
    View que manipula o callback do Google após a autorização.
    Recebe o código de autorização, troca-o por tokens e guarda as credenciais.
    """

    state_from_session = request.session.pop('oauth_state', None)
    state_from_google = request.GET.get('state')

    if not state_from_session or state_from_session != state_from_google:

        return HttpResponse("Erro: Parâmetro 'state' inválido. A autenticação pode ter sido comprometida.", status=403)

    flow = Flow.from_client_secrets_file(
        youtube_config.CLIENT_SECRETS_FILE,
        scopes=youtube_config.SCOPES,
        redirect_uri=youtube_config.REDIRECT_URI
    )

    try:
        code = request.GET.get('code')
        if not code:
            return HttpResponse("Erro: Código de autorização não fornecido pelo Google.", status=400)

        flow.fetch_token(code=code)
        
        credentials = flow.credentials

        with open(youtube_config.TOKEN_PICKLE_FILE, 'wb') as token_file:
            pickle.dump(credentials, token_file)
        
        return HttpResponse("Autenticação com Google bem-sucedida! O token foi guardado. Pode agora tentar fazer uploads.")

    except FileNotFoundError:
        return HttpResponse("Erro: O arquivo 'client_secret.json' não foi encontrado durante o callback. Verifique o caminho.", status=500)
    except Exception as e:
        # Registe o erro para depuração
        print(f"Erro durante o callback da autenticação Google: {str(e)}")
        return HttpResponse(f"Ocorreu um erro durante a autenticação com Google: {str(e)}", status=500)
