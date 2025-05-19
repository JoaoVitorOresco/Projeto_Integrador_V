import matplotlib 
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64

# ============================================================================
# FUNÇÕES DE GERAÇÃO DE GRÁFICOS
# ============================================================================

def generate_graph_base64(fig):
    """Converte uma figura Matplotlib em uma string base64 PNG."""
    if fig is None:
        return None
    try:
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig) 
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Erro ao converter figura para base64: {e}")
        if fig:
            plt.close(fig)
        return None
    finally:
        if 'buffer' in locals():
            buffer.close()


def grafico_media_angulo_perna(dados):

    dados_renomeados = dados.rename(columns={
        'frame_number': 'frame',
        'player_label': 'jogador',
        'left_leg_angle': 'esq_angulo_perna',
        'right_leg_angle': 'dir_angulo_perna',
        'front_leg': 'perna_da_frente',
    })

    required_cols = ['frame', 'esq_angulo_perna', 'dir_angulo_perna', 'perna_da_frente', 'jogador']
    if not all(col in dados_renomeados.columns for col in required_cols):
        print(f"Erro: Colunas necessárias {required_cols} para grafico_media_angulo_perna em falta após renomear.")
        return None

    dados_renomeados['tempo_s'] = dados_renomeados['frame'] // 30

    def obter_angulo_perna_frente(row):
        if pd.isna(row['perna_da_frente']): return pd.NA
        if row['perna_da_frente'] == 0:
            return row['esq_angulo_perna']
        elif row['perna_da_frente'] == 1:
            return row['dir_angulo_perna']
        return pd.NA

    dados_renomeados['angulo_perna_frente'] = dados_renomeados.apply(obter_angulo_perna_frente, axis=1)
    dados_renomeados.dropna(subset=['angulo_perna_frente'], inplace=True)

    if dados_renomeados.empty:
        print("Erro: DataFrame vazio após processar angulo_perna_frente.")
        return None

    dados_jogador_esquerda = dados_renomeados[dados_renomeados['jogador'] == 0]
    dados_jogador_direita = dados_renomeados[dados_renomeados['jogador'] == 1]

    media_por_segundo_esquerda = dados_jogador_esquerda.groupby('tempo_s')['angulo_perna_frente'].mean() if not dados_jogador_esquerda.empty else pd.Series(dtype=float)
    media_por_segundo_direita = dados_jogador_direita.groupby('tempo_s')['angulo_perna_frente'].mean() if not dados_jogador_direita.empty else pd.Series(dtype=float)
    media_total_esquerda = dados_jogador_esquerda['angulo_perna_frente'].mean() if not dados_jogador_esquerda.empty else None
    media_total_direita = dados_jogador_direita['angulo_perna_frente'].mean() if not dados_jogador_direita.empty else None

    fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    fig.suptitle('Ângulo da Perna da Frente por Tempo (em segundos)')

    if not media_por_segundo_esquerda.empty:
        axes[0].plot(media_por_segundo_esquerda.index, media_por_segundo_esquerda.values, label='Perna da Frente', color='purple')
        if media_total_esquerda is not None:
             axes[0].axhline(media_total_esquerda, linestyle='--', color='purple', alpha=0.6, label=f'Média: {media_total_esquerda:.1f}')
    axes[0].set_title('Jogador da esquerda')
    axes[0].set_xlabel('Tempo (s)')
    axes[0].set_ylabel('Ângulo (graus)')
    axes[0].legend()
    axes[0].grid(True)

    if not media_por_segundo_direita.empty:
        axes[1].plot(media_por_segundo_direita.index, media_por_segundo_direita.values, label='Perna da Frente', color='purple')
        if media_total_direita is not None:
            axes[1].axhline(media_total_direita, linestyle='--', color='purple', alpha=0.6, label=f'Média: {media_total_direita:.1f}')
    axes[1].set_title('Jogador da direita')
    axes[1].set_xlabel('Tempo (s)')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig 

