import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.animation as animation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# --- CONFIGURAÇÕES DO PALETE ---
# Trabalhamos em unidades de 10cm (0.1m) para formar a grade
PALLET_W_CELLS = 10  # 1.0 metro
PALLET_D_CELLS = 10  # 1.0 metro
PALLET_H_CELLS = 25  # 2.5 metros
CELL_SIZE = 0.1      # metros
MAX_WEIGHT = 1400.0  # kg
MAX_VOLUME = (PALLET_W_CELLS * CELL_SIZE) * (PALLET_D_CELLS * CELL_SIZE) * (PALLET_H_CELLS * CELL_SIZE)

class PaletizadorTetris:
    def __init__(self):
        self.reset()

    def reset(self):
        # Mapa de alturas que guarda a altura atual de cada coluna (x, y)
        self.height_map = np.zeros((PALLET_W_CELLS, PALLET_D_CELLS), dtype=int)
        self.boxes = []
        self.current_weight = 0.0
        self.used_volume_cells = 0
        self.game_over = False
        self.next_box = self.generate_box()

    def generate_box(self):
        # Dimensões aleatórias entre 10cm (1) e 80cm (8) para não encher muito rápido
        w = np.random.randint(1, 9)
        d = np.random.randint(1, 9)
        h = np.random.randint(1, 9)
        
        # Volume da caixa em m³
        vol_m3 = (w * CELL_SIZE) * (d * CELL_SIZE) * (h * CELL_SIZE)
        
        # Peso baseado em uma densidade aleatória (ex: 100 a 400 kg/m³)
        density = np.random.uniform(100, 400)
        weight = vol_m3 * density
        
        return (w, d, h, weight)

    def step(self):
        if self.game_over:
            return False

        w, d, h, weight = self.next_box

        # Verifica se o peso excede o limite do palete
        if self.current_weight + weight > MAX_WEIGHT:
            self.game_over = True
            return False

        best_z = float('inf')
        best_pos = None
        best_dim = None

        # Testa as 6 orientações 3D da caixa
        rotations = list(set([
            (w, d, h), (w, h, d), (d, w, h), 
            (d, h, w), (h, w, d), (h, d, w)
        ]))

        for (rw, rd, rh) in rotations:
            # Pula se a dimensão não couber nos limites do palete
            if rw > PALLET_W_CELLS or rd > PALLET_D_CELLS or rh > PALLET_H_CELLS:
                continue

            # Testa todas as posições x,y possíveis
            for x in range(PALLET_W_CELLS - rw + 1):
                for y in range(PALLET_D_CELLS - rd + 1):
                    # Acha o ponto mais alto naquela região para "apoiar" a caixa
                    z = np.max(self.height_map[x:x+rw, y:y+rd])
                    
                    # Verifica se não vai estourar a altura máxima do palete
                    if z + rh <= PALLET_H_CELLS:
                        # Regra de decisão: menor altura de encaixe. Em empate, mais perto do canto (x+y)
                        if z < best_z:
                            best_z = z
                            best_pos = (x, y, z)
                            best_dim = (rw, rd, rh)
                        elif z == best_z:
                            if best_pos is None or (x + y < best_pos[0] + best_pos[1]):
                                best_pos = (x, y, z)
                                best_dim = (rw, rd, rh)

        # Se não achou posição válida, o palete está cheio
        if best_pos is None:
            self.game_over = True
            return False

        # Aplica a caixa no mapa de alturas
        x, y, z = best_pos
        rw, rd, rh = best_dim

        self.height_map[x:x+rw, y:y+rd] = z + rh
        
        # Cor aleatória para visualização
        color = plt.cm.get_cmap('Set3')(np.random.rand())
        
        self.boxes.append({
            'pos': (x, y, z),
            'dim': (rw, rd, rh),
            'weight': weight,
            'color': color
        })
        
        self.current_weight += weight
        self.used_volume_cells += (rw * rd * rh)

        # Gera a próxima caixa que ficará "aguardando"
        self.next_box = self.generate_box()
        return True

    def get_stats(self):
        used_vol_m3 = self.used_volume_cells * (CELL_SIZE**3)
        # Volume morto = (Volume de toda a base abaixo do ponto mais alto) - Volume real usado
        total_vol_under_heightmap = np.sum(self.height_map) * (CELL_SIZE**3)
        dead_vol_m3 = total_vol_under_heightmap - used_vol_m3
        
        return used_vol_m3, dead_vol_m3

# --- INTERFACE E VISUALIZAÇÃO ---

