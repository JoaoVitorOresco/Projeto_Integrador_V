# api_mmpose/video_processor.py (Upload YouTube Reintegrado com upload_video_ytb)
import cv2
import os
import time
import numpy as np
from django.conf import settings
from .apps import ApiMmposeConfig

# --- Importa as suas classes e funções ---
from .class_dados import (
    calcular_angulo_pernas, definir_perna_da_frente, definir_pulso_da_frente,
    definir_copo_acima, calcular_distancia_pe_pulso
)
from .class_combate import DetectorCombate
from .models import Video, FrameData

import traceback 
try:
    from projeto_integrador_V.youtube_uploader import upload_video_ytb 
    youtube_uploader_available = True
    print("INFO (video_processor.py): Função 'upload_video_ytb' importada com sucesso.")
except ImportError as e_yt_import:
    youtube_uploader_available = False
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"ERRO DETALHADO AO IMPORTAR 'upload_video_ytb' de 'projeto_integrador_V.youtube_uploader':")
    print(f"Tipo do Erro: {type(e_yt_import)}"); print(f"Mensagem do Erro: {e_yt_import}")
    print("Traceback Completo:"); traceback.print_exc()
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    def upload_video_ytb(*args, **kwargs): 
        print("ERRO (placeholder): upload_video_ytb não está disponível devido a falha na importação.")
        return None 


skeleton_custom = [ 
    (0, 2), (2, 4), (1, 3), (3, 5), (6, 8), (8, 10), (7, 9), (9, 11),
    (0, 6), (1, 7), (0, 1), (6, 7)
]
KEYPOINT_FIELDS_MAP = {
    0: ('shoulder_left_x', 'shoulder_left_y'), 1: ('shoulder_right_x', 'shoulder_right_y'),
    2: ('elbow_left_x', 'elbow_left_y'),       3: ('elbow_right_x', 'elbow_right_y'),
    4: ('wrist_left_x', 'wrist_left_y'),       5: ('wrist_right_x', 'wrist_right_y'),
    6: ('hip_left_x', 'hip_left_y'),           7: ('hip_right_x', 'hip_right_y'),
    8: ('knee_left_x', 'knee_left_y'),         9: ('knee_right_x', 'knee_right_y'),
    10: ('ankle_left_x', 'ankle_left_y'),      11: ('ankle_right_x', 'ankle_right_y')
}

