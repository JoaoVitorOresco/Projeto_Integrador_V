import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import base64
import numpy as np 
import seaborn as sns 
from matplotlib.collections import LineCollection 

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
    """Helper para aplicar filtro de estado de combate."""
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

# --- Funções de Gráfico Existentes (já usam nomes corretos após rename) ---
def grafico_media_angulo_perna(dados, estado_combate_filtro=None):
    print(f"DEBUG (angulo_perna): Iniciando. Filtro: {estado_combate_filtro}")
    dados_para_grafico = _aplicar_filtro_combate(dados, estado_combate_filtro)
    if dados_para_grafico is None or dados_para_grafico.empty:
        print(f"Info (angulo_perna): Dados insuficientes após filtro '{estado_combate_filtro}'.")
        return None
    dados_renomeados = dados_para_grafico.rename(columns={'frame_number':'frame','player_label':'jogador','left_leg_angle':'esq_angulo_perna','right_leg_angle':'dir_angulo_perna','front_leg':'perna_da_frente'})
    required_cols = ['frame','esq_angulo_perna','dir_angulo_perna','perna_da_frente','jogador']
    if not all(col in dados_renomeados.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in dados_renomeados.columns]; print(f"Erro (angulo_perna): Colunas {missing_cols} em falta."); return None
    dados_renomeados['tempo_s'] = dados_renomeados['frame'] // 30
    def obter_angulo_perna_frente(row):
        if pd.isna(row['perna_da_frente']): return pd.NA
        if row['perna_da_frente'] == 0: return row['esq_angulo_perna']
        elif row['perna_da_frente'] == 1: return row['dir_angulo_perna']
        return pd.NA
    dados_renomeados['angulo_perna_frente'] = dados_renomeados.apply(obter_angulo_perna_frente, axis=1)
    dados_renomeados.dropna(subset=['angulo_perna_frente'], inplace=True)
    if dados_renomeados.empty: print("Info (angulo_perna): DataFrame vazio."); return None
    dados_j0 = dados_renomeados[dados_renomeados['jogador']==0]; dados_j1 = dados_renomeados[dados_renomeados['jogador']==1]
    media_s_j0 = dados_j0.groupby('tempo_s')['angulo_perna_frente'].mean() if not dados_j0.empty else pd.Series(dtype=float)
    media_s_j1 = dados_j1.groupby('tempo_s')['angulo_perna_frente'].mean() if not dados_j1.empty else pd.Series(dtype=float)
    media_t_j0 = dados_j0['angulo_perna_frente'].mean() if not dados_j0.empty else None
    media_t_j1 = dados_j1['angulo_perna_frente'].mean() if not dados_j1.empty else None
    fig,axes=plt.subplots(1,2,figsize=(12,6),sharey=True); title_suffix = f' (Estado: {estado_combate_filtro.replace("_"," ").title()})' if estado_combate_filtro else ""; fig.suptitle(f'Ângulo da Perna da Frente{title_suffix}')
    if not media_s_j0.empty: axes[0].plot(media_s_j0.index,media_s_j0.values,label='Perna da Frente',color='purple',marker='o',linestyle='-');_ = axes[0].axhline(media_t_j0,linestyle='--',color='darkorchid',alpha=0.7,label=f'Média: {media_t_j0:.1f}°') if media_t_j0 else None
    axes[0].set_title('Jogador da Esquerda');axes[0].set_xlabel('Tempo (s)');axes[0].set_ylabel('Ângulo Médio (°)') ;axes[0].legend();axes[0].grid(True,linestyle=':',alpha=0.7)
    if not media_s_j1.empty: axes[1].plot(media_s_j1.index,media_s_j1.values,label='Perna da Frente',color='purple',marker='o',linestyle='-');_ = axes[1].axhline(media_t_j1,linestyle='--',color='darkorchid',alpha=0.7,label=f'Média: {media_t_j1:.1f}°') if media_t_j1 else None
    axes[1].set_title('Jogador da Direita');axes[1].set_xlabel('Tempo (s)');axes[1].legend();axes[1].grid(True,linestyle=':',alpha=0.7)
    plt.tight_layout(rect=[0,0.03,1,0.93]); print("DEBUG (angulo_perna): Geração concluída."); return fig

