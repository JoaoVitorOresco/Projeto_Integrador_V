print("DEBUG VIEWS.PY: Iniciando bloco de teste de importação no topo.")
_MODELS_IMPORTED_OK = False; _SERIALIZERS_IMPORTED_OK = False; _YTDOWNLOADER_IMPORTED_OK = False
_GRAPHS_IMPORTED_OK = False; _PROCESSOR_IMPORTED_OK = False
graphs_available = False 
video_processor_available = False 
baixar_video_do_youtube_para_servidor = None # Inicializa como None

try:
    from .models import Video, FrameData
    _MODELS_IMPORTED_OK = True; print("DEBUG VIEWS.PY: Modelos (.models) importados com sucesso.")
    from .serializers import VideoSerializer, VideoUploadSerializer
    _SERIALIZERS_IMPORTED_OK = True; print("DEBUG VIEWS.PY: Serializers (.serializers) importados com sucesso.")
    
    # Tenta importar a função de download do YouTube
    try:
        from .youtube_downloader_util import baixar_video_do_youtube_para_servidor
        _YTDOWNLOADER_IMPORTED_OK = True; print("DEBUG VIEWS.PY: youtube_downloader_util importado com sucesso.")
    except ImportError as e_ytdownload_import:
        print(f"AVISO VIEWS.PY: Falha ao importar 'youtube_downloader_util': {e_ytdownload_import}. Funcionalidade de download do YouTube pode estar indisponível.")
        baixar_video_do_youtube_para_servidor = None # Garante que é None se o import falhar
        # Não re-levanta a exceção aqui para permitir que o resto das views carregue,
        # a view de download tratará a ausência desta função.

    from .graphs import (
        generate_graph_base64, 
        grafico_media_angulo_perna, 
        grafico_distancia_arma_comparativo,
        grafico_scatter_pulso_mais_alto_comparativo, 
        grafico_media_pulso_acima_comparativo,
        grafico_heatmap_pulso_frente_esquerda, 
        grafico_heatmap_pulso_frente_direita, 
        grafico_velocidade_pulso_frente_esquerda, 
        grafico_velocidade_pulso_frente_direita, 
        grafico_trajetoria_pulso_frente_esquerda,
        grafico_trajetoria_pulso_frente_direita
    )
    _GRAPHS_IMPORTED_OK = True; graphs_available = True; print("DEBUG VIEWS.PY: Módulo graphs.py (com novos gráficos) importado com sucesso.")
    
    from .video_processor import process_video_with_mmpose
    _PROCESSOR_IMPORTED_OK = True; video_processor_available = True; print("DEBUG VIEWS.PY: Módulo video_processor.py importado com sucesso.")

except ImportError as e_force_import: # Captura outros ImportErrors que não foram os de youtube_downloader_util
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"ERRO DE IMPORTAÇÃO NO TOPO DE VIEWS.PY (Não relacionado ao youtube_downloader_util):")
    print(f" MdlOK:{_MODELS_IMPORTED_OK},SrlOK:{_SERIALIZERS_IMPORTED_OK},YTDwnOK:{_YTDOWNLOADER_IMPORTED_OK},GrphOK:{_GRAPHS_IMPORTED_OK},PrcOK:{_PROCESSOR_IMPORTED_OK}")
    print(f"Tipo: {type(e_force_import)}, Msg: {e_force_import}"); import traceback; traceback.print_exc()
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    # Para o servidor parar em caso de erro de importação crítico (exceto youtube_downloader_util que tem tratamento na view)
    if not _MODELS_IMPORTED_OK or not _SERIALIZERS_IMPORTED_OK or not _GRAPHS_IMPORTED_OK or not _PROCESSOR_IMPORTED_OK:
        raise e_force_import 
except Exception as e_geral_force:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"ERRO GERAL DURANTE IMPORTAÇÕES NO TOPO DE VIEWS.PY:")
    print(f" MdlOK:{_MODELS_IMPORTED_OK},SrlOK:{_SERIALIZERS_IMPORTED_OK},YTDwnOK:{_YTDOWNLOADER_IMPORTED_OK},GrphOK:{_GRAPHS_IMPORTED_OK},PrcOK:{_PROCESSOR_IMPORTED_OK}")
    print(f"Tipo: {type(e_geral_force)}, Msg: {e_geral_force}"); import traceback; traceback.print_exc()
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    raise e_geral_force
# ----- FIM DO BLOCO DE TESTE DE IMPORT -----

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, HttpResponseNotFound, JsonResponse
import cv2 
import numpy as np 
import pandas as pd 
import traceback
from django.shortcuts import get_object_or_404 
# from django.urls import reverse # Não usado atualmente aqui
import json 
import os 
import time 
import re 

from .apps import ApiMmposeConfig

