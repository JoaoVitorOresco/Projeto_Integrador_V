import numpy as np

class DetectorCombate:
    def __init__(self, threshold_movimento=500, intervalo_frames=2, limite_mov_detectado=8,#8,
                 threshold_braco=87, threshold_angulo_perna=151, lim_minimo_mov_detectado=-12):
        self.frames_buffer = []
        self.intervalo_frames = intervalo_frames
        self.threshold_movimento = threshold_movimento
        self.limite_mov_detectado = limite_mov_detectado
        self.threshold_braco = threshold_braco
        self.threshold_angulo_perna = threshold_angulo_perna
        self.qtd_mov_detectado = 0
        self.estado_combate = "fora_de_combate"
        self.lim_minimo_mov_detectado = lim_minimo_mov_detectado

    def calcular_movimento_total(self, pontos_anteriores, pontos_atuais):
        movimento_total = 0
        for i in range(len(pontos_anteriores)):
            if pontos_anteriores[i] is None or pontos_atuais[i] is None:
                continue
            dx = pontos_anteriores[i][0] - pontos_atuais[i][0]
            dy = pontos_anteriores[i][1] - pontos_atuais[i][1]
            movimento_total += abs(dx) + abs(dy)
        return movimento_total

    def calcular_direcao_braco(self, pontos):
        # Usa o pulso_da_frente baseado na posição X
        ombro_esq, ombro_dir = pontos[0], pontos[1]
        cotovelo_esq, cotovelo_dir = pontos[2], pontos[3]
        pulso_esq, pulso_dir = pontos[4], pontos[5]

        bracos = []
        for ombro, cotovelo, pulso in [(ombro_esq, cotovelo_esq, pulso_esq), (ombro_dir, cotovelo_dir, pulso_dir)]:
            if None in (ombro, cotovelo, pulso):
                continue
            v1 = np.array(cotovelo) - np.array(ombro)
            v2 = np.array(pulso) - np.array(cotovelo)
            angulo_rad = np.arctan2(v2[1], v2[0])  # Ângulo do cotovelo → pulso
            angulo_rad = abs(angulo_rad)
            bracos.append(np.degrees(angulo_rad))
        return np.mean(bracos) if bracos else None

    def calcular_angulo_pernas_media(self, pontos):
        quadril_esq, quadril_dir = pontos[6], pontos[7]
        joelho_esq, joelho_dir = pontos[8], pontos[9]
        tornozelo_esq, tornozelo_dir = pontos[10], pontos[11]

        def angulo(a, b, c):
            ba = np.array(a) - np.array(b)
            bc = np.array(c) - np.array(b)
            cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
            return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

        ang_esq = angulo(quadril_esq, joelho_esq, tornozelo_esq)
        ang_dir = angulo(quadril_dir, joelho_dir, tornozelo_dir)
        return (ang_esq + ang_dir) / 2

    def atualizar(self, pontos_jogador0, pontos_jogador1):
        self.frames_buffer.append((pontos_jogador0, pontos_jogador1))

        if len(self.frames_buffer) > self.intervalo_frames:
            pontos_inicio = self.frames_buffer.pop(0)
            pontos_fim = self.frames_buffer[-1]

            movimento0 = self.calcular_movimento_total(pontos_inicio[0], pontos_fim[0])
            movimento1 = self.calcular_movimento_total(pontos_inicio[1], pontos_fim[1])
            movimento_total = movimento0 + movimento1

            braco_dir = np.mean([
                self.calcular_direcao_braco(pontos_fim[0]),
                self.calcular_direcao_braco(pontos_fim[1])
            ])
            angulo_perna_medio = np.mean([
                self.calcular_angulo_pernas_media(pontos_fim[0]),
                self.calcular_angulo_pernas_media(pontos_fim[1])
            ])

            print(f"[DetectorCombate] Movimento={movimento_total:.1f}, Ângulo braço={braco_dir:.1f}, Ângulo perna={angulo_perna_medio:.1f}")

            cond1 = movimento_total > self.threshold_movimento
            cond2 = braco_dir is not None and braco_dir < self.threshold_braco
            cond3 = angulo_perna_medio < self.threshold_angulo_perna

            print( cond1, cond2, cond3 )

            if sum([cond1, cond2, cond3]) >= 2:#(movimento_total > self.threshold_movimento and braco_dir is not None and braco_dir < self.threshold_braco and angulo_perna_medio < self.threshold_angulo_perna):
                if self.qtd_mov_detectado <0:
                    self.qtd_mov_detectado = 0
                self.qtd_mov_detectado += 1
                self.qtd_mov_detectado = min(self.qtd_mov_detectado, self.limite_mov_detectado)
                print(self.qtd_mov_detectado)
                if self.estado_combate == "fora_de_combate" and self.qtd_mov_detectado >= self.limite_mov_detectado/2:
                    self.qtd_mov_detectado = self.limite_mov_detectado
                    print("[DetectorCombate] Combate INICIADO")
                    self.estado_combate = "em_combate"

            else:
                self.qtd_mov_detectado -= 1
                self.qtd_mov_detectado = max(self.qtd_mov_detectado, self.lim_minimo_mov_detectado)
                print(self.qtd_mov_detectado)
                if self.estado_combate == "em_combate" and self.qtd_mov_detectado <= -8:
                    print("[DetectorCombate] Combate FINALIZADO")
                    self.estado_combate = "fora_de_combate"

        print(f"Estado atual: {self.estado_combate}")