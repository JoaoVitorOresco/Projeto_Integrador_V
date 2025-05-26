import yt_dlp
import os
from django.conf import settings
import time 

def baixar_video_do_youtube_para_servidor(youtube_url, nome_sugerido_base="video_youtube"):
    """
    Baixa um vídeo do YouTube para uma pasta temporária no servidor.
    Retorna o caminho completo do arquivo baixado ou None em caso de falha.
    """
    pasta_downloads_servidor = os.path.join(settings.MEDIA_ROOT, 'temp_youtube_downloads')
    os.makedirs(pasta_downloads_servidor, exist_ok=True)


    nome_base_seguro = "".join([c if c.isalnum() else "_" for c in nome_sugerido_base])

    timestamp = int(time.time())
    nome_arquivo_template = f"{nome_base_seguro}_{timestamp}.%(ext)s"

    caminho_template_saida = os.path.join(pasta_downloads_servidor, nome_arquivo_template)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best',
        'outtmpl': caminho_template_saida,
        'merge_output_format': 'mp4',
        'noplaylist': True, 
        'quiet': False,
        'no_warnings': False, 

    }

    caminho_arquivo_baixado_final = None
    try:
        print(f"INFO (YT Downloader Util): Iniciando download do YouTube para: {youtube_url}")
        print(f"INFO (YT Downloader Util): Opções yt-dlp: {ydl_opts}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True) 

            if info_dict and '_filename' in info_dict:
                caminho_arquivo_baixado_final = info_dict['_filename']
            elif info_dict: 
                titulo_sanitizado_yt = "".join([c if c.isalnum() else "_" for c in info_dict.get('title', nome_sugerido_base)])
                ext_yt = info_dict.get('ext', 'mp4')
                nome_arquivo_reconstruido = f"{titulo_sanitizado_yt}_{timestamp}.{ext_yt}" if info_dict.get('title') else nome_arquivo_template.replace('%(ext)s', ext_yt)

                caminho_arquivo_baixado_final = os.path.join(pasta_downloads_servidor, os.path.basename(nome_arquivo_reconstruido))


        if caminho_arquivo_baixado_final and os.path.exists(caminho_arquivo_baixado_final):
            print(f"INFO (YT Downloader Util): Vídeo baixado com sucesso para o servidor em: {caminho_arquivo_baixado_final}")
            return caminho_arquivo_baixado_final
        else:
            print(f"AVISO (YT Downloader Util): Não foi possível determinar o nome exato do arquivo baixado via info_dict._filename. Tentando encontrar na pasta...")
            arquivos_na_pasta = os.listdir(pasta_downloads_servidor)
            arquivos_candidatos = [f for f in arquivos_na_pasta if nome_base_seguro in f and str(timestamp) in f]
            if arquivos_candidatos:
                caminho_arquivo_baixado_final = os.path.join(pasta_downloads_servidor, arquivos_candidatos[0]) 
                print(f"INFO (YT Downloader Util): Encontrado arquivo candidato: {caminho_arquivo_baixado_final}")
                return caminho_arquivo_baixado_final
            else:
                print(f"ERRO (YT Downloader Util): Download concluído (info_dict obtido), mas o arquivo final não foi encontrado em {pasta_downloads_servidor} com base no template.")
                return None

    except yt_dlp.utils.DownloadError as e_dlp:
        print(f"ERRO (YT Downloader Util): yt-dlp DownloadError ao baixar {youtube_url}: {e_dlp}")
        return None
    except Exception as e:
        print(f"ERRO (YT Downloader Util): Exceção ao baixar vídeo do YouTube ({youtube_url}) para o servidor: {e}")
        import traceback
        traceback.print_exc()
        return None