def create_box_faces(pos, dim):
    x, y, z = pos
    dx, dy, dz = dim
    
    # Converte de células para metros
    x, y, z = x * CELL_SIZE, y * CELL_SIZE, z * CELL_SIZE
    dx, dy, dz = dx * CELL_SIZE, dy * CELL_SIZE, dz * CELL_SIZE

    vertices = [
        [x, y, z], [x+dx, y, z], [x+dx, y+dy, z], [x, y+dy, z],
        [x, y, z+dz], [x+dx, y, z+dz], [x+dx, y+dy, z+dz], [x, y+dy, z+dz]
    ]
    
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]], # Fundo
        [vertices[4], vertices[5], vertices[6], vertices[7]], # Topo
        [vertices[0], vertices[1], vertices[5], vertices[4]], # Frente
        [vertices[2], vertices[3], vertices[7], vertices[6]], # Trás
        [vertices[1], vertices[2], vertices[6], vertices[5]], # Direita
        [vertices[0], vertices[3], vertices[7], vertices[4]]  # Esquerda
    ]
    return faces

# Inicializa o motor do jogo e a figura
tracker = PaletizadorTetris()

fig = plt.figure(figsize=(12, 8))
fig.canvas.manager.set_window_title("Paletizador 3D Automático")
ax = fig.add_subplot(111, projection='3d')
fig.subplots_adjust(left=0.05, right=0.7, bottom=0.15)

# Textos de UI
ui_next_box = fig.text(0.72, 0.85, "", fontsize=12, family='monospace', verticalalignment='top')
ui_stats = fig.text(0.72, 0.60, "", fontsize=12, family='monospace', verticalalignment='top')
ui_status = fig.text(0.72, 0.95, "", fontsize=14, color='red', weight='bold', verticalalignment='top')

def init_plot():
    ax.clear()
    # Ajusta a proporção real visual no gráfico (1 x 1 x 2.5)
    ax.set_box_aspect([1, 1, 2.5])
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.0)
    ax.set_zlim(0, 2.5)
    ax.set_xlabel('Largura (m)')
    ax.set_ylabel('Profundidade (m)')
    ax.set_zlabel('Altura (m)')
    
    # Desenha as linhas das bordas do palete
    edges = [
        ([0,1], [0,0], [0,0]), ([0,1], [1,1], [0,0]), ([0,0], [0,1], [0,0]), ([1,1], [0,1], [0,0]),
        ([0,1], [0,0], [2.5,2.5]), ([0,1], [1,1], [2.5,2.5]), ([0,0], [0,1], [2.5,2.5]), ([1,1], [0,1], [2.5,2.5]),
        ([0,0], [0,0], [0,2.5]), ([1,1], [0,0], [0,2.5]), ([0,0], [1,1], [0,2.5]), ([1,1], [1,1], [0,2.5])
    ]
    for edge in edges:
        ax.plot(edge[0], edge[1], edge[2], color='black', linewidth=1, alpha=0.3)

    ui_status.set_text("EMPACOTANDO...")

def update_ui():
    w, d, h, weight = tracker.next_box
    next_box_txt = (
        "📦 PRÓXIMA CAIXA:\n"
        "------------------\n"
        f"Largura: {w*CELL_SIZE:.2f} m\n"
        f"Profund.: {d*CELL_SIZE:.2f} m\n"
        f"Altura: {h*CELL_SIZE:.2f} m\n"
        f"Peso: {weight:.1f} kg"
    )
    ui_next_box.set_text(next_box_txt)

    used_vol, dead_vol = tracker.get_stats()
    vol_percent = (used_vol / MAX_VOLUME) * 100
    
    stats_txt = (
        "📊 STATUS DO PALETE:\n"
        "------------------\n"
        f"Peso: {tracker.current_weight:.1f} / {MAX_WEIGHT} kg\n\n"
        f"Vol Max: {MAX_VOLUME:.2f} m³\n"
        f"Vol Usado: {used_vol:.2f} m³ ({vol_percent:.1f}%)\n"
        f"Vol Morto: {dead_vol:.2f} m³\n"
        f"(Espaço inútil sob caixas)"
    )
    ui_stats.set_text(stats_txt)

def update(frame):
    if not tracker.game_over:
        success = tracker.step()
        
        if success:
            # Pega a última caixa adicionada e a renderiza
            box = tracker.boxes[-1]
            faces = create_box_faces(box['pos'], box['dim'])
            poly3d = Poly3DCollection(faces, facecolors=box['color'], linewidths=1, edgecolors='black', alpha=0.9)
            ax.add_collection3d(poly3d)
            update_ui()
        else:
            ui_status.set_text("PALETE CHEIO!\n(Volume ou Peso máximo)")

def reset_callback(event):
    tracker.reset()
    init_plot()
    update_ui()

# Configuração do Botão
ax_btn = plt.axes([0.72, 0.15, 0.2, 0.075])
btn_reset = Button(ax_btn, 'Reiniciar Palete', color='lightblue', hovercolor='0.975')
btn_reset.on_clicked(reset_callback)

# Inicialização
init_plot()
update_ui()

# Loop de animação (Adiciona uma caixa a cada 800ms)
ani = animation.FuncAnimation(fig, update, interval=800, cache_frame_data=False)

plt.show()
