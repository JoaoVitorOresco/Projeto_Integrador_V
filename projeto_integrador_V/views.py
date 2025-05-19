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

        # 'access_type='offline'' é crucial para obter um refresh_token,
        # permitindo que a sua aplicação obtenha novos access_tokens sem interação do utilizador no futuro.
        # 'prompt='consent'' força o ecrã de consentimento a aparecer. Útil para testes
        # ou se quiser que o utilizador reconfirme o consentimento. Remova para um fluxo mais suave após a primeira vez.
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent' 
        )
        
        # Armazena o 'state' na sessão para verificar no callback.
        # Isto é uma medida de segurança para prevenir ataques CSRF.
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
    # Verifica o 'state' para proteção CSRF (opcional, mas recomendado)
    state_from_session = request.session.pop('oauth_state', None)
    state_from_google = request.GET.get('state')

    if not state_from_session or state_from_session != state_from_google:
        # Pode querer registar este erro ou mostrar uma página de erro mais amigável
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

        # Troca o código de autorização por credenciais (access_token, refresh_token, etc.)
        flow.fetch_token(code=code)
        
        credentials = flow.credentials

        # Guarda as credenciais de forma segura.
        # Para este exemplo, estamos a usar um arquivo pickle.
        # Em produção, considere soluções mais robustas como Django sessions,
        # um modelo de base de dados encriptado, ou um sistema de gestão de segredos.
        with open(youtube_config.TOKEN_PICKLE_FILE, 'wb') as token_file:
            pickle.dump(credentials, token_file)
        
        # Pode redirecionar para uma página de sucesso ou mostrar uma mensagem.
        # Por exemplo, redirecionar para a página principal ou para a página de onde o upload foi iniciado.
        # return redirect(reverse('alguma_view_de_sucesso')) 
        return HttpResponse("Autenticação com Google bem-sucedida! O token foi guardado. Pode agora tentar fazer uploads.")

    except FileNotFoundError:
        return HttpResponse("Erro: O arquivo 'client_secret.json' não foi encontrado durante o callback. Verifique o caminho.", status=500)
    except Exception as e:
        # Registe o erro para depuração
        print(f"Erro durante o callback da autenticação Google: {str(e)}")
        return HttpResponse(f"Ocorreu um erro durante a autenticação com Google: {str(e)}", status=500)
