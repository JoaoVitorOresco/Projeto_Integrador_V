import numpy as np

def calcular_angulo_pernas(p1, p2, p3):
    """
    Calcula o ângulo (em graus) formado pelos três pontos (p1, p2, p3),
    com p2 sendo o vértice do ângulo.

    p1, p2, p3: coordenadas (x, y)
    """
    a = np.array(p1)
    b = np.array(p2)
    c = np.array(p3)

    # Vetores
    ba = a - b
    bc = c - b

    # Calcula o ângulo
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

    return np.degrees(angle)

def definir_pulso_da_frente(player_label, pulso_esq_x, pulso_dir_x):
    """
    Decide qual pulso (esquerdo ou direito) está mais à frente no eixo X.
    Retorna 0 para o pulso esquerdo, 1 para o direito.
    """
    if player_label == 0:
        # Jogador 0 anda para a direita (pulso com maior X é o da frente)
        return 0 if pulso_esq_x > pulso_dir_x else 1
    else:
        # Jogador 1 anda para a esquerda (pulso com menor X é o da frente)
        return 0 if pulso_esq_x < pulso_dir_x else 1

def definir_copo_acima(pulso_atual_y, pulso_adversario_y):
    """
    Define se o pulso do jogador está mais alto (menor valor de Y) que o do adversário.
    Retorna 1 se sim (copo acima), 0 se não.
    """
    return 1 if pulso_atual_y < pulso_adversario_y else 0

def definir_perna_da_frente(player_label, tornozelo_esq_x, tornozelo_dir_x):
    """
    Decide qual perna está mais à frente baseado nos tornozelos esquerdo e direito.
    Retorna 0 se a perna esquerda está na frente, 1 se a direita.
    """
    if player_label == 0:
        # Jogador 0 anda para a direita (perna com maior X é a da frente)
        return 0 if tornozelo_esq_x > tornozelo_dir_x else 1
    else:
        # Jogador 1 anda para a esquerda (perna com menor X é a da frente)
        return 0 if tornozelo_esq_x < tornozelo_dir_x else 1

def calcular_distancia_pe_pulso(tornozelo_tras, pulso_frente):
    """
    Calcula a distância euclidiana entre o tornozelo de trás e o pulso de ataque (da frente).
    tornozelo_tras, pulso_frente: (x, y)
    """
    t = np.array(tornozelo_tras)
    p = np.array(pulso_frente)
    distancia = np.linalg.norm(t - p)
    return distancia