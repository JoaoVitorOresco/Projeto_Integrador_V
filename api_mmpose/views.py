# api_mmpose/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
import cv2
import numpy as np
import pandas as pd
from django.shortcuts import get_object_or_404
from django.urls import reverse
import json
import os

# Importa a configuração do app para acessar o inferencer pré-carregado
from .apps import ApiMmposeConfig

# Importa modelos e serializers
try:
    from .models import Video, FrameData # Adicionado FrameData
    from .serializers import VideoSerializer, VideoUploadSerializer
except ImportError:
    Video = None
    FrameData = None
    VideoSerializer = None
    VideoUploadSerializer = None
    print("AVISO (views.py): Modelos ou Serializers não encontrados.")


try:
    from .graphs import (
        grafico_media_angulo_perna,
        grafico_distancia_arma_comparativo,
        grafico_scatter_pulso_mais_alto_comparativo,
        grafico_media_pulso_acima_comparativo,
        generate_graph_base64
    )
    graphs_available = True
except ImportError:
    graphs_available = False
    print("AVISO (views.py): Módulo 'graphs.py' ou funções de gráfico não encontradas.")
    # Define funções placeholder para evitar NameError se graphs.py não existir
    def generate_graph_base64(fig): return None
    def grafico_media_angulo_perna(dados): return None
    def grafico_distancia_arma_comparativo(dados): return None
    def grafico_scatter_pulso_mais_alto_comparativo(dados): return None
    def grafico_media_pulso_acima_comparativo(dados): return None



# -----------------------------------------------------

# Importa a função de processamento de vídeo
try:
    from .video_processor import process_video_with_mmpose
    video_processor_available = True
except ImportError as e_vp_import:
    video_processor_available = False
    print(f"AVISO (views.py): Módulo 'video_processor.py' não encontrado: {e_vp_import}.")
    # Função placeholder para evitar NameError se video_processor.py não existir
    # e para manter a assinatura esperada (com django_request_object)
    def process_video_with_mmpose(video_instance, django_request_object=None):
        print("ERRO (placeholder): Função process_video_with_mmpose não disponível.")
        if video_instance:
            video_instance.processing_status = 'failed'
            video_instance.processing_log = 'Erro interno: Processador de vídeo não encontrado (placeholder).'
            video_instance.save()


# ============================================================================
# API VIEW PARA ESTIMATIVA DE POSE
# ============================================================================

