import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pickle
from google.auth.transport.requests import Request
import googleapiclient.http
from django.conf import settings # Para usar BASE_DIR
import traceback # Para logging de exceção detalhado

# Define os escopos
scopes = ["https://www.googleapis.com/auth/youtube.upload"]

# Caminhos para os arquivos de credenciais e token
# Estes arquivos devem estar na pasta raiz do seu projeto Django (onde manage.py está)
CLIENT_SECRET_FILE_NAME = "client_secret.json" 
TOKEN_PICKLE_FILE_NAME = "token.pickle"

# Constrói o caminho absoluto usando settings.BASE_DIR
# settings.BASE_DIR geralmente aponta para a pasta que contém manage.py
CLIENT_SECRET_FILE_PATH = os.path.join(settings.BASE_DIR, CLIENT_SECRET_FILE_NAME)
TOKEN_PICKLE_FILE_PATH = os.path.join(settings.BASE_DIR, TOKEN_PICKLE_FILE_NAME)

def upload_video_ytb(video_path, title, description):
    """
    Faz o upload de um vídeo para o YouTube.
    Lida com a autenticação e o upload.
    Retorna o ID do vídeo em caso de sucesso, ou None em caso de falha.
    """
    credentials = None
    
    if not os.path.exists(CLIENT_SECRET_FILE_PATH):
        print(f"ERRO CRÍTICO (YT Uploader): Arquivo de segredo do cliente '{CLIENT_SECRET_FILE_NAME}' NÃO ENCONTRADO em {CLIENT_SECRET_FILE_PATH}")
        print(f"Por favor, coloque o arquivo client_secret.json (renomeado se necessário para '{CLIENT_SECRET_FILE_NAME}') na pasta raiz do projeto: {settings.BASE_DIR}")
        return None

    if os.path.exists(TOKEN_PICKLE_FILE_PATH):
        with open(TOKEN_PICKLE_FILE_PATH, "rb") as token_file:
            try:
                credentials = pickle.load(token_file)
                print(f"INFO (YT Uploader): Token carregado de {TOKEN_PICKLE_FILE_PATH}")
            except Exception as e:
                print(f"AVISO (YT Uploader): Erro ao carregar token.pickle: {e}. Tentando obter novo token.")
                credentials = None

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                print("INFO (YT Uploader): Token expirado. Tentando atualizar...")
                credentials.refresh(Request())
                print("INFO (YT Uploader): Token atualizado com sucesso via refresh_token.")
            except Exception as e_refresh:
                print(f"ERRO (YT Uploader): Falha ao atualizar token: {e_refresh}. Será necessário reautenticar.")
                credentials = None 
        
        if not credentials: 
            print("INFO (YT Uploader): Credenciais não encontradas ou inválidas. Iniciando fluxo InstalledAppFlow.")
            print(f"AVISO (YT Uploader): Se isto for um processo de servidor, o fluxo InstalledAppFlow pode bloquear ou exigir interação manual.")
            try:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    CLIENT_SECRET_FILE_PATH, scopes)
                print(f"INFO (YT Uploader): Executando flow.run_local_server() para obter credenciais...")
                credentials = flow.run_local_server(port=0) 
                print(f"INFO (YT Uploader): Credenciais obtidas via run_local_server.")
            except FileNotFoundError:
                print(f"ERRO CRÍTICO (YT Uploader): Arquivo '{CLIENT_SECRET_FILE_NAME}' não encontrado durante InstalledAppFlow.")
                return None
            except Exception as e_flow:
                print(f"ERRO (YT Uploader): Falha no fluxo InstalledAppFlow: {e_flow}")
                print(f"ERRO (YT Uploader): Verifique se você pode interagir com o console/navegador se esta for a primeira autenticação ou se o token expirou sem refresh.")
                return None


        if credentials: 
            try:
                with open(TOKEN_PICKLE_FILE_PATH, "wb") as token_file:
                    pickle.dump(credentials, token_file)
                print(f"INFO (YT Uploader): Credenciais salvas/atualizadas em {TOKEN_PICKLE_FILE_PATH}")
            except Exception as e_save_token:
                print(f"ERRO (YT Uploader): Falha ao salvar token.pickle: {e_save_token}")

    if not credentials:
        print("ERRO (YT Uploader): Não foi possível obter credenciais válidas após todas as tentativas.")
        return None

    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
        print(f"INFO (YT Uploader): Serviço YouTube construído. Fazendo upload de: {video_path}")

        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "17" 
            },
            "status": {
                "privacyStatus": "unlisted", 
                "selfDeclaredMadeForKids": False
            }
        }

        request_yt = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=googleapiclient.http.MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )
        
        response = None
        print("INFO (YT Uploader): Iniciando envio de chunks do vídeo...")
        while response is None:
            status_prog, response = request_yt.next_chunk()
            if status_prog:
                print(f"INFO (YT Uploader): Upload {int(status_prog.progress() * 100)}% concluído.")
        
        video_id = response.get("id")
        if video_id:
            youtube_watch_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"SUCESSO (YT Uploader): Vídeo enviado! ID: {video_id}")
            print(f"Link: {youtube_watch_url}")
            return video_id 
        else:
            print(f"ERRO (YT Uploader): Upload concluído, mas sem ID de vídeo na resposta. Resposta: {response}")
            return None

    except googleapiclient.errors.HttpError as e_http:
        print(f"ERRO HTTP (YT Uploader): {e_http.resp.status} - {e_http._get_reason()}")
        try:
            error_details = e_http.content.decode('utf-8')
            print(f"Detalhes do erro HTTP: {error_details}")
        except Exception: pass
        return None
    except FileNotFoundError as e_fnf:
        print(f"ERRO (YT Uploader): Arquivo de vídeo não encontrado em '{video_path}'. Detalhes: {e_fnf}")
        return None
    except Exception as e:
        print(f"ERRO INESPERADO (YT Uploader): {e}")
        traceback.print_exc()
        return None