# Placeholders se os imports no topo falharem (o raise e_force_import deve prevenir isso)
if not graphs_available: # Se o import de graphs.py falhou
    def generate_graph_base64(fig): return None
    grafico_media_angulo_perna=lambda d,f=None: None; grafico_distancia_arma_comparativo=lambda d,f=None: None;
    grafico_scatter_pulso_mais_alto_comparativo=lambda d,f=None: None; grafico_media_pulso_acima_comparativo=lambda d,f=None: None;
    grafico_heatmap_pulso_frente_esquerda=lambda d,f=None: None;
    grafico_heatmap_pulso_frente_direita=lambda d,f=None: None; grafico_velocidade_pulso_frente_esquerda=lambda d,f=None: None;
    grafico_velocidade_pulso_frente_direita=lambda d,f=None: None; grafico_trajetoria_pulso_frente_esquerda=lambda d,f=None: None;
    grafico_trajetoria_pulso_frente_direita=lambda d,f=None: None;
if not video_processor_available:
    def process_video_with_mmpose(video_instance, django_request_object=None):
        if video_instance: video_instance.processing_status='failed'; video_instance.processing_log='Proc. indisponível.'; video_instance.save()
# baixar_video_do_youtube_para_servidor já é definido como None se o import falhar.


class PoseEstimationView(APIView):
    parser_classes = (MultiPartParser, FormParser) 
    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        if not image_file: return Response({"error": "Nenhum arquivo de imagem enviado."}, status=status.HTTP_400_BAD_REQUEST)
        inferencer = ApiMmposeConfig.inferencer; model_loaded = ApiMmposeConfig.model_loaded
        if not model_loaded or not inferencer: return Response({"error": "Serviço de estimação de pose indisponível."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            contents = image_file.read(); nparr = np.frombuffer(contents, np.uint8); img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_cv is None: return Response({"error": "Não foi possível decodificar a imagem."}, status=status.HTTP_400_BAD_REQUEST)
            results_generator = inferencer(img_cv, show=False); result = next(results_generator)
            keypoints = result['predictions'][0][0]['keypoints']; keypoint_scores = result['predictions'][0][0]['keypoint_scores']
            formatted_keypoints = [{'part_id':i,'x':float(c[0]),'y':float(c[1]),'score':float(s)} for i,(c,s) in enumerate(zip(keypoints,keypoint_scores))]
            return Response({"filename":image_file.name,"pose_keypoints":formatted_keypoints,"status":"success_ready"}, status=status.HTTP_200_OK)
        except Exception as e: print(f"Erro PoseEstimationView: {e}"); traceback.print_exc(); return Response({"error": "Erro interno ao processar imagem."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VideoUploadView(APIView):
    authentication_classes = [TokenAuthentication]; permission_classes = [IsAuthenticated]; parser_classes = [MultiPartParser, FormParser]
    def post(self, request, *args, **kwargs):
        if not video_processor_available: return Response({"error": "Serviço de processamento indisponível."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not VideoUploadSerializer or not Video or not VideoSerializer : return Response({"error": "Configuração incompleta para upload (M/S)."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        upload_serializer = VideoUploadSerializer(data=request.data)
        if upload_serializer.is_valid():
            video_file_obj=upload_serializer.validated_data['video']; title=upload_serializer.validated_data.get('title',video_file_obj.name); description=upload_serializer.validated_data.get('description','')
            video_instance = None
            try:
                video_instance = Video.objects.create(user=request.user,title=title,description=description,video_file=video_file_obj,processing_status='pending')
                print(f"INFO (VideoUploadView): Iniciando processamento para vídeo ID: {video_instance.id}")
                process_video_with_mmpose(video_instance, django_request_object=request) # Passa o request
                video_instance.refresh_from_db()
                
                video_data_serializer = VideoSerializer(video_instance, context={'request': request})
                response_message = f"Upload do vídeo '{video_instance.title}' bem-sucedido."
                if video_instance.processing_status == 'completed': 
                    response_message += " Processamento local concluído."
                    if video_instance.youtube_video_id and video_instance.youtube_upload_status == 'uploaded_to_youtube':
                        response_message += f" Enviado para o YouTube (ID: {video_instance.youtube_video_id})."
                    elif video_instance.youtube_upload_status and video_instance.youtube_upload_status != 'not_attempted':
                         response_message += f" Status YouTube: {video_instance.youtube_upload_status}."
                elif video_instance.processing_status == 'processing':
                    response_message += " Processamento local iniciado."
                elif video_instance.processing_status == 'failed':
                    response_message += f" Falha no processamento local: {video_instance.processing_log or 'Ver logs.'}"
                
                return Response({"message":response_message,"video":video_data_serializer.data}, status=status.HTTP_201_CREATED)
            except Exception as e: 
                error_message=f"Erro na view de upload: {str(e)}"; print(f"ERRO (VideoUploadView): {error_message}"); traceback.print_exc();
                if video_instance: video_instance.processing_status='failed'; video_instance.processing_log=f"Erro view: {str(e)}"; video_instance.save()
                return Response({"error":error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else: 
            print(f"ERRO (VideoUploadView): Dados de upload inválidos: {upload_serializer.errors}")
            return Response(upload_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VideoListView(APIView):
    authentication_classes = [TokenAuthentication]; permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        if not Video or not VideoSerializer: return Response({"error": "Configuração incompleta (M/S)."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        videos = Video.objects.filter(user=request.user).order_by('-uploaded_at')
        serializer = VideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class VideoAnalyticsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, video_id, *args, **kwargs):
        if not graphs_available:
            return Response({"error": "Funcionalidade de gráficos não está disponível."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        print(f"INFO (VideoAnalyticsView): Requisição para vídeo ID: {video_id}")
        try:
            # Garante que o usuário só acesse seus próprios vídeos, a menos que seja staff
            video_q = Video.objects.filter(pk=video_id)
            if not request.user.is_staff:
                video_q = video_q.filter(user=request.user)
            video = get_object_or_404(video_q) # get_object_or_404 em um queryset filtrado
        except Video.DoesNotExist: # get_object_or_404 levanta DoesNotExist se o queryset estiver vazio
             return Response({"detail": "Vídeo não encontrado ou não autorizado."}, status=status.HTTP_404_NOT_FOUND)

        required_db_fields = [
            'frame_number', 'player_label', 'combat_state', 
            'left_leg_angle', 'right_leg_angle', 'front_leg', 'front_wrist',
            'arm_base_distance', 'cup_above',
            'shoulder_left_x', 'shoulder_left_y', 'shoulder_right_x', 'shoulder_right_y',
            'elbow_left_x', 'elbow_left_y', 'elbow_right_x', 'elbow_right_y',
            'wrist_left_x', 'wrist_left_y', 'wrist_right_x', 'wrist_right_y',
            'hip_left_x', 'hip_left_y', 'hip_right_x', 'hip_right_y',
            'knee_left_x', 'knee_left_y', 'knee_right_x', 'knee_right_y',
            'ankle_left_x', 'ankle_left_y', 'ankle_right_x', 'ankle_right_y'
        ]
        print(f"DEBUG (VideoAnalyticsView): Campos requisitados do DB: {required_db_fields}")
        frame_data_qs = FrameData.objects.filter(video_id=video_id).values(*required_db_fields).order_by('frame_number', 'player_label')
        
        if not frame_data_qs.exists():
            print(f"AVISO (VideoAnalyticsView): Nenhum FrameData encontrado no DB para video_id: {video_id}")
            return Response({"detail": "Nenhum dado de frame encontrado para este vídeo."}, status=status.HTTP_404_NOT_FOUND)

        df = pd.DataFrame.from_records(frame_data_qs)
        print(f"INFO (VideoAnalyticsView): DataFrame criado com {len(df)} linhas para vídeo ID: {video_id}.")
        print(f"DEBUG (VideoAnalyticsView): Colunas do DataFrame: {df.columns.tolist()}")
        if not df.empty:
            print(f"DEBUG (VideoAnalyticsView): Amostra dos dados do DataFrame (primeiras 2 linhas):\n{df.head(2).to_string()}")
        else:
            print("AVISO (VideoAnalyticsView): DataFrame está vazio após criação a partir do queryset.")
            return Response({"detail": "Dados de frame vazios após consulta."}, status=status.HTTP_404_NOT_FOUND)

        graficos_base64 = {}
        funcoes_grafico_map = {
            'angulo_perna': grafico_media_angulo_perna,
            'distancia_arma': grafico_distancia_arma_comparativo,
            'scatter_pulso_mais_alto': grafico_scatter_pulso_mais_alto_comparativo, 
            'media_pulso_acima': grafico_media_pulso_acima_comparativo, 
            'heatmap_pulso_esq': grafico_heatmap_pulso_frente_esquerda,
            'heatmap_pulso_dir': grafico_heatmap_pulso_frente_direita,
            'velocidade_pulso_esq': grafico_velocidade_pulso_frente_esquerda,
            'velocidade_pulso_dir': grafico_velocidade_pulso_frente_direita,
            'trajetoria_pulso_esq': grafico_trajetoria_pulso_frente_esquerda,
            'trajetoria_pulso_dir': grafico_trajetoria_pulso_frente_direita,
        }

        filtro_combate = 'em_combate' 

        for nome_grafico, funcao_grafico in funcoes_grafico_map.items():
            print(f"INFO (VideoAnalyticsView): Gerando gráfico '{nome_grafico}' com filtro '{filtro_combate}'...")
            df_para_funcao = df.copy() 
            fig = None
            try:
                # Verifica se a função existe e é chamável antes de chamar
                if callable(funcao_grafico):
                    fig = funcao_grafico(df_para_funcao, estado_combate_filtro=filtro_combate) 
                    if fig: 
                        graficos_base64[nome_grafico] = generate_graph_base64(fig) 
                        if graficos_base64[nome_grafico]: 
                            print(f"INFO (VideoAnalyticsView): Gráfico '{nome_grafico}' gerado com sucesso.")
                        else: 
                            print(f"AVISO (VideoAnalyticsView): Gráfico '{nome_grafico}' não gerou imagem base64.")
                            graficos_base64[nome_grafico] = None 
                    else: 
                        print(f"AVISO (VideoAnalyticsView): Função de gráfico '{nome_grafico}' não retornou uma figura.")
                        graficos_base64[nome_grafico] = None 
                else:
                    print(f"ERRO (VideoAnalyticsView): Função de gráfico '{nome_grafico}' não é chamável ou não foi importada corretamente.")
                    graficos_base64[nome_grafico] = None
            except Exception as e_graph:
                print(f"ERRO (VideoAnalyticsView): Exceção ao gerar gráfico '{nome_grafico}': {e_graph}"); 
                traceback.print_exc(); 
                graficos_base64[nome_grafico] = None 
            finally:
                if fig: 
                    try: plt.close(fig) # matplotlib.pyplot importado em graphs.py
                    except Exception: pass 
        
        print(f"INFO (VideoAnalyticsView): Retornando {len(graficos_base64)} chaves de gráficos (algumas podem ser None).")
        return Response(graficos_base64, status=status.HTTP_200_OK)

class DownloadYouTubeVideoView(APIView):
    authentication_classes = [TokenAuthentication]; permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        video_db_id = request.GET.get('id')
        if not video_db_id: return JsonResponse({'error': 'Parâmetro "id" obrigatório.'}, status=400)
        try:
            video_obj = get_object_or_404(Video, pk=video_db_id) # Removido user=request.user para teste, ADICIONE DE VOLTA SE NECESSÁRIO PARA SEGURANÇA
            # if video_obj.user != request.user and not request.user.is_staff: # Adicione esta verificação de volta
            #      return JsonResponse({'error': 'Não autorizado.'}, status=403)

            if not video_obj.youtube_video_id: return JsonResponse({'error': 'Vídeo sem ID do YouTube.'}, status=404)
            youtube_video_url = f"https://www.youtube.com/watch?v={video_obj.youtube_video_id}"
            nome_sugerido = f"{video_obj.title or 'video_youtube'}_{video_obj.youtube_video_id}"
            
            if not callable(baixar_video_do_youtube_para_servidor): 
                print("ERRO (DownloadYouTubeVideoView): Função 'baixar_video_do_youtube_para_servidor' não está disponível/importada.")
                raise ImportError("Função de download não carregada.")

            caminho_no_servidor = baixar_video_do_youtube_para_servidor(youtube_video_url, nome_sugerido_base=nome_sugerido)
            if caminho_no_servidor and os.path.exists(caminho_no_servidor):
                try:
                    _, ext = os.path.splitext(caminho_no_servidor); ext = ext or '.mp4'
                    base_fn = video_obj.title or f"video_{video_obj.youtube_video_id}"
                    sanitized_base = re.sub(r'[^\w\s._-]', '', base_fn)
                    sanitized_base = re.sub(r'\s+', '_', sanitized_base).strip("._-") or f"video_{video_obj.youtube_video_id}"
                    desired_filename = f"{sanitized_base}{ext}"
                    response = FileResponse(open(caminho_no_servidor, 'rb'), as_attachment=True, filename=desired_filename)
                    return response
                except Exception as e: print(f"ERRO Servindo arquivo: {e}"); return JsonResponse({'error': 'Erro ao servir.'}, status=500)
            else: 
                print(f"ERRO (DownloadYouTubeVideoView): Falha ao baixar do YouTube ({youtube_video_url}) para o servidor ou arquivo não encontrado.")
                return JsonResponse({'error': 'Falha ao obter vídeo do YT.'}, status=500)
        except Video.DoesNotExist: return JsonResponse({'error': 'Vídeo não encontrado.'}, status=404)
        except ImportError as e_imp: print(f"ERRO (DownloadYouTubeVideoView): Dependência de download faltando: {e_imp}"); traceback.print_exc(); return JsonResponse({'error': 'Serviço de download indisponível.'}, status=500)
        except Exception as e: print(f"ERRO (DownloadYouTubeVideoView): Exceção geral: {str(e)}"); traceback.print_exc(); return JsonResponse({'error': f'Erro interno: {str(e)}'}, status=500)