class PoseEstimationView(APIView):
    parser_classes = (MultiPartParser, FormParser) 

    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response(
                {"error": "Nenhum arquivo de imagem enviado no campo 'image'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Acessa o modelo pré-carregado pela AppConfig
        inferencer = ApiMmposeConfig.inferencer
        model_loaded = ApiMmposeConfig.model_loaded
        
        if not model_loaded or not inferencer:
            print("AVISO (View - PoseEstimation): Modelo MMPose não disponível.")
            return Response(
                {"error": "Serviço de estimação de pose temporariamente indisponível (modelo não carregado)."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            contents = image_file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_cv is None:
                return Response({"error": "Não foi possível decodificar a imagem."}, status=status.HTTP_400_BAD_REQUEST)

            results_generator = inferencer(img_cv, show=False) 
            result = next(results_generator)

            keypoints = result['predictions'][0][0]['keypoints']
            keypoint_scores = result['predictions'][0][0]['keypoint_scores']
            formatted_keypoints = []
            for i, (coord, score) in enumerate(zip(keypoints, keypoint_scores)):
                formatted_keypoints.append({
                    'part_id': i,
                    'x': float(coord[0]),
                    'y': float(coord[1]),
                    'score': float(score)
                })

            output_data = {"filename": image_file.name, "pose_keypoints": formatted_keypoints, "status": "success_ready"}
            print(f"Pose estimada (via apps.ready) para: {image_file.name}")
            return Response(output_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Erro durante o processamento da imagem ou inferência na PoseEstimationView: {e}")
            return Response(
                {"error": "Ocorreu um erro interno no servidor ao processar a imagem."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VideoUploadView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        if not VideoUploadSerializer or not Video or not VideoSerializer:
            return Response(
                {"error": "Configuração do servidor incompleta para upload de vídeo (serializers/modelo faltando)."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        upload_serializer = VideoUploadSerializer(data=request.data)
        
        if upload_serializer.is_valid():
            video_file_obj = upload_serializer.validated_data['video']
            title = upload_serializer.validated_data.get('title', video_file_obj.name)
            description = upload_serializer.validated_data.get('description', '')

            video_instance = None 
            try:
                video_instance = Video.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    video_file=video_file_obj,
                    processing_status='pending' # Status inicial antes do processamento
                )
                
                print(f"INFO (VideoUploadView): Iniciando processamento para o vídeo ID: {video_instance.id}, Título: {video_instance.title}")
                
                # Chama a função de processamento de vídeo, passando o objeto request
                # para que ele possa ser usado no fluxo de autenticação do YouTube se necessário.
                if video_processor_available:
                    process_video_with_mmpose(video_instance, django_request_object=request)
                else:
                    # Se o processador não estiver disponível, marca como falha imediatamente
                    video_instance.processing_status = 'failed'
                    video_instance.processing_log = 'Erro crítico: Módulo video_processor.py não carregado.'
                    video_instance.save()
                    print(f"ERRO (VideoUploadView): video_processor.py não disponível para vídeo ID: {video_instance.id}")


                print(f"INFO (VideoUploadView): Chamada a process_video_with_mmpose finalizada para o vídeo ID: {video_instance.id}. Verificando estado no DB...")
                
                # Atualiza a instância do banco de dados para obter o status mais recente
                # definido pela função de processamento (que pode ser assíncrona ou síncrona)
                video_instance.refresh_from_db()
                video_data_serializer = VideoSerializer(video_instance, context={'request': request})
                
                response_message = f"Upload do vídeo '{video_instance.title}' bem-sucedido."
                
                # Adiciona detalhes sobre o processamento e o status do YouTube
                if video_instance.processing_status == 'completed':
                    response_message += " Processamento local concluído."
                    if video_instance.youtube_upload_status == 'uploaded_to_youtube':
                        response_message += f" Enviado para o YouTube com ID: {video_instance.youtube_video_id}."
                    elif video_instance.youtube_upload_status == 'youtube_auth_required':
                        response_message += " Upload para YouTube pendente: autenticação necessária."
                    elif video_instance.youtube_upload_status == 'youtube_upload_failed':
                        response_message += " Falha ao enviar para o YouTube."
                    elif video_instance.youtube_upload_status == 'pending_youtube_upload':
                         response_message += " Tentando enviar para o YouTube..." # Se o processamento for síncrono e o upload também
                elif video_instance.processing_status == 'processing': # Se o processamento for assíncrono
                    response_message += " Processamento local iniciado em segundo plano."
                elif video_instance.processing_status == 'failed':
                    response_message += f" Falha no processamento local: {video_instance.processing_log or 'Verifique os logs do servidor.'}"
                
                print(f"INFO (VideoUploadView): Resposta para vídeo ID {video_instance.id}: {response_message}")
                return Response({
                    "message": response_message,
                    "video": video_data_serializer.data
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                error_message = f"Erro na view de upload durante a criação do objeto Video ou chamada de processamento: {str(e)}"
                print(f"ERRO (VideoUploadView): {error_message}")
                import traceback
                traceback.print_exc() # Para log mais detalhado no console do servidor
                if video_instance: # Tenta atualizar o status do vídeo se a instância foi criada
                    video_instance.processing_status = 'failed'
                    video_instance.processing_log = f"Erro na view de upload: {str(e)}"
                    video_instance.save()
                return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"ERRO (VideoUploadView): Dados de upload inválidos: {upload_serializer.errors}")
            return Response(upload_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VideoListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not Video or not VideoSerializer:
            return Response(
                {"error": "Configuração do servidor incompleta para listar vídeos (modelo/serializer faltando)."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        videos = Video.objects.filter(user=request.user).order_by('-uploaded_at')
        serializer = VideoSerializer(videos, many=True, context={'request': request}) # Adicionado context
        return Response(serializer.data, status=status.HTTP_200_OK)
    

# ============================================================================
# API VIEW PARA OBTER DADOS E GERAR GRÁFICOS
# ============================================================================
class VideoAnalyticsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, video_id, *args, **kwargs):
        if not graphs_available:
            return Response(
                {"error": "Funcionalidade de gráficos não está disponível (verifique o módulo graphs.py)."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        print(f"INFO (VideoAnalyticsView): Recebida requisição para análise do vídeo ID: {video_id}")
        # Assegura que o vídeo pertence ao utilizador ou que o utilizador é staff
        video = get_object_or_404(Video, pk=video_id)

        if video.user != request.user and not request.user.is_staff:
            print(f"AVISO (VideoAnalyticsView): Acesso negado para usuário {request.user.id} ao vídeo {video_id} do usuário {video.user.id}")
            return Response({"detail": "Não autorizado a ver as análises deste vídeo."}, status=status.HTTP_403_FORBIDDEN)

        # Verifica se há dados de frame antes de tentar construir o DataFrame
        if not FrameData.objects.filter(video_id=video_id).exists():
            print(f"INFO (VideoAnalyticsView): Nenhum dado de frame encontrado para vídeo ID: {video_id}")
            return Response({"detail": "Nenhum dado de frame encontrado para este vídeo. O processamento pode não ter sido concluído ou pode ter falhado."}, status=status.HTTP_404_NOT_FOUND)

        required_db_fields = [
            'frame_number', 'player_label',
            'left_leg_angle', 'right_leg_angle', 'front_leg', 'front_wrist',
            'arm_base_distance', 'cup_above',
            'wrist_left_y', 'wrist_right_y'
        ]
        # Obtém apenas os campos necessários
        frame_data_qs = FrameData.objects.filter(video_id=video_id).values(*required_db_fields).order_by('frame_number', 'player_label')
        
        df = pd.DataFrame.from_records(frame_data_qs)
        print(f"INFO (VideoAnalyticsView): DataFrame criado com {len(df)} linhas a partir do banco de dados para vídeo ID: {video_id}.")

        if df.empty: # Esta verificação pode ser redundante devido ao .exists() anterior, mas não custa.
            return Response({"detail": "DataFrame vazio após buscar dados do banco. Verifique se o processamento do vídeo gerou dados."}, status=status.HTTP_404_NOT_FOUND)

        graficos_base64 = {}
        funcoes_grafico_map = {
            'angulo_perna': grafico_media_angulo_perna,
            'distancia_arma': grafico_distancia_arma_comparativo,
            'scatter_pulso': grafico_scatter_pulso_mais_alto_comparativo,
            'media_pulso': grafico_media_pulso_acima_comparativo,
        }

        for nome, funcao in funcoes_grafico_map.items():
            print(f"INFO (VideoAnalyticsView): Gerando gráfico '{nome}' para vídeo ID: {video_id}")
            df_copy = df.copy() # Trabalha com uma cópia para cada gráfico
            fig = None
            try:
                fig = funcao(df_copy) # A função de gráfico deve retornar um objeto Figure do Matplotlib
                if fig: # Verifica se a figura foi realmente criada
                    graficos_base64[nome] = generate_graph_base64(fig) 
                    if graficos_base64[nome]:
                        print(f"INFO (VideoAnalyticsView): Gráfico '{nome}' gerado com sucesso para vídeo ID: {video_id}.")
                    else:
                        print(f"AVISO (VideoAnalyticsView): Gráfico '{nome}' não foi gerado (generate_graph_base64 retornou None) para vídeo ID: {video_id}.")
                else:
                    print(f"AVISO (VideoAnalyticsView): Função de gráfico '{nome}' não retornou uma figura para vídeo ID: {video_id}.")
                    graficos_base64[nome] = None
            except Exception as e_graph:
                print(f"ERRO (VideoAnalyticsView): Exceção ao gerar gráfico '{nome}' para vídeo ID: {video_id}: {e_graph}")
                import traceback
                traceback.print_exc()
                graficos_base64[nome] = None
            finally:
                if fig: 
                    # Tenta fechar a figura mesmo se houve erro, para liberar memória
                    try:
                        import matplotlib.pyplot as plt
                        plt.close(fig)
                    except Exception as e_close_fig:
                        print(f"AVISO (VideoAnalyticsView): Erro menor ao tentar fechar figura do gráfico '{nome}': {e_close_fig}")
                        pass 

        print(f"INFO (VideoAnalyticsView): Retornando {len(graficos_base64)} gráficos para vídeo ID: {video_id}")
        return Response(graficos_base64, status=status.HTTP_200_OK)