def process_video_with_mmpose(video_instance, django_request_object=None):
    if not ApiMmposeConfig.model_loaded or not ApiMmposeConfig.inferencer:
        video_instance.processing_status = 'failed'
        video_instance.processing_log = 'Modelo MMPose não disponível.'
        video_instance.save()
        return

    print(f"--- INICIANDO PROCESSAMENTO E UPLOAD PARA YOUTUBE ---")
    inferencer = ApiMmposeConfig.inferencer
    detector_combate_instance = DetectorCombate() 
    input_video_path = video_instance.video_file.path
    original_filename_base = os.path.splitext(os.path.basename(input_video_path))[0]
    timestamp = int(time.time())
    
    output_video_filename = f"{original_filename_base}_processed_yt_{timestamp}.mp4"
    processed_video_path_relative_to_media = os.path.join('videos', 'processed', output_video_filename)
    output_video_full_path = os.path.join(settings.MEDIA_ROOT, processed_video_path_relative_to_media)
    os.makedirs(os.path.dirname(output_video_full_path), exist_ok=True)

    video_instance.processing_status = 'processing' 
    video_instance.processing_log = "Iniciando Processamento Local e Preparação para Upload YouTube."
    video_instance.youtube_video_id = None 
    video_instance.youtube_upload_status = 'pending_local_processing' 
    video_instance.save()

    cap = None; out = None; frame_count = 0 
    all_drawn_frames = [] 
    frame_data_objects_to_create_db = [] 
    processing_error_occurred = False

    try:
        # === LOOP 1: Ler frames, processar dados, DESENHAR, armazenar frames desenhados e dados ===
        print("INFO: Iniciando Loop 1 - Leitura, Processamento de Dados MMPose e Desenhos...")
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened(): raise IOError(f"Não foi possível abrir vídeo: {input_video_path}")
        
        fps_original = int(cap.get(cv2.CAP_PROP_FPS))
        if fps_original <= 0: fps_original = 30 
        width_original = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height_original = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
        while cap.isOpened():
            ret, frame_bgr_original = cap.read()
            if not ret: break 
            frame_count += 1
            if frame_count % 100 == 0: print(f"INFO: Processando e desenhando no frame {frame_count}...")
            
            frame_to_draw_on = frame_bgr_original.copy() 
            frame_to_infer = cv2.cvtColor(frame_bgr_original, cv2.COLOR_BGR2RGB) 
            results_generator = inferencer(frame_to_infer, return_vis=False)
            result_mmpose_frame = next(results_generator) 
            
            if 'predictions' in result_mmpose_frame and result_mmpose_frame['predictions'] and \
               len(result_mmpose_frame['predictions'][0]) > 0:
                detections_cf = result_mmpose_frame['predictions'][0]
                detections_sorted_cf = sorted(detections_cf, key=lambda x: x.get('bbox_score', 0), reverse=True)
                if len(detections_sorted_cf) >= 2:
                    top2_detections_cf = detections_sorted_cf[:2]
                    bbox_pA_data = top2_detections_cf[0].get('bbox'); bbox_pB_data = top2_detections_cf[1].get('bbox')
                    bbox_pA_x = bbox_pA_data[0][0] if bbox_pA_data and len(bbox_pA_data) > 0 else float('inf')
                    bbox_pB_x = bbox_pB_data[0][0] if bbox_pB_data and len(bbox_pB_data) > 0 else float('inf')
                    ordered_detections_for_frame = [top2_detections_cf[0], top2_detections_cf[1]] if bbox_pA_x < bbox_pB_x else [top2_detections_cf[1], top2_detections_cf[0]]
                    
                    keypoints_j0_all = ordered_detections_for_frame[0].get('keypoints', [])
                    keypoints_j1_all = ordered_detections_for_frame[1].get('keypoints', [])
                    pontos_j0_fatiados = keypoints_j0_all[5:17] if len(keypoints_j0_all) >=17 else []
                    pontos_j1_fatiados = keypoints_j1_all[5:17] if len(keypoints_j1_all) >=17 else []

                    if not pontos_j0_fatiados or not pontos_j1_fatiados:
                        estado_combate_atual_para_db = detector_combate_instance.estado_combate 
                    else:
                        detector_combate_instance.atualizar(pontos_j0_fatiados, pontos_j1_fatiados)
                        estado_combate_atual_para_db = detector_combate_instance.estado_combate
                        for player_label_db, det_item_db in enumerate(ordered_detections_for_frame):
                            keypoints_fatiados_db = det_item_db['keypoints'][5:17] if len(det_item_db['keypoints']) >=17 else []
                            if not keypoints_fatiados_db or len(keypoints_fatiados_db) != 12: continue
                            
                            for (x, y) in keypoints_fatiados_db: 
                                cv2.circle(frame_to_draw_on, (int(x), int(y)), radius=3, color=(0, 255, 0), thickness=-1)
                            for start_idx, end_idx in skeleton_custom: 
                                try:
                                    cv2.line(frame_to_draw_on, 
                                             (int(keypoints_fatiados_db[start_idx][0]), int(keypoints_fatiados_db[start_idx][1])), 
                                             (int(keypoints_fatiados_db[end_idx][0]), int(keypoints_fatiados_db[end_idx][1])), 
                                             color=(255, 100, 100), thickness=1)
                                except IndexError: continue

                            data_for_model_db = {'video': video_instance, 'frame_number': frame_count, 
                                                 'player_label': player_label_db, 'combat_state': estado_combate_atual_para_db}
                            for i, (x_coord, y_coord) in enumerate(keypoints_fatiados_db):
                                field_x_name, field_y_name = KEYPOINT_FIELDS_MAP.get(i)
                                if field_x_name and field_y_name:
                                    data_for_model_db[field_x_name] = float(x_coord); data_for_model_db[field_y_name] = float(y_coord)
                            kpts_np = np.array(keypoints_fatiados_db)
                            q_esq, q_dir=kpts_np[6],kpts_np[7]; j_esq,j_dir=kpts_np[8],kpts_np[9]; t_esq,t_dir=kpts_np[10],kpts_np[11]; p_esq,p_dir=kpts_np[4],kpts_np[5]
                            data_for_model_db['left_leg_angle']=calcular_angulo_pernas(q_esq,j_esq,t_esq); data_for_model_db['right_leg_angle']=calcular_angulo_pernas(q_dir,j_dir,t_dir)
                            data_for_model_db['front_leg']=definir_perna_da_frente(player_label_db,t_esq[0],t_dir[0]); data_for_model_db['front_wrist']=definir_pulso_da_frente(player_label_db,p_esq[0],p_dir[0])
                            pulso_f_coord=p_esq if data_for_model_db['front_wrist']==0 else p_dir; pe_t_coord=t_dir if data_for_model_db['front_leg']==0 else t_esq
                            data_for_model_db['arm_base_distance']=calcular_distancia_pe_pulso(pulso_f_coord,pe_t_coord)
                            frame_data_objects_to_create_db.append(FrameData(**data_for_model_db))
                    
                    label_text = "EM COMBATE" if estado_combate_atual_para_db == "em_combate" else "FORA DE COMBATE"
                    label_color = (0, 255, 0) if estado_combate_atual_para_db == "em_combate" else (0, 0, 255)
                    (text_width, text_height), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)
                    text_x = frame_to_draw_on.shape[1] - text_width - 15; text_y = 25
                    cv2.rectangle(frame_to_draw_on, (text_x - 5, text_y - text_height - 5), (text_x + text_width + 5, text_y + 5), (50,50,50), -1)
                    cv2.putText(frame_to_draw_on, label_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, label_color, 1, cv2.LINE_AA)

            all_drawn_frames.append(frame_to_draw_on) 
        
        if cap: cap.release()
        print(f"INFO: Loop 1 concluído. {frame_count} frames lidos. {len(all_drawn_frames)} frames desenhados armazenados.")

        if frame_data_objects_to_create_db:
            frames_dict_for_cup={}; [frames_dict_for_cup.setdefault(f.frame_number,[]).append(f) for f in frame_data_objects_to_create_db]
            for f_num, p_objs in frames_dict_for_cup.items():
                if len(p_objs)==2:
                    o0=next((o for o in p_objs if o.player_label==0),None); o1=next((o for o in p_objs if o.player_label==1),None)
                    if o0 and o1: 
                        y0=o0.wrist_left_y if o0.front_wrist==0 else o0.wrist_right_y; y1=o1.wrist_left_y if o1.front_wrist==0 else o1.wrist_right_y
                        if y0 is not None and y1 is not None: o0.cup_above=definir_copo_acima(y0,y1); o1.cup_above=definir_copo_acima(y1,y0)
            try: FrameData.objects.bulk_create(frame_data_objects_to_create_db, batch_size=500); print(f"INFO: {len(frame_data_objects_to_create_db)} FrameData salvos.")
            except Exception as e_db: print(f"ERRO: bulk_create FrameData: {e_db}"); video_instance.processing_log+=f"\nErro DB: {e_db}"
        else: print("INFO: Nenhum FrameData para salvar.")

        if not all_drawn_frames:
            raise ValueError("Nenhum frame desenhado foi armazenado em memória para escrita.")

        print(f"INFO: Iniciando Loop 2 - Escrita dos {len(all_drawn_frames)} frames DESENHADOS para {output_video_full_path}...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_full_path, fourcc, fps_original, (width_original, height_original))
        if not out.isOpened():
            output_video_filename_avi = f"{original_filename_base}_processed_yt_{timestamp}.avi" 
            processed_video_path_relative_to_media_avi = os.path.join('videos', 'processed', output_video_filename_avi) 
            output_video_full_path_avi = os.path.join(settings.MEDIA_ROOT, processed_video_path_relative_to_media_avi) 
            fourcc = cv2.VideoWriter_fourcc(*'XVID'); out = cv2.VideoWriter(output_video_full_path_avi, fourcc, fps_original, (width_original, height_original))
            if not out.isOpened(): raise IOError(f"Não foi possível abrir VideoWriter para {output_video_full_path} ou {output_video_full_path_avi} no Loop 2")
            else: 
                processed_video_path_relative_to_media = processed_video_path_relative_to_media_avi
                output_video_full_path = output_video_full_path_avi
        
        for drawn_frame_to_write in all_drawn_frames: 
            out.write(drawn_frame_to_write)
        
        if out: out.release()
        print(f"INFO: Loop 2 concluído. Vídeo com frames DESENHADOS salvo em: {output_video_full_path}")
        video_instance.processed_video_file.name = processed_video_path_relative_to_media

    except Exception as e:
        print(f"ERRO EXCEPCIONAL (PROCESSAMENTO): {e}"); traceback.print_exc()
        video_instance.processing_status = 'failed' 
        video_instance.processing_log += f"\nExceção no processamento: {str(e)}"
        processing_error_occurred = True
    finally: 
        if cap and cap.isOpened(): cap.release()
        if out and out.isOpened(): out.release()

    if not processing_error_occurred:
        video_instance.processing_status = 'completed' 
        video_instance.processing_log += f'\nProcessamento local concluído. {frame_count} frames. Salvo em {output_video_full_path}.'
        
        # --- LÓGICA DE UPLOAD PARA O YOUTUBE REINTEGRADA ---
        if youtube_uploader_available and os.path.exists(output_video_full_path):
            print(f"INFO: Tentando upload de {output_video_full_path} para YouTube...")
            video_instance.youtube_upload_status = 'pending_youtube_upload'
            video_instance.save() # Salva o status antes da chamada
            title_yt = f"{video_instance.title or original_filename_base} - Análise Esgrimetrics"
            description_yt = (
                f"Análise de esgrima para o vídeo: {video_instance.title or original_filename_base}.\n"
                f"Enviado por: {video_instance.user.username if hasattr(video_instance, 'user') and video_instance.user else 'Utilizador'}\n"
                f"Processado por Esgrimetrics."
            )
            tags_yt = ["esgrima", "fencing", "análise", "esgrimetrics", "mmpose"]
            if hasattr(video_instance, 'user') and video_instance.user:
                 tags_yt.append(video_instance.user.username)
            
            
            youtube_id_str = upload_video_ytb(
                video_path=output_video_full_path,
                title=title_yt,
                description=description_yt,
            )

            if youtube_id_str:
                video_instance.youtube_video_id = youtube_id_str
                video_instance.youtube_upload_status = 'uploaded_to_youtube'
                video_instance.processing_log += f"\nVídeo enviado para YouTube com ID: {youtube_id_str}"
                print(f"INFO: Vídeo enviado para YouTube com ID: {youtube_id_str}")
            else:
                video_instance.youtube_upload_status = 'youtube_upload_failed'
                video_instance.processing_log += "\nFalha ao enviar vídeo para YouTube."
                print("ERRO: Falha ao enviar vídeo para YouTube (upload_video_ytb não retornou ID).")
        elif not youtube_uploader_available:
            video_instance.youtube_upload_status = 'youtube_module_missing'
            video_instance.processing_log += "\nMódulo de upload para YouTube não disponível."
        elif not os.path.exists(output_video_full_path):
            video_instance.youtube_upload_status = 'no_processed_file_for_youtube'
            video_instance.processing_log += "\nArquivo processado não encontrado para upload."
            
    else: 
        video_instance.youtube_upload_status = 'not_attempted_due_to_local_failure'
        video_instance.processing_log += f"\nProcessamento local falhou. Upload para YouTube não tentado."

    video_instance.save() 
    print(f"INFO: Estado final salvo. ProcStatus: {video_instance.processing_status}, YTStatus: {video_instance.youtube_upload_status}")
    print(f"--- FIM DO PROCESSAMENTO ---")