def grafico_distancia_arma_comparativo(dados, estado_combate_filtro=None):
    print(f"DEBUG (distancia_arma): Iniciando. Filtro: {estado_combate_filtro}"); dados_para_grafico = _aplicar_filtro_combate(dados, estado_combate_filtro)
    if dados_para_grafico is None or dados_para_grafico.empty: print(f"Info (distancia_arma): Dados insuficientes após filtro '{estado_combate_filtro}'."); return None
    dados_renomeados = dados_para_grafico.rename(columns={'frame_number':'frame','player_label':'jogador','arm_base_distance':'distancia_base_arma'})
    required_cols = ['frame','distancia_base_arma','jogador']; 
    if not all(col in dados_renomeados.columns for col in required_cols): missing_cols = [col for col in required_cols if col not in dados_renomeados.columns]; print(f"Erro (distancia_arma): Colunas {missing_cols} em falta."); return None
    dados_renomeados['tempo_s'] = dados_renomeados['frame'] // 30; dados_renomeados.dropna(subset=['distancia_base_arma'], inplace=True)
    if dados_renomeados.empty: print("Info (distancia_arma): DataFrame vazio."); return None
    j0=dados_renomeados[dados_renomeados['jogador']==0]; j1=dados_renomeados[dados_renomeados['jogador']==1]
    m_s_j0=j0.groupby('tempo_s')['distancia_base_arma'].mean() if not j0.empty else pd.Series(dtype=float); m_s_j1=j1.groupby('tempo_s')['distancia_base_arma'].mean() if not j1.empty else pd.Series(dtype=float)
    m_t_j0=j0['distancia_base_arma'].mean() if not j0.empty else None; m_t_j1=j1['distancia_base_arma'].mean() if not j1.empty else None
    fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True); title_suffix = f' (Estado: {estado_combate_filtro.replace("_"," ").title()})' if estado_combate_filtro else ""; fig.suptitle(f'Distância Média Pé de Trás-Arma{title_suffix}')
    if not m_s_j0.empty: axes[0].plot(m_s_j0.index,m_s_j0.values,color='darkcyan',label='Dist. Média',marker='.',linestyle='-');_ = axes[0].axhline(m_t_j0,color='teal',linestyle='--',label=f'Média Geral: {m_t_j0:.1f}px') if m_t_j0 else None
    axes[0].set_title('Jogador da Esquerda');axes[0].set_xlabel('Tempo (s)');axes[0].set_ylabel('Dist. Média (px)');axes[0].legend();axes[0].grid(True,linestyle=':',alpha=0.7)
    if not m_s_j1.empty: axes[1].plot(m_s_j1.index,m_s_j1.values,color='darkcyan',label='Dist. Média',marker='.',linestyle='-');_ = axes[1].axhline(m_t_j1,color='teal',linestyle='--',label=f'Média Geral: {m_t_j1:.1f}px') if m_t_j1 else None
    axes[1].set_title('Jogador da Direita');axes[1].set_xlabel('Tempo (s)');axes[1].legend();axes[1].grid(True,linestyle=':',alpha=0.7)
    plt.tight_layout(rect=[0,0.03,1,0.93]); print("DEBUG (distancia_arma): Geração concluída."); return fig

