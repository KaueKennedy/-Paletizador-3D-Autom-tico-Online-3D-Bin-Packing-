# 📦 Paletizador 3D Automático (Online 3D Bin Packing)

Este projeto implementa um algoritmo de empacotamento 3D dinâmico (Online 3D Bin Packing) utilizando uma **Heurística de Queda Baseada em Grade (Grid-based Tetris Drop)**. O sistema recebe caixas de dimensões e pesos variáveis sequencialmente (sem conhecimento prévio das próximas peças) e decide em tempo real a melhor posição e rotação para alocá-las em um palete, respeitando limites físicos de volume, dimensões e peso máximo.

## 🧠 Arquitetura do Sistema

O problema do "Online Bin Packing" é NP-Difícil. Como o algoritmo não conhece o conjunto total de caixas antecipadamente, não é possível encontrar a otimização global perfeita. Para contornar isso, utilizamos uma abordagem gulosa (greedy) focada em otimização local a cada passo.

O espaço do palete é discretizado em uma grade (Grid) 2D, onde cada célula representa uma área de 10 x 10 cm. 

### Tecnologias Utilizadas
*   **Python:** Lógica principal.
*   **NumPy:** Gerenciamento do mapa de alturas (Height Map) em matrizes, garantindo cálculos vetorizados ultra-rápidos para detecção de colisões.
*   **Matplotlib:** Renderização de polígonos 3D (`Poly3DCollection`) e loop de animação assíncrono para a visualização em tempo real.

---

## ⚙️ O Algoritmo de Empilhamento

Para cada nova caixa gerada, o algoritmo executa o seguinte pipeline de decisão:

### 1. Permutação de Rotações (3D)
Dada uma caixa com dimensões originais (w, d, h), o sistema gera até 6 permutações únicas de orientação geométrica:
R = {(w,d,h), (w,h,d), (d,w,h), (d,h,w), (h,w,d), (h,d,w)}
Qualquer rotação em que uma das dimensões da base exceda os limites do palete é imediatamente descartada.

### 2. Varredura Espacial e Detecção de Apoio
Para cada rotação válida, o algoritmo varre todas as coordenadas (x, y) possíveis na grade do palete. 
Para saber em qual altura (eixo Z) a caixa irá "pousar", o sistema consulta o **Height Map** (uma matriz 2D que guarda o ponto mais alto de cada coluna do palete). A altura de apoio (Z_apoio) é o valor máximo encontrado na submatriz que a caixa ocupará.

### 3. Função de Custo e Decisão (Otimização Local)
Com centenas de posições de pouso possíveis, o algoritmo aplica duas regras restritas para escolher a vencedora:
1.  **Minimização do Eixo Z (Gravidade):** O objetivo primário é manter o centro de gravidade do palete o mais baixo possível. O algoritmo seleciona a coordenada que resulta no menor Z_apoio.
2.  **Desempate por Alinhamento (Bottom-Left Fill):** Se houver múltiplas posições com o mesmo Z_apoio (o que é comum em um palete vazio), o sistema escolhe a posição que minimiza a distância até a origem (0,0). A função de custo de desempate é: C = x + y.
    Isso garante que as caixas sejam agrupadas nos cantos, maximizando a área contígua livre para as próximas peças.

---

## 🧮 Cálculos e Métricas do Sistema

O sistema mantém rastreamento em tempo real da eficiência do empacotamento. Trabalhamos com uma unidade base c = 0.1 m (10 cm).

### Peso e Densidade
O peso de cada caixa não é puramente aleatório; ele é derivado de uma simulação física de densidade variando entre 100 e 400 kg/m³. 
*   V_caixa = (w * c) * (d * c) * (h * c)
*   W_caixa = V_caixa * densidade

### Cálculo de Volumes

*   **Volume Máximo do Palete:** Volume total da bounding box.
*   **Volume Utilizado:** Soma do volume real de todas as caixas já inseridas.
*   **Volume Morto (Dead Volume):** Um dos cálculos mais importantes do sistema. Representa o espaço vazio gerado "embaixo" das caixas quando elas se apoiam no topo de pilhas irregulares. 
    Para calcular isso computacionalmente, pegamos o volume de toda a topografia atual do palete (a soma da matriz do Height Map multiplicada pelo cubo da resolução da grade) e subtraímos o volume útil das caixas.

### Condições de Parada
O loop de empacotamento é interrompido (Game Over) quando qualquer um dos limites hard é atingido:
1.  **Limite de Peso:** Soma do peso das caixas > 1400 kg.
2.  **Limite de Volume/Dimensão:** O Z_apoio + altura da caixa excede a altura máxima permitida do palete (2.5 m) para todas as rotações em todos os pontos (x,y).
