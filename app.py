# app.py - Streamlit UI para Sleeping Barber (com detecção de deadlock e log otimizado)
import streamlit as st
import time
import datetime
from barber_simulation import BarberSimulation
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title='Sleeping Barber - Visual', layout='wide')

st.title('Problema do Barbeiro Dorminhoco — Visualização ao vivo')

# -------------------------
# Sidebar (controles globais)
# -------------------------
st.sidebar.header('Configurações da Simulação')
num_barbers = st.sidebar.number_input('Número de barbeiros', min_value=1, max_value=10, value=2, step=1)
num_chairs = st.sidebar.number_input('Número de cadeiras na sala de espera', min_value=0, max_value=25, value=5, step=1)
arrival_rate = st.sidebar.slider('Tempo médio entre chegadas (s)', 0.1, 5.0, 1.0, 0.1)
enable_solution = st.sidebar.checkbox('Ativar solução para evitar deadlock (Modo SAFE)', value=True)
deadlock_timeout = st.sidebar.number_input('Tempo (s) para detectar possível deadlock', min_value=1.0, max_value=30.0, value=4.0, step=0.5)
show_logs = st.sidebar.checkbox('Mostrar log de eventos', value=False)

# -------------------------
# Layout principal: visual à esquerda, controles/estatísticas à direita
# -------------------------
col1, col2 = st.columns([2, 1])

with col1:
    deadlock_placeholder = st.empty()
    vis_placeholder = st.empty()

with col2:
    controls_box = st.container()
    stat_placeholder = st.empty()
    notes_box = st.container()
    if show_logs:
        log_expander = st.expander("Log de eventos (últimas entradas)", expanded=True)
        log_placeholder = log_expander.container().empty()
    else:
        log_placeholder = st.empty()

# -------------------------
# Inicializa session_state usado pelo laço
# -------------------------
if 'sim' not in st.session_state:
    st.session_state.sim = None
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'last_snapshot' not in st.session_state:
    st.session_state.last_snapshot = None
if 'last_progress_time' not in st.session_state:
    st.session_state.last_progress_time = time.time()
if 'last_served_count' not in st.session_state:
    st.session_state.last_served_count = 0
if 'deadlock_detected' not in st.session_state:
    st.session_state.deadlock_detected = False

MAX_LOG_LINES = 500

def _now_ts():
    return datetime.datetime.now().strftime("%H:%M:%S")

def append_log(line: str):
    logs = st.session_state.logs
    logs.append(f"[{_now_ts()}] {line}")
    if len(logs) > MAX_LOG_LINES:
        logs = logs[-MAX_LOG_LINES:]
    st.session_state.logs = logs

# -------------------------
# Controles (botões)
# -------------------------
with controls_box:
    st.markdown('### Controles')
    start_btn = st.button('Iniciar Simulação')
    stop_btn = st.button('Parar Simulação')
    reset_btn = st.button('Reiniciar (parar + limpar logs)')
    st.markdown('---')
    notes_box.markdown("### Notas")
    notes_box.write("No **Modo BUGGY** (sem a solução ativada), a simulação é propositalmente falha para ilustrar como deadlocks podem ocorrer.")

    if start_btn:
        if st.session_state.sim is None:
            sim = BarberSimulation(
                num_barbers=num_barbers,
                num_chairs=num_chairs,
                arrival_rate=arrival_rate,
                enable_solution=enable_solution,
            )
            sim.start()
            st.session_state.sim = sim
            st.session_state.logs = []
            st.session_state.last_snapshot = None
            st.session_state.last_progress_time = time.time()
            st.session_state.last_served_count = 0
            st.session_state.deadlock_detected = False
            append_log("Simulação iniciada (Modo SAFE)" if enable_solution else "Simulação iniciada (Modo BUGGY)")
        else:
            st.warning('Simulação já em execução. Pare primeiro para reiniciar.')

    if stop_btn:
        if st.session_state.sim is not None:
            st.session_state.sim.stop()
            st.session_state.sim = None
            append_log("Simulação parada pelo usuário.")
        else:
            st.info("Nenhuma simulação em execução.")

    if reset_btn:
        if st.session_state.sim is not None:
            st.session_state.sim.stop()
        st.session_state.sim = None
        st.session_state.logs = []
        st.session_state.last_snapshot = None
        st.session_state.last_served_count = 0
        st.session_state.deadlock_detected = False
        st.session_state.last_progress_time = time.time()
        append_log("Simulação reiniciada (estado limpo).")