def grafico_scatter_pulso_mais_alto_comparativo(dados, estado_combate_filtro=None):
    print(f"DEBUG (scatter_pulso): Iniciando. Filtro: {estado_combate_filtro}"); dados_para_grafico = _aplicar_filtro_combate(dados, estado_combate_filtro)
    if dados_para_grafico is None or dados_para_grafico.empty: print(f"Info (scatter_pulso): Dados insuficientes após filtro '{estado_combate_filtro}'."); return None
    dados_renomeados = dados_para_grafico.rename(columns={'frame_number':'frame','player_label':'jogador', 'front_wrist':'pulso_da_frente'})
    required_cols=['frame','jogador','pulso_da_frente','wrist_left_y','wrist_right_y']
    if not all(col in dados_renomeados.columns for col in required_cols): missing_cols=[col for col in required_cols if col not in dados_renomeados.columns]; print(f"Erro (scatter_pulso): Colunas {missing_cols} em falta."); return None
    def obter_y_pulso_frente(row):
        if pd.isna(row['pulso_da_frente']): return pd.NA
        if row['pulso_da_frente']==0: return row['wrist_left_y'] 
        elif row['pulso_da_frente']==1: return row['wrist_right_y'] 
        return pd.NA
    dados_renomeados['y_pulso_frente']=dados_renomeados.apply(obter_y_pulso_frente,axis=1); dados_renomeados.dropna(subset=['y_pulso_frente'],inplace=True)
    if dados_renomeados.empty: print("Info (scatter_pulso): DataFrame vazio."); return None
    j0=dados_renomeados[dados_renomeados['jogador']==0]; j1=dados_renomeados[dados_renomeados['jogador']==1]
    if j0.empty or j1.empty: print("Info (scatter_pulso): Dados insuficientes para um ou ambos jogadores."); return None
    comp=pd.merge(j0[['frame','y_pulso_frente']],j1[['frame','y_pulso_frente']],on='frame',suffixes=('_j0','_j1'),how='inner')
    if comp.empty: print("Info (scatter_pulso): Nenhum frame comum."); return None
    comp['quem_mais_alto_num']=comp.apply(lambda r:0 if r['y_pulso_frente_j0']<r['y_pulso_frente_j1'] else(1 if r['y_pulso_frente_j1']<r['y_pulso_frente_j0'] else 2),axis=1)
    map_j={0:'Jogador da Esquerda',1:'Jogador da Direita',2:'Empate (Mesma Altura)'}; map_c={0:'blue',1:'green',2:'grey'}
    comp['quem_mais_alto_label']=comp['quem_mais_alto_num'].map(map_j)
    fig,ax=plt.subplots(figsize=(12,5)); title_suffix = f' (Estado: {estado_combate_filtro.replace("_"," ").title()})' if estado_combate_filtro else ""; 
    for i,lbl in map_j.items():
        subset=comp[comp['quem_mais_alto_num']==i]
        if not subset.empty: ax.scatter(subset['frame'],subset['quem_mais_alto_label'],color=map_c[i],label=lbl,s=20,alpha=0.7)
    ax.set_title(f'Pulso da Frente Mais Alto por Frame{title_suffix}');ax.set_xlabel('Número do Frame');ax.set_ylabel('Jogador');ax.grid(True,linestyle=':',alpha=0.5,axis='x')
    ax.legend(title="Jogador",bbox_to_anchor=(1.05,1),loc='upper left');plt.yticks(list(map_j.values()));plt.tight_layout(rect=[0,0,0.85,1]); print("DEBUG (scatter_pulso): Geração concluída."); return fig

