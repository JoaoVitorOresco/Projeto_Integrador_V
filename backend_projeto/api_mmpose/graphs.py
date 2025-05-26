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
        print("DEBUG (generate_graph_base64): Figura é None, retornando None.")
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
        if 'buffer' in locals() and not buffer.closed:
            buffer.close()


def _aplicar_filtro_combate(dados_df, estado_combate_filtro):
    """Helper para aplicar filtro de estado de combate e verificar colunas."""
    if estado_combate_filtro:
        if 'combat_state' not in dados_df.columns:
            print(f"Erro (Helper Filtro): Coluna 'combat_state' não encontrada nos dados de entrada para aplicar filtro '{estado_combate_filtro}'.")
            return None 
        
        dados_filtrados = dados_df[dados_df['combat_state'] == estado_combate_filtro].copy()
        
        if dados_filtrados.empty:
            print(f"Info (Helper Filtro): Nenhum dado encontrado para o estado_combate_filtro: '{estado_combate_filtro}'.")
            return pd.DataFrame()
        return dados_filtrados
    return dados_df.copy()


def grafico_media_angulo_perna(dados, estado_combate_filtro=None):
    print(f"DEBUG (angulo_perna): Iniciando. Filtro de combate: {estado_combate_filtro}")
    
    dados_para_grafico = _aplicar_filtro_combate(dados, estado_combate_filtro)
    if dados_para_grafico is None or dados_para_grafico.empty: 
        print(f"Info (angulo_perna): Dados insuficientes após aplicar filtro '{estado_combate_filtro}'.")
        return None

    dados_renomeados = dados_para_grafico.rename(columns={
        'frame_number': 'frame',
        'player_label': 'jogador',
        'left_leg_angle': 'esq_angulo_perna',
        'right_leg_angle': 'dir_angulo_perna',
        'front_leg': 'perna_da_frente',
    })

    required_cols = ['frame', 'esq_angulo_perna', 'dir_angulo_perna', 'perna_da_frente', 'jogador']
    if not all(col in dados_renomeados.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in dados_renomeados.columns]
        print(f"Erro (angulo_perna): Colunas necessárias {missing_cols} em falta após renomear.")
        return None

    dados_renomeados['tempo_s'] = dados_renomeados['frame'] // 30

    def obter_angulo_perna_frente(row):
        if pd.isna(row['perna_da_frente']): return pd.NA
        if row['perna_da_frente'] == 0: return row['esq_angulo_perna']
        elif row['perna_da_frente'] == 1: return row['dir_angulo_perna']
        return pd.NA

    dados_renomeados['angulo_perna_frente'] = dados_renomeados.apply(obter_angulo_perna_frente, axis=1)
    dados_renomeados.dropna(subset=['angulo_perna_frente'], inplace=True)

    if dados_renomeados.empty:
        print("Info (angulo_perna): DataFrame vazio após processar angulo_perna_frente.")
        return None

    
    dados_jogador_esquerda = dados_renomeados[dados_renomeados['jogador'] == 0]
    dados_jogador_direita = dados_renomeados[dados_renomeados['jogador'] == 1]

    media_por_segundo_esquerda = dados_jogador_esquerda.groupby('tempo_s')['angulo_perna_frente'].mean() if not dados_jogador_esquerda.empty else pd.Series(dtype=float)
    media_por_segundo_direita = dados_jogador_direita.groupby('tempo_s')['angulo_perna_frente'].mean() if not dados_jogador_direita.empty else pd.Series(dtype=float)
    media_total_esquerda = dados_jogador_esquerda['angulo_perna_frente'].mean() if not dados_jogador_esquerda.empty else None
    media_total_direita = dados_jogador_direita['angulo_perna_frente'].mean() if not dados_jogador_direita.empty else None

    fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    titulo_grafico = 'Ângulo da Perna da Frente'
    if estado_combate_filtro:
        titulo_grafico += f' (Estado: {estado_combate_filtro.replace("_", " ").title()})'
    fig.suptitle(titulo_grafico)

    if not media_por_segundo_esquerda.empty:
        axes[0].plot(media_por_segundo_esquerda.index, media_por_segundo_esquerda.values, label='Perna da Frente', color='purple', marker='o', linestyle='-')
        if media_total_esquerda is not None:
            axes[0].axhline(media_total_esquerda, linestyle='--', color='darkorchid', alpha=0.7, label=f'Média: {media_total_esquerda:.1f}°')
    axes[0].set_title('Jogador da Esquerda')
    axes[0].set_xlabel('Tempo (s)')
    axes[0].set_ylabel('Ângulo Médio (graus)')
    axes[0].legend()
    axes[0].grid(True, linestyle=':', alpha=0.7)

    if not media_por_segundo_direita.empty:
        axes[1].plot(media_por_segundo_direita.index, media_por_segundo_direita.values, label='Perna da Frente', color='purple', marker='o', linestyle='-')
        if media_total_direita is not None:
            axes[1].axhline(media_total_direita, linestyle='--', color='darkorchid', alpha=0.7, label=f'Média: {media_total_direita:.1f}°')
    axes[1].set_title('Jogador da Direita')
    axes[1].set_xlabel('Tempo (s)')
    axes[1].legend()
    axes[1].grid(True, linestyle=':', alpha=0.7)

    plt.tight_layout(rect=[0, 0.03, 1, 0.93]) 
    print("DEBUG (angulo_perna): Geração de gráfico concluída.")
    return fig 

