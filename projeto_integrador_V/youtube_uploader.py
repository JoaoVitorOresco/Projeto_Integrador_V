# youtube_uploader.py (ou como quer que o tenha chamado)
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import config


try:
    from projeto_integrador_V import youtube_config 
except ImportError:

    print("AVISO: Não foi possível importar 'youtube_config' do projeto Django.")
    print("A certificar-se que TOKEN_PICKLE_FILE, SCOPES, e CLIENT_SECRETS_FILE estão definidos ou acessíveis.")

    class youtube_config:
        TOKEN_PICKLE_FILE = "token.pickle"
        # CLIENT_SECRETS_FILE = "client_secret.json" # Necessário para construir o serviço se o token falhar
        # SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

def get_authenticated_service(request_django=None): 
    """
    Obtém um objeto de serviço autenticado da API do YouTube.
    Tenta carregar credenciais guardadas. Se falhar, indica que a autenticação via web é necessária.
    """
    creds = None
    token_path = youtube_config.TOKEN_PICKLE_FILE

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Guarda as credenciais atualizadas
                with open(token_path, 'wb') as token_file:
                    pickle.dump(creds, token_file)
            except Exception as e:
                print(f"Erro ao atualizar token: {e}. É necessário reautenticar via web.")
                creds = None # Força a falha para indicar reautenticação
        else:
            # Se não há credenciais ou o refresh_token é inválido,
            # a autenticação precisa ser feita através do fluxo web do Django.
            creds = None 
            print("Credenciais do YouTube não encontradas ou inválidas.")
            if request_django: # Se tivermos o objeto request do Django
                print(f"Por favor, autentique visitando: {request_django.build_absolute_uri(reverse('google_auth_start'))}")
            else:
                print("Por favor, autentique através do URL '/google-auth-start/' no seu website.")


    if not creds:
        # Retorna None para indicar que a autenticação é necessária.
        # A lógica que chama esta função deve tratar este caso.
        return None

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
        return service
    except HttpError as e:
        print(f"Ocorreu um erro HTTP ao construir o serviço: {e.resp.status} - {e._get_reason()}")
        return None
    except Exception as e:
        print(f"Uma exceção geral ocorreu ao construir o serviço: {str(e)}")
        return None

def upload_video(service, file_path, title, description, category_id = config.category_id, tags, privacy_status= config.privacy_status):
    """
    Faz o upload de um vídeo para o YouTube. (Esta função permanece como antes)
    ... (código da função upload_video como no exemplo anterior) ...
    """
    if not os.path.exists(file_path):
        print(f"Erro: Arquivo de vídeo não encontrado em {file_path}")
        return None

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    try:
        print(f"Iniciando upload do arquivo: {file_path}")
        media_body = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        
        insert_request = service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media_body
        )

        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                print(f"Upload {int(status.progress() * 100)}% concluído.")
        
        video_id = response.get("id")
        print(f"Vídeo enviado com sucesso! ID do vídeo: {video_id}")
        print(f"Link do vídeo: https://www.youtube.com/watch?v={video_id}")
        return video_id

    except HttpError as e:
        print(f"Ocorreu um erro HTTP durante o upload: {e.resp.status} - {e._get_reason()}")
        try:
            error_details = e.content.decode('utf-8')
            print(f"Detalhes do erro: {error_details}")
        except Exception as decode_error:
            print(f"Não foi possível descodificar os detalhes do erro: {decode_error}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o upload: {str(e)}")
        return None