def grafico_media_pulso_acima_comparativo(dados, estado_combate_filtro=None):
    print(f"DEBUG (media_pulso_acima): Iniciando. Filtro: {estado_combate_filtro}"); dados_para_grafico = _aplicar_filtro_combate(dados, estado_combate_filtro)
    if dados_para_grafico is None or dados_para_grafico.empty: print(f"Info (media_pulso_acima): Dados insuficientes após filtro '{estado_combate_filtro}'."); return None
    dados_renomeados = dados_para_grafico.rename(columns={'frame_number':'frame','player_label':'jogador','front_wrist':'pulso_da_frente'})
    required_cols=['frame','jogador','pulso_da_frente','wrist_left_y','wrist_right_y']
    if not all(col in dados_renomeados.columns for col in required_cols): missing_cols=[col for col in required_cols if col not in dados_renomeados.columns]; print(f"Erro (media_pulso_acima): Colunas {missing_cols} em falta."); return None
    def obter_y_pulso_frente(row):
        if pd.isna(row['pulso_da_frente']): return pd.NA
        if row['pulso_da_frente']==0: return row['wrist_left_y']
        elif row['pulso_da_frente']==1: return row['wrist_right_y']
        return pd.NA
    dados_renomeados['y_pulso_frente']=dados_renomeados.apply(obter_y_pulso_frente,axis=1); dados_renomeados.dropna(subset=['y_pulso_frente'],inplace=True)
    if dados_renomeados.empty: print("Info (media_pulso_acima): DataFrame vazio."); return None
    j0=dados_renomeados[dados_renomeados['jogador']==0]; j1=dados_renomeados[dados_renomeados['jogador']==1]
    if j0.empty or j1.empty: print("Info (media_pulso_acima): Dados insuficientes."); return None
    comp=pd.merge(j0[['frame','y_pulso_frente']],j1[['frame','y_pulso_frente']],on='frame',suffixes=('_j0','_j1'),how='inner')
    if comp.empty: print("Info (media_pulso_acima): Nenhum frame comum."); return None
    comp['j0_acima']=comp['y_pulso_frente_j0']<comp['y_pulso_frente_j1']; comp['empate']=abs(comp['y_pulso_frente_j0']-comp['y_pulso_frente_j1'])<1.0
    total_comp=len(comp); 
    if total_comp==0: print("Info (media_pulso_acima): Nenhum frame para comparação."); return None
    qtd_j0_estrito=comp[~comp['empate']&comp['j0_acima']].shape[0]; qtd_j1_estrito=comp[~comp['empate']&~comp['j0_acima']].shape[0]; qtd_emp=comp['empate'].sum()
    total_dif=qtd_j0_estrito+qtd_j1_estrito
    p_j0=(qtd_j0_estrito/total_dif)*100 if total_dif>0 else 0; p_j1=(qtd_j1_estrito/total_dif)*100 if total_dif>0 else 0; p_emp=(qtd_emp/total_comp)*100
    fig,ax=plt.subplots(figsize=(8,6)); lbls=['Esq. Mais Alto','Dir. Mais Alto','Empate']; vals=[p_j0,p_j1,p_emp]; clrs=['cornflowerblue','mediumseagreen','silver']
    bars=ax.bar(lbls,vals,color=clrs,width=0.6); title_suffix = f' (Estado: {estado_combate_filtro.replace("_"," ").title()})' if estado_combate_filtro else ""; ax.set_title(f'Percentual de Tempo com Pulso da Frente Mais Alto{title_suffix}')
    ax.set_ylabel('Percentual de Frames (%)');ax.set_ylim(0,100)
    for bar in bars: height=bar.get_height(); ax.text(bar.get_x()+bar.get_width()/2.,height+1,f'{height:.1f}%',ha='center',va='bottom',fontsize=9)
    plt.xticks(rotation=15,ha="right");plt.tight_layout(); print("DEBUG (media_pulso_acima): Geração concluída."); return fig

# --- NOVAS FUNÇÕES DE GRÁFICO (COM CORREÇÕES DE IMPORT E NOMES DE COLUNA) ---


def _prepare_pulso_data(dados_df, estado_combate_filtro):
    print(f"DEBUG (_prepare_pulso_data): Iniciando. Filtro: {estado_combate_filtro}")
    dados_para_analise = _aplicar_filtro_combate(dados_df, estado_combate_filtro)
    if dados_para_analise is None or dados_para_analise.empty:
        print(f"Info (_prepare_pulso_data): Dados insuficientes após filtro '{estado_combate_filtro}'.")
        return None

    df_pulsos = dados_para_analise.copy()
    required_kpt_cols = ['frame_number', 'player_label', 'front_wrist', 
                           'wrist_left_x', 'wrist_left_y', 'wrist_right_x', 'wrist_right_y']
    if not all(col in df_pulsos.columns for col in required_kpt_cols):
        missing_cols = [col for col in required_kpt_cols if col not in df_pulsos.columns]
        print(f"Erro (_prepare_pulso_data): Colunas dos pulsos ({missing_cols}) ou 'front_wrist' não encontradas.")
        return None
    
    def obter_coord_pulso_frente(row):
        if pd.isna(row['front_wrist']): return [np.nan, np.nan]
        if row['front_wrist'] == 0: return [row['wrist_left_x'], row['wrist_left_y']]
        elif row['front_wrist'] == 1: return [row['wrist_right_x'], row['wrist_right_y']]
        return [np.nan, np.nan]

    pulso_frente_coords = df_pulsos.apply(obter_coord_pulso_frente, axis=1)
    df_pulsos[['pulso_frente_x', 'pulso_frente_y']] = pd.DataFrame(pulso_frente_coords.to_list(), index=df_pulsos.index)
    df_pulsos.dropna(subset=['pulso_frente_x', 'pulso_frente_y'], inplace=True)
    
    if df_pulsos.empty: print("Info (_prepare_pulso_data): DataFrame vazio após extrair coordenadas do pulso da frente.")
    return df_pulsos