def grafico_distancia_arma_comparativo(dados, estado_combate_filtro=None):
    print(f"DEBUG (distancia_arma): Iniciando. Filtro de combate: {estado_combate_filtro}")
    dados_para_grafico = _aplicar_filtro_combate(dados, estado_combate_filtro)
    if dados_para_grafico is None or dados_para_grafico.empty:
        print(f"Info (distancia_arma): Dados insuficientes após aplicar filtro '{estado_combate_filtro}'.")
        return None

    dados_renomeados = dados_para_grafico.rename(columns={
        'frame_number': 'frame', 'player_label': 'jogador', 'arm_base_distance': 'distancia_base_arma',
    })
    required_cols = ['frame', 'distancia_base_arma', 'jogador']
    if not all(col in dados_renomeados.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in dados_renomeados.columns]
        print(f"Erro (distancia_arma): Colunas necessárias {missing_cols} em falta.")
        return None
    dados_renomeados['tempo_s'] = dados_renomeados['frame'] // 30
    dados_renomeados.dropna(subset=['distancia_base_arma'], inplace=True)
    if dados_renomeados.empty:
        print("Info (distancia_arma): DataFrame vazio após processar distancia_base_arma.")
        return None

    jogador_esq = dados_renomeados[dados_renomeados['jogador'] == 0]
    jogador_dir = dados_renomeados[dados_renomeados['jogador'] == 1]
    media_esq = jogador_esq.groupby('tempo_s')['distancia_base_arma'].mean() if not jogador_esq.empty else pd.Series(dtype=float)
    media_dir = jogador_dir.groupby('tempo_s')['distancia_base_arma'].mean() if not jogador_dir.empty else pd.Series(dtype=float)
    media_total_esq = jogador_esq['distancia_base_arma'].mean() if not jogador_esq.empty else None
    media_total_dir = jogador_dir['distancia_base_arma'].mean() if not jogador_dir.empty else None

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    titulo_grafico = 'Distância Média Pé de Trás-Arma'
    if estado_combate_filtro:
        titulo_grafico += f' (Estado: {estado_combate_filtro.replace("_", " ").title()})'
    fig.suptitle(titulo_grafico)
    
    if not media_esq.empty:
        axes[0].plot(media_esq.index, media_esq.values, color='darkcyan', label='Distância Média', marker='.', linestyle='-')
        if media_total_esq is not None:
            axes[0].axhline(media_total_esq, color='teal', linestyle='--', label=f'Média Geral: {media_total_esq:.1f}px')
    axes[0].set_title('Jogador da Esquerda'); axes[0].set_xlabel('Tempo (s)'); axes[0].set_ylabel('Distância Média (pixels)'); axes[0].legend(); axes[0].grid(True, linestyle=':', alpha=0.7)
    if not media_dir.empty:
        axes[1].plot(media_dir.index, media_dir.values, color='darkcyan', label='Distância Média', marker='.', linestyle='-')
        if media_total_dir is not None:
            axes[1].axhline(media_total_dir, color='teal', linestyle='--', label=f'Média Geral: {media_total_dir:.1f}px')
    axes[1].set_title('Jogador da Direita'); axes[1].set_xlabel('Tempo (s)'); axes[1].legend(); axes[1].grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout(rect=[0, 0.03, 1, 0.93])
    print("DEBUG (distancia_arma): Geração de gráfico concluída.")
    return fig 

