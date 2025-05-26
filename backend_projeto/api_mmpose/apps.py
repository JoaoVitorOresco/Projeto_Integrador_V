
from django.apps import AppConfig
import sys
import os 

class ApiMmposeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_mmpose'

    inferencer = None
    model_loaded = False

    def ready(self):
        """
        Este método é chamado pelo Django quando a aplicação está pronta.
        Ideal para inicializações como carregar modelos de ML.
        """
        running_server = 'runserver' in sys.argv
        is_main_process = os.environ.get('RUN_MAIN') == 'true' or not running_server

        if running_server and is_main_process and not ApiMmposeConfig.model_loaded:
            print("-" * 30)
            print("Executando ApiMmposeConfig.ready() para carregar o modelo MMPose...")

            try:
                print("Tentando importar MMPoseInferencer...")
                from mmpose.apis import MMPoseInferencer
                import torch 

                pose2d_config_path = 'x'
                pose2d_weights_path = 'x'


                if not os.path.exists(pose2d_config_path):
                    raise FileNotFoundError(f"Ficheiro de configuração do modelo não encontrado: {pose2d_config_path}")
                if not os.path.exists(pose2d_weights_path):
                    raise FileNotFoundError(f"Ficheiro de pesos do modelo não encontrado: {pose2d_weights_path}")

                print(f"A inicializar MMPoseInferencer com:")
                print(f"  Config: {pose2d_config_path}")
                print(f"  Weights: {pose2d_weights_path}")

                device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
                print(f"A utilizar dispositivo: {device}")

                ApiMmposeConfig.inferencer = MMPoseInferencer(
                    pose2d=pose2d_config_path,
                    pose2d_weights=pose2d_weights_path,
                    device=device
                )
                
                ApiMmposeConfig.model_loaded = True
                print(f"--- Modelo MMPose PERSONALIZADO ({os.path.basename(pose2d_config_path)}) CARREGADO com sucesso! ---")

            except ImportError as e:
                print(f"!!! ERRO: Falha ao IMPORTAR dependências do MMPose em apps.py: {e}")
                ApiMmposeConfig.inferencer = None
                ApiMmposeConfig.model_loaded = False
            except FileNotFoundError as e:
                print(f"!!! ERRO: Ficheiro do modelo não encontrado: {e}")
                ApiMmposeConfig.inferencer = None
                ApiMmposeConfig.model_loaded = False
            except Exception as e: 
                print(f"!!! ERRO: Falha ao INICIALIZAR modelo MMPose em apps.py: {e}")
                ApiMmposeConfig.inferencer = None
                ApiMmposeConfig.model_loaded = False
            print("-" * 30)
        elif not running_server:
            print("ApiMmposeConfig.ready(): Não é 'runserver', modelo não será carregado.")
        elif ApiMmposeConfig.model_loaded:
            print("ApiMmposeConfig.ready(): Modelo já carregado.")