def grafico_heatmap_pulso_frente(dados, jogador_label, cmap_color, titulo_jogador, estado_combate_filtro=None):
    # ... (código mantido como na versão anterior do artefato, já usa _prepare_pulso_data) ...
    dados_jogador = _prepare_pulso_data(dados, estado_combate_filtro)
    if dados_jogador is None or dados_jogador.empty: print(f"Info (heatmap_pulso {titulo_jogador}): Dados insuficientes."); return None
    jogador_data = dados_jogador[dados_jogador['player_label'] == jogador_label]
    if jogador_data.empty or jogador_data[['pulso_frente_x','pulso_frente_y']].isnull().all().all(): print(f"Info (heatmap_pulso {titulo_jogador}): Sem dados válidos."); return None
    fig,ax=plt.subplots(figsize=(8,7)); sns.kdeplot(x=jogador_data['pulso_frente_x'].astype(float),y=jogador_data['pulso_frente_y'].astype(float),cmap=cmap_color,fill=True,ax=ax,bw_adjust=0.5,thresh=0.05,levels=10)
    title_suffix = f' (Estado: {estado_combate_filtro.replace("_"," ").title()})' if estado_combate_filtro else ""; ax.set_title(f'Mapa de Calor - Pulso da Frente\n{titulo_jogador}{title_suffix}')
    ax.set_xlabel('Posição X (px)');ax.set_ylabel('Posição Y (px)');ax.grid(True,linestyle=':',alpha=0.6);plt.tight_layout(); print(f"DEBUG (heatmap_pulso {titulo_jogador}): Geração concluída."); return fig

def grafico_velocidade_pulso_frente(dados, jogador_label, cor_linha, titulo_jogador, estado_combate_filtro=None):
    # ... (código mantido como na versão anterior do artefato, já usa _prepare_pulso_data) ...
    dados_jogador_vel = _prepare_pulso_data(dados, estado_combate_filtro)
    if dados_jogador_vel is None or dados_jogador_vel.empty: print(f"Info (velocidade_pulso {titulo_jogador}): Dados insuficientes."); return None
    jogador = dados_jogador_vel[dados_jogador_vel['player_label'] == jogador_label].sort_values('frame_number')
    if jogador.empty or len(jogador)<2: print(f"Info (velocidade_pulso {titulo_jogador}): Pontos insuficientes ({len(jogador)})."); return None
    jogador['tempo_s']=jogador['frame_number']/30.0; dx=jogador['pulso_frente_x'].diff(); dy=jogador['pulso_frente_y'].diff(); dt=jogador['tempo_s'].diff()
    vel_inst=np.sqrt(dx**2+dy**2)/dt; vel_inst=vel_inst.fillna(0).replace([np.inf,-np.inf],0)
    fig,ax=plt.subplots(figsize=(12,5)); ax.plot(jogador['tempo_s'],vel_inst,color=cor_linha,alpha=0.8,linewidth=1.5)
    if len(vel_inst)>=5: media_movel=vel_inst.rolling(window=5,center=True,min_periods=1).mean(); ax.plot(jogador['tempo_s'],media_movel,color='red',linestyle='--',linewidth=1,label='Média Móvel (5f)'); ax.legend()
    title_suffix = f' (Estado: {estado_combate_filtro.replace("_"," ").title()})' if estado_combate_filtro else ""; ax.set_title(f'Velocidade do Pulso da Frente\n{titulo_jogador}{title_suffix}')
    ax.set_xlabel('Tempo (s)');ax.set_ylabel('Velocidade (px/s)');ax.grid(True,linestyle=':',alpha=0.7);ax.set_ylim(bottom=0);plt.tight_layout(); print(f"DEBUG (velocidade_pulso {titulo_jogador}): Geração concluída."); return fig

def grafico_trajetoria_pulso_frente(dados, jogador_label, cmap_color, titulo_jogador, estado_combate_filtro=None):
    # ... (código mantido como na versão anterior do artefato, já usa _prepare_pulso_data) ...
    dados_jogador_traj = _prepare_pulso_data(dados, estado_combate_filtro)
    if dados_jogador_traj is None or dados_jogador_traj.empty: print(f"Info (trajetoria_pulso {titulo_jogador}): Dados insuficientes."); return None
    jogador = dados_jogador_traj[dados_jogador_traj['player_label'] == jogador_label].sort_values('frame_number'); jogador = jogador.dropna(subset=['pulso_frente_x','pulso_frente_y'])
    if jogador.empty or len(jogador)<2: print(f"Info (trajetoria_pulso {titulo_jogador}): Pontos insuficientes ({len(jogador)})."); return None
    fig,ax=plt.subplots(figsize=(8,7)); x=jogador['pulso_frente_x'].values; y=jogador['pulso_frente_y'].values
    pts=np.array([x,y]).T.reshape(-1,1,2); segs=np.concatenate([pts[:-1],pts[1:]],axis=1)
    lc=LineCollection(segs,cmap=plt.get_cmap(cmap_color),norm=plt.Normalize(0,1),linewidth=2,alpha=0.8); lc.set_array(np.linspace(0,1,len(segs))); line=ax.add_collection(lc)
    ax.plot(x[0],y[0],'o',markersize=8,markerfacecolor='lime',markeredgecolor='black',label='Início'); ax.plot(x[-1],y[-1],'X',markersize=10,markerfacecolor='red',markeredgecolor='black',label='Fim')
    cbar=fig.colorbar(line,ax=ax,orientation='vertical',fraction=0.046,pad=0.04,ticks=[0,1]); cbar.ax.set_yticklabels(['Início','Fim']); cbar.set_label('Progressão Temporal',rotation=270,labelpad=15)
    if not jogador.empty: ax.set_xlim(x.min()-20,x.max()+20); ax.set_ylim(y.min()-20,y.max()+20) # Ajustado para usar x.min/max e y.min/max
    title_suffix = f' (Estado: {estado_combate_filtro.replace("_"," ").title()})' if estado_combate_filtro else ""; ax.set_title(f'Trajetória do Pulso da Frente\n{titulo_jogador}{title_suffix}')
    ax.set_xlabel('Posição X (px)');ax.set_ylabel('Posição Y (px)');ax.legend();ax.grid(True,linestyle=':',alpha=0.6);ax.set_aspect('equal',adjustable='box');plt.tight_layout(); print(f"DEBUG (trajetoria_pulso {titulo_jogador}): Geração concluída."); return fig

# Funções wrapper (mantidas)
def grafico_heatmap_pulso_frente_esquerda(dados, estado_combate_filtro=None): return grafico_heatmap_pulso_frente(dados,0,'Blues','Jogador da Esquerda',estado_combate_filtro)
def grafico_heatmap_pulso_frente_direita(dados, estado_combate_filtro=None): return grafico_heatmap_pulso_frente(dados,1,'Greens','Jogador da Direita',estado_combate_filtro)
def grafico_velocidade_pulso_frente_esquerda(dados, estado_combate_filtro=None): return grafico_velocidade_pulso_frente(dados,0,'blue','Jogador da Esquerda',estado_combate_filtro)
def grafico_velocidade_pulso_frente_direita(dados, estado_combate_filtro=None): return grafico_velocidade_pulso_frente(dados,1,'green','Jogador da Direita',estado_combate_filtro)
def grafico_trajetoria_pulso_frente_esquerda(dados, estado_combate_filtro=None): return grafico_trajetoria_pulso_frente(dados,0,'Blues','Jogador da Esquerda',estado_combate_filtro)
def grafico_trajetoria_pulso_frente_direita(dados, estado_combate_filtro=None): return grafico_trajetoria_pulso_frente(dados,1,'Greens','Jogador da Direita',estado_combate_filtro)