def grafico_scatter_pulso_mais_alto_comparativo(dados, estado_combate_filtro=None):
    print(f"DEBUG (scatter_pulso): Iniciando. Filtro de combate: {estado_combate_filtro}")
    dados_para_grafico = _aplicar_filtro_combate(dados, estado_combate_filtro)
    if dados_para_grafico is None or dados_para_grafico.empty:
        print(f"Info (scatter_pulso): Dados insuficientes após aplicar filtro '{estado_combate_filtro}'.")
        return None
        
    dados_renomeados = dados_para_grafico.rename(columns={
        'frame_number': 'frame', 'player_label': 'jogador', 'front_wrist': 'pulso_da_frente',
    })
    required_cols = ['frame', 'jogador', 'pulso_da_frente', 'wrist_left_y', 'wrist_right_y']
    if not all(col in dados_renomeados.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in dados_renomeados.columns]
        print(f"Erro (scatter_pulso): Colunas necessárias {missing_cols} em falta.")
        return None
    def obter_y_pulso_frente(row):
        if pd.isna(row['pulso_da_frente']): return pd.NA
        if row['pulso_da_frente'] == 0: return row['wrist_left_y']
        elif row['pulso_da_frente'] == 1: return row['wrist_right_y']
        return pd.NA
    dados_renomeados['y_pulso_frente'] = dados_renomeados.apply(obter_y_pulso_frente, axis=1)
    dados_renomeados.dropna(subset=['y_pulso_frente'], inplace=True)
    if dados_renomeados.empty:
        print("Info (scatter_pulso): DataFrame vazio após processar y_pulso_frente.")
        return None
    

    jogador_0 = dados_renomeados[dados_renomeados['jogador'] == 0]
    jogador_1 = dados_renomeados[dados_renomeados['jogador'] == 1]
    if jogador_0.empty or jogador_1.empty:
        print("Info (scatter_pulso): Dados insuficientes para um ou ambos jogadores.")
        return None
    comparacoes = pd.merge(jogador_0[['frame','y_pulso_frente']], jogador_1[['frame','y_pulso_frente']], on='frame', suffixes=('_j0','_j1'), how='inner')
    if comparacoes.empty:
        print("Info (scatter_pulso): Nenhum frame comum entre jogadores.")
        return None
    comparacoes['quem_mais_alto_num'] = comparacoes.apply(lambda r: 0 if r['y_pulso_frente_j0'] < r['y_pulso_frente_j1'] else (1 if r['y_pulso_frente_j1'] < r['y_pulso_frente_j0'] else 2), axis=1)
    map_jogador = {0: 'Jogador da Esquerda', 1: 'Jogador da Direita', 2: 'Empate (Mesma Altura)'}
    map_cor = {0: 'blue', 1: 'green', 2: 'grey'}
    comparacoes['quem_mais_alto_label'] = comparacoes['quem_mais_alto_num'].map(map_jogador)
    
    fig, ax = plt.subplots(figsize=(12, 5))
    titulo_grafico = 'Pulso da Frente Mais Alto por Frame'
    if estado_combate_filtro:
        titulo_grafico += f' (Estado: {estado_combate_filtro.replace("_", " ").title()})'
    
    for i, jogador_label in map_jogador.items():
        subset = comparacoes[comparacoes['quem_mais_alto_num'] == i]
        if not subset.empty:
            ax.scatter(subset['frame'], subset['quem_mais_alto_label'], color=map_cor[i], label=jogador_label, s=20, alpha=0.7)
    ax.set_title(titulo_grafico)
    ax.set_xlabel('Número do Frame'); ax.set_ylabel('Jogador com Pulso Mais Alto'); ax.grid(True, linestyle=':', alpha=0.5, axis='x')
    ax.legend(title="Jogador", bbox_to_anchor=(1.05, 1), loc='upper left'); plt.yticks(list(map_jogador.values()))
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    print("DEBUG (scatter_pulso): Geração de gráfico concluída.")
    return fig 