# -------------------------
# Função de desenho (vis)
# -------------------------
def draw_snapshot(snap):
    fig, ax = plt.subplots(figsize=(10, 4)) # Aumenta um pouco a figura
    ax.axis('off')
    ax.set_title('Sala de Espera & Barbeiros', fontsize=14, weight='bold')

    chairs = snap['num_chairs']
    waiting = snap['waiting']
    barber_states = snap['barber_states']

    # Cadeiras de espera
    if chairs > 0:
        # Define posições para as cadeiras de forma equidistante
        chair_xs = np.linspace(0, chairs - 1, chairs)
        for i, x in enumerate(chair_xs):
            y = 1
            if i < len(waiting):
                circle = plt.Circle((x, y), 0.35, color="#4a90e2")
                ax.text(x, y, str(waiting[i]), va='center', ha='center', color='white', fontsize=9, weight='bold')
            else:
                circle = plt.Circle((x, y), 0.35, edgecolor="#999", facecolor="none", lw=1.5, ls='--')
            ax.add_patch(circle)

    # Barbeiros
    colors = {"idle": "#bbb", "serving": "#4caf50", "sleeping": "#e53935"}
    barber_xs = np.linspace(0, chairs - 1, len(barber_states)) if chairs > 1 else [0]
    
    for i, state in enumerate(barber_states):
        x = barber_xs[i]
        y = -0.5
        color_key = "serving" if "serving" in state else state
        color = colors.get(color_key, colors["idle"])

        # CORREÇÃO: Removido o argumento 'radius' que causava o erro.
        rect = plt.Rectangle((x - 0.45, y - 0.35), 0.9, 0.7,
                             facecolor=color, edgecolor="black", lw=1.5)
        ax.add_patch(rect)
        ax.text(x, y, f"Barbeiro {i+1}\n{state}", va='center', ha='center',
                fontsize=9, color="white" if color != "#bbb" else "black", weight='bold')

    # CORREÇÃO: Define o aspect ratio como 'equal' para garantir que os círculos não achatem
    ax.set_aspect('equal', adjustable='box')
    
    # Ajusta os limites para dar um bom espaçamento visual
    if chairs > 0:
        ax.set_xlim(-1, chairs)
    ax.set_ylim(-1.5, 2)
    
    fig.tight_layout(pad=1.0)
    return fig

# -------------------------
# Loop principal de atualização
# -------------------------
while st.session_state.get('sim', None):
    sim = st.session_state.sim
    snap = sim.snapshot()
    prev = st.session_state.last_snapshot
    now = time.time()

    # Log de eventos
    if prev:
        if snap['customer_count'] > prev['customer_count']:
            new_arrivals = snap['customer_count'] - prev['customer_count']
            turned_away = snap['turned_away_count'] - prev['turned_away_count']
            entered = new_arrivals - turned_away
            if entered > 0:
                append_log(f"{entered} cliente(s) entraram na barbearia.")
            if turned_away > 0:
                append_log(f"{turned_away} cliente(s) desistiram (sem lugar).")

        if snap['served_count'] > prev['served_count']:
            append_log(f"Cliente atendido. (Total: {snap['served_count']})")
        
        for i, (old_s, new_s) in enumerate(zip(prev['barber_states'], snap['barber_states'])):
            if old_s != new_s:
                append_log(f"Barbeiro {i+1}: {old_s} -> {new_s}")

    # Detecção de deadlock
    if snap['served_count'] > st.session_state.last_served_count:
        st.session_state.last_served_count = snap['served_count']
        st.session_state.last_progress_time = now
        if st.session_state.deadlock_detected:
            st.session_state.deadlock_detected = False
            append_log("Progresso detectado — possível deadlock resolvido.")
    else:
        time_since_progress = now - st.session_state.last_progress_time
        waiting_len = len(snap['waiting'])
        is_serving = any('serving' in s for s in snap['barber_states'])
        if time_since_progress > deadlock_timeout and waiting_len > 0 and not is_serving:
            if not st.session_state.deadlock_detected:
                st.session_state.deadlock_detected = True
                reason = ("Modo BUGGY: Barbeiros 'dormiram' sem serem notificados da chegada de clientes.") if not enable_solution else \
                         ("Falta de progresso detectada. Verifique se a taxa de chegada é muito alta.")
                append_log(f"DEADLOCK PROVÁVEL — Motivo: {reason}")

    # Renderização
    stat_placeholder.markdown(
        f"**Clientes chegados:** `{snap['customer_count']}`  \n"
        f"**Clientes atendidos:** `{snap['served_count']}`  \n"
        f"**Clientes dispensados:** `{snap['turned_away_count']}`  \n" # Novo
        f"**Cadeiras ocupadas:** `{len(snap['waiting'])} / {snap['num_chairs']}`  \n"
        f"**Modo:** `{'SAFE (Solução Ativa)' if enable_solution else 'BUGGY (Propenso a Deadlock)'}`"
    )

    if st.session_state.deadlock_detected:
        reason_short = ("Os barbeiros não estão acordando para atender os clientes na fila. "
                        "Isso ocorre no modo BUGGY devido a uma 'condição de corrida', onde o sinal para acordar é perdido.")
        html = (
            f'<div style="padding:14px;border-radius:8px;background:#b00020;color:white;">'
            f'<strong style="font-size:18px">⚠ DEADLOCK DETECTADO</strong><br>'
            f'<span style="font-size:13px">{reason_short}</span>'
            f'</div>'
        )
        deadlock_placeholder.markdown(html, unsafe_allow_html=True)
    else:
        deadlock_placeholder.empty()

    fig = draw_snapshot(snap)
    vis_placeholder.pyplot(fig, use_container_width=True)

    if show_logs:
        log_text = "\n".join(st.session_state.logs[-200:])
        log_placeholder.code(log_text)
    
    st.session_state.last_snapshot = snap
    time.sleep(0.4) # Intervalo de atualização

# Se o loop terminar (simulação parada), limpa a interface
if not st.session_state.get('sim', None):
    stat_placeholder.info('Simulação parada. Configure e pressione "Iniciar Simulação".')
    deadlock_placeholder.empty()
    vis_placeholder.empty()

