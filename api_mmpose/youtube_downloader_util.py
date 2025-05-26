import yt_dlp
import os
from django.conf import settings
import time # Para nomes de arquivo únicos, se necessário

def baixar_video_do_youtube_para_servidor(youtube_url, nome_sugerido_base="video_youtube"):
    """
    Baixa um vídeo do YouTube para uma pasta temporária no servidor.
    Retorna o caminho completo do arquivo baixado ou None em caso de falha.
    """
    pasta_downloads_servidor = os.path.join(settings.MEDIA_ROOT, 'temp_youtube_downloads')
    os.makedirs(pasta_downloads_servidor, exist_ok=True)

    # Tenta criar um nome de arquivo mais seguro e único
    nome_base_seguro = "".join([c if c.isalnum() else "_" for c in nome_sugerido_base])
    # Adiciona um timestamp para tornar o nome do arquivo mais único e evitar sobrescrever
    # se vários usuários baixarem vídeos com o mesmo título ao mesmo tempo.
    timestamp = int(time.time())
    nome_arquivo_template = f"{nome_base_seguro}_{timestamp}.%(ext)s"

    caminho_template_saida = os.path.join(pasta_downloads_servidor, nome_arquivo_template)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best',
        'outtmpl': caminho_template_saida,
        'merge_output_format': 'mp4',
        'noplaylist': True, # Baixa apenas o vídeo, não a playlist
        'quiet': False, # Mantenha False para debug, mude para True em produção
        'no_warnings': False, # Mantenha False para debug
        # 'verbose': True, # Para debug máximo do yt-dlp
    }

    caminho_arquivo_baixado_final = None
    try:
        print(f"INFO (YT Downloader Util): Iniciando download do YouTube para: {youtube_url}")
        print(f"INFO (YT Downloader Util): Opções yt-dlp: {ydl_opts}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True) # O download acontece aqui
            # yt-dlp usa 'outtmpl' para nomear o arquivo.
            # Precisamos reconstruir o nome do arquivo com a extensão real.
            # Se o download for bem-sucedido, o arquivo estará no caminho especificado por outtmpl.

            # Tenta obter o nome do arquivo como foi salvo.
            # Se 'outtmpl' tem %(ext)s, ydl.prepare_filename pode não dar o nome final exato
            # até que o download e o merge (se houver) estejam completos.
            # É mais seguro pegar o nome do arquivo do info_dict após o download.

            if info_dict and '_filename' in info_dict:
                # Este é o caminho absoluto onde yt-dlp salvou o arquivo
                caminho_arquivo_baixado_final = info_dict['_filename']
            elif info_dict: # Tenta construir a partir do título e extensão se _filename não estiver presente
                titulo_sanitizado_yt = "".join([c if c.isalnum() else "_" for c in info_dict.get('title', nome_sugerido_base)])
                ext_yt = info_dict.get('ext', 'mp4')
                # Recria o nome usando o timestamp para corresponder ao que foi salvo
                nome_arquivo_reconstruido = f"{titulo_sanitizado_yt}_{timestamp}.{ext_yt}" if info_dict.get('title') else nome_arquivo_template.replace('%(ext)s', ext_yt)

                caminho_arquivo_baixado_final = os.path.join(pasta_downloads_servidor, os.path.basename(nome_arquivo_reconstruido))


        if caminho_arquivo_baixado_final and os.path.exists(caminho_arquivo_baixado_final):
            print(f"INFO (YT Downloader Util): Vídeo baixado com sucesso para o servidor em: {caminho_arquivo_baixado_final}")
            return caminho_arquivo_baixado_final
        else:
            # Se _filename não estava no info_dict ou o arquivo não existe
            # Tenta listar o diretório para encontrar um arquivo correspondente (último recurso)
            # Isso é frágil e depende do nome do arquivo ser previsível.
            print(f"AVISO (YT Downloader Util): Não foi possível determinar o nome exato do arquivo baixado via info_dict._filename. Tentando encontrar na pasta...")
            arquivos_na_pasta = os.listdir(pasta_downloads_servidor)
            arquivos_candidatos = [f for f in arquivos_na_pasta if nome_base_seguro in f and str(timestamp) in f]
            if arquivos_candidatos:
                caminho_arquivo_baixado_final = os.path.join(pasta_downloads_servidor, arquivos_candidatos[0]) # Pega o primeiro candidato
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