def grafico_media_pulso_acima_comparativo(dados, estado_combate_filtro=None):
    print(f"DEBUG (media_pulso_acima): Iniciando. Filtro de combate: {estado_combate_filtro}")
    dados_para_grafico = _aplicar_filtro_combate(dados, estado_combate_filtro)
    if dados_para_grafico is None or dados_para_grafico.empty:
        print(f"Info (media_pulso_acima): Dados insuficientes após aplicar filtro '{estado_combate_filtro}'.")
        return None
        
    dados_renomeados = dados_para_grafico.rename(columns={
        'frame_number': 'frame', 'player_label': 'jogador', 'front_wrist': 'pulso_da_frente',
    })
    required_cols = ['frame', 'jogador', 'pulso_da_frente', 'wrist_left_y', 'wrist_right_y']
    if not all(col in dados_renomeados.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in dados_renomeados.columns]
        print(f"Erro (media_pulso_acima): Colunas necessárias {missing_cols} em falta.")
        return None
    def obter_y_pulso_frente(row):
        if pd.isna(row['pulso_da_frente']): return pd.NA
        if row['pulso_da_frente'] == 0: return row['wrist_left_y']
        elif row['pulso_da_frente'] == 1: return row['wrist_right_y']
        return pd.NA
    dados_renomeados['y_pulso_frente'] = dados_renomeados.apply(obter_y_pulso_frente, axis=1)
    dados_renomeados.dropna(subset=['y_pulso_frente'], inplace=True)
    if dados_renomeados.empty:
        print("Info (media_pulso_acima): DataFrame vazio após processar y_pulso_frente.")
        return None


    jogador_0 = dados_renomeados[dados_renomeados['jogador'] == 0]; jogador_1 = dados_renomeados[dados_renomeados['jogador'] == 1]
    if jogador_0.empty or jogador_1.empty:
        print("Info (media_pulso_acima): Dados insuficientes para um ou ambos jogadores.")
        return None
    comparacoes = pd.merge(jogador_0[['frame','y_pulso_frente']], jogador_1[['frame','y_pulso_frente']], on='frame', suffixes=('_j0','_j1'), how='inner')
    if comparacoes.empty:
        print("Info (media_pulso_acima): Nenhum frame comum entre jogadores.")
        return None
    comparacoes['jogador0_acima'] = comparacoes['y_pulso_frente_j0'] < comparacoes['y_pulso_frente_j1']
    comparacoes['empate_altura'] = abs(comparacoes['y_pulso_frente_j0'] - comparacoes['y_pulso_frente_j1']) < 1.0 
    total_frames_comparados = len(comparacoes)
    if total_frames_comparados == 0: print("Info (media_pulso_acima): Nenhum frame para comparação."); return None
    qtd_j0_estritamente_acima = comparacoes[~comparacoes['empate_altura'] & comparacoes['jogador0_acima']].shape[0]
    qtd_j1_estritamente_acima = comparacoes[~comparacoes['empate_altura'] & ~comparacoes['jogador0_acima']].shape[0]
    qtd_empates = comparacoes['empate_altura'].sum()
    total_frames_com_diferenca = qtd_j0_estritamente_acima + qtd_j1_estritamente_acima
    percentual_j0 = (qtd_j0_estritamente_acima / total_frames_com_diferenca) * 100 if total_frames_com_diferenca > 0 else 0
    percentual_j1 = (qtd_j1_estritamente_acima / total_frames_com_diferenca) * 100 if total_frames_com_diferenca > 0 else 0
    percentual_empate = (qtd_empates / total_frames_comparados) * 100
    
    fig, ax = plt.subplots(figsize=(8, 6))
    labels = ['Jogador da Esquerda Mais Alto', 'Jogador da Direita Mais Alto', 'Empate (Altura Similar)']
    valores = [percentual_j0, percentual_j1, percentual_empate]
    cores = ['cornflowerblue', 'mediumseagreen', 'silver']
    bars = ax.bar(labels, valores, color=cores, width=0.6)
    titulo_grafico = 'Percentual de Tempo com Pulso da Frente Mais Alto'
    if estado_combate_filtro:
        titulo_grafico += f' (Estado: {estado_combate_filtro.replace("_", " ").title()})'
    ax.set_title(titulo_grafico)
    ax.set_ylabel('Percentual de Frames (%)'); ax.set_ylim(0, 100)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    plt.xticks(rotation=15, ha="right"); plt.tight_layout()
    print("DEBUG (media_pulso_acima): Geração de gráfico concluída.")
    return fig