def grafico_distancia_arma_comparativo(dados):
    dados_renomeados = dados.rename(columns={
        'frame_number': 'frame',
        'player_label': 'jogador',
        'arm_base_distance': 'distancia_base_arma',
    })

    required_cols = ['frame', 'distancia_base_arma', 'jogador']
    if not all(col in dados_renomeados.columns for col in required_cols):
        print(f"Erro: Colunas necessárias {required_cols} para grafico_distancia_arma_comparativo em falta.")
        return None

    dados_renomeados['tempo_s'] = dados_renomeados['frame'] // 30
    dados_renomeados.dropna(subset=['distancia_base_arma'], inplace=True)

    if dados_renomeados.empty:
        print("Erro: DataFrame vazio após processar distancia_base_arma.")
        return None

    jogador_esq = dados_renomeados[dados_renomeados['jogador'] == 0]
    jogador_dir = dados_renomeados[dados_renomeados['jogador'] == 1]

    media_esq = jogador_esq.groupby('tempo_s')['distancia_base_arma'].mean() if not jogador_esq.empty else pd.Series(dtype=float)
    media_dir = jogador_dir.groupby('tempo_s')['distancia_base_arma'].mean() if not jogador_dir.empty else pd.Series(dtype=float)
    media_total_esq = jogador_esq['distancia_base_arma'].mean() if not jogador_esq.empty else None
    media_total_dir = jogador_dir['distancia_base_arma'].mean() if not jogador_dir.empty else None

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    fig.suptitle('Distância do Pé de Trás e da Arma por Tempo')

    if not media_esq.empty:
        axes[0].plot(media_esq.index, media_esq.values, color='green', label='Distância')
        if media_total_esq is not None:
            axes[0].axhline(media_total_esq, color='red', linestyle='--', label=f'Média: {media_total_esq:.1f}')
    axes[0].set_title('Jogador da Esquerda')
    axes[0].set_xlabel('Tempo (s)')
    axes[0].set_ylabel('Distância (pixels)')
    axes[0].legend()
    axes[0].grid(True)

    if not media_dir.empty:
        axes[1].plot(media_dir.index, media_dir.values, color='green', label='Distância')
        if media_total_dir is not None:
            axes[1].axhline(media_total_dir, color='red', linestyle='--', label=f'Média: {media_total_dir:.1f}')
    axes[1].set_title('Jogador da Direita')
    axes[1].set_xlabel('Tempo (s)')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig 

def grafico_scatter_pulso_mais_alto_comparativo(dados):
    dados_renomeados = dados.rename(columns={
        'frame_number': 'frame',
        'player_label': 'jogador',
        'front_wrist': 'pulso_da_frente',
    })

    required_cols = ['frame', 'jogador', 'pulso_da_frente', 'wrist_left_y', 'wrist_right_y']
    if not all(col in dados_renomeados.columns for col in required_cols):
        print(f"Erro: Colunas necessárias {required_cols} para grafico_scatter_pulso_mais_alto em falta.")
        return None

    def obter_y_pulso_frente(row):
        if pd.isna(row['pulso_da_frente']): return pd.NA
        if row['pulso_da_frente'] == 0:
            return row['wrist_left_y']
        elif row['pulso_da_frente'] == 1:
            return row['wrist_right_y']
        return pd.NA

    dados_renomeados['y_pulso_frente'] = dados_renomeados.apply(obter_y_pulso_frente, axis=1)
    dados_renomeados.dropna(subset=['y_pulso_frente'], inplace=True)

    if dados_renomeados.empty:
        print("Erro: DataFrame vazio após processar y_pulso_frente (scatter).")
        return None

    jogador_0 = dados_renomeados[dados_renomeados['jogador'] == 0]
    jogador_1 = dados_renomeados[dados_renomeados['jogador'] == 1]

    if jogador_0.empty or jogador_1.empty:
        print("Erro: Dados insuficientes para comparar jogadores (scatter pulso).")
        return None

    comparacoes = pd.merge(
        jogador_0[['frame', 'y_pulso_frente']],
        jogador_1[['frame', 'y_pulso_frente']],
        on='frame',
        suffixes=('_j0', '_j1'),
        how='inner'
    )

    if comparacoes.empty:
        print("Erro: Nenhum frame comum entre jogadores para comparar pulsos (scatter).")
        return None

    comparacoes['quem_mais_alto'] = comparacoes.apply(
        lambda row: 'Jogador da esquerda' if row['y_pulso_frente_j0'] < row['y_pulso_frente_j1'] else 'Jogador da direita',
        axis=1
    )

    cores = comparacoes['quem_mais_alto'].map({'Jogador da esquerda': 'blue', 'Jogador da direita': 'green'})

    fig, ax = plt.subplots(figsize=(12, 4))
    if len(comparacoes['frame']) == len(comparacoes['quem_mais_alto']) == len(cores):
         ax.scatter(comparacoes['frame'], comparacoes['quem_mais_alto'], c=cores, s=10)
    else:
        print("Erro: Inconsistência de tamanho nos dados do scatter plot.")
        plt.close(fig)
        return None
        
    ax.set_title('Pulso da Frente Mais Alto por Frame')
    ax.set_xlabel('Frame')
    ax.set_ylabel('Jogador')
    ax.grid(True)
    plt.tight_layout()
    return fig 

def grafico_media_pulso_acima_comparativo(dados):
    dados_renomeados = dados.rename(columns={
        'frame_number': 'frame',
        'player_label': 'jogador',
        'front_wrist': 'pulso_da_frente',
    })
    required_cols = ['frame', 'jogador', 'pulso_da_frente', 'wrist_left_y', 'wrist_right_y']
    if not all(col in dados_renomeados.columns for col in required_cols):
        print(f"Erro: Colunas necessárias {required_cols} para grafico_media_pulso_acima em falta.")
        return None

    def obter_y_pulso_frente(row):
        if pd.isna(row['pulso_da_frente']): return pd.NA
        if row['pulso_da_frente'] == 0:
            return row['wrist_left_y']
        elif row['pulso_da_frente'] == 1:
            return row['wrist_right_y']
        return pd.NA

    dados_renomeados['y_pulso_frente'] = dados_renomeados.apply(obter_y_pulso_frente, axis=1)
    dados_renomeados.dropna(subset=['y_pulso_frente'], inplace=True)

    if dados_renomeados.empty:
        print("Erro: DataFrame vazio após processar y_pulso_frente (media).")
        return None

    jogador_0 = dados_renomeados[dados_renomeados['jogador'] == 0]
    jogador_1 = dados_renomeados[dados_renomeados['jogador'] == 1]

    if jogador_0.empty or jogador_1.empty:
        print("Erro: Dados insuficientes para comparar jogadores (media pulso).")
        return None

    comparacoes = pd.merge(
        jogador_0[['frame', 'y_pulso_frente']],
        jogador_1[['frame', 'y_pulso_frente']],
        on='frame',
        suffixes=('_j0', '_j1'),
        how='inner'
    )

    if comparacoes.empty:
        print("Erro: Nenhum frame comum entre jogadores para comparar pulsos (media).")
        return None

    comparacoes['jogador0_acima'] = comparacoes['y_pulso_frente_j0'] < comparacoes['y_pulso_frente_j1']

    total = len(comparacoes)
    if total == 0: return None

    qtd_j0 = comparacoes['jogador0_acima'].sum()
    qtd_j1 = total - qtd_j0
    percentual_j0 = (qtd_j0 / total) * 100
    percentual_j1 = (qtd_j1 / total) * 100

    fig, ax = plt.subplots(figsize=(6, 5))
    labels = ['Jogador da esquerda', 'Jogador da direita']
    valores = [percentual_j0, percentual_j1]
    cores = ['blue', 'green']
    bars = ax.bar(labels, valores, color=cores)

    ax.set_title('Percentual de Tempo com o Pulso da Frente Mais Alto')
    ax.set_ylabel('Percentual (%)')
    ax.set_ylim(0, 100)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

    plt.tight_layout()
    return fig



