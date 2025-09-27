# app.py - Streamlit UI para Sleeping Barber (com detecção de deadlock e log otimizado)
import streamlit as st
import time
import datetime
from barber_simulation import BarberSimulation
import matplotlib.pyplot as plt

st.set_page_config(page_title='Sleeping Barber - Visual', layout='wide')

st.title('Problema do Barbeiro Dorminhoco — Visualização ao vivo')

# -------------------------
# Sidebar (controles globais)
# -------------------------
st.sidebar.header('Configurações da Simulação')
num_barbers = st.sidebar.number_input('Número de barbeiros', min_value=1, max_value=10, value=2, step=1)
num_chairs = st.sidebar.number_input('Número de cadeiras na sala de espera', min_value=0, max_value=20, value=5, step=1)
arrival_rate = st.sidebar.slider('Tempo médio entre chegadas (segundos)', 0.1, 5.0, 1.0, 0.1)
enable_solution = st.sidebar.checkbox('Ativar soluções para evitar deadlock (recomendado)', value=True)
deadlock_timeout = st.sidebar.number_input('Tempo (s) para detectar possível deadlock', min_value=1.0, max_value=30.0, value=4.0, step=0.5)
show_logs = st.sidebar.checkbox('Mostrar log de eventos', value=False)

# -------------------------
# Layout principal: visual à esquerda, controles/estatísticas à direita
# -------------------------
col1, col2 = st.columns([2, 1])

# placeholders fixos (evita criar novas seções a cada atualização)
with col1:
    deadlock_placeholder = st.empty()
    vis_placeholder = st.empty()

with col2:
    controls_box = st.container()
    stat_placeholder = st.empty()
    notes_box = st.container()
    # log expander (um único espaço para logs para não recriar seções toda atualização)
    if show_logs:
        log_expander = st.expander("Log de eventos (últimas entradas)", expanded=True)
        log_placeholder = log_expander.container().empty()
    else:
        # placeholder inativo quando logs não solicitados
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

MAX_LOG_LINES = 500  # limite para não crescer indefinidamente


def _now_ts():
    return datetime.datetime.now().strftime("%H:%M:%S")


def append_log(line: str):
    logs = st.session_state.logs
    logs.append(f"[{_now_ts()}] {line}")
    # mantém apenas as últimas linhas para otimização
    if len(logs) > MAX_LOG_LINES:
        logs = logs[-MAX_LOG_LINES:]
    st.session_state.logs = logs


# -------------------------
# Controles (botões) - ficam na coluna direita
# -------------------------
with controls_box:
    st.markdown('### Controles')
    start_btn = st.button('Iniciar Simulação')
    stop_btn = st.button('Parar Simulação')
    reset_btn = st.button('Reiniciar (stop + limpar logs)')
    st.markdown('---')
    notes_box.markdown("### Notas")
    notes_box.write('No modo **BUGGY**, a simulação tenta reproduzir comportamento incorreto que pode levar a bloqueios (deadlock).')

    # iniciar simulação
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
            # reset estado de monitoramento
            st.session_state.logs = []
            st.session_state.last_snapshot = None
            st.session_state.last_progress_time = time.time()
            st.session_state.last_served_count = 0
            st.session_state.deadlock_detected = False
            append_log("Simulação iniciada (modo SAFE)" if enable_solution else "Simulação iniciada (modo BUGGY)")
        else:
            st.warning('Simulação já em execução. Pare primeiro para reiniciar com novas configurações.')

    # parar simulação
    if stop_btn:
        if st.session_state.sim is not None:
            try:
                st.session_state.sim.stop()
            except Exception:
                pass
            st.session_state.sim = None
            append_log("Simulação parada pelo usuário.")
        else:
            st.info("Não há simulação em execução.")

    # reiniciar totalmente (stop + limpa logs)
    if reset_btn:
        if st.session_state.sim is not None:
            try:
                st.session_state.sim.stop()
            except Exception:
                pass
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
    fig, ax = plt.subplots(figsize=(5, 3))  # levemente menor para ocupar coluna
    ax.set_title('Sala de espera & Barbeiros')
    ax.axis('off')

    chairs = snap['num_chairs']
    waiting = snap['waiting']
    barber_states = snap['barber_states']

    # desenha cadeiras (linha superior)
    for i in range(chairs):
        x = i
        y = 1
        circle = plt.Circle((x, y), 0.28, linewidth=1)
        if i < len(waiting):
            ax.add_patch(circle)
            ax.text(x, y, str(waiting[i]), va='center', ha='center', color='white')
        else:
            ax.add_patch(circle)
            # desenha contorno (sem preenchimento) - já feito por default

    # desenha barbeiros (linha inferior)
    for i in range(len(barber_states)):
        x = i * 2
        y = -1
        state = barber_states[i]
        rect = plt.Rectangle((x - 0.4, y - 0.3), 0.8, 0.6, linewidth=1)
        ax.add_patch(rect)
        ax.text(x, y, f'B{i}\n{state}', va='center', ha='center')

    ax.set_xlim(-1, max(chairs, len(barber_states) * 2))
    ax.set_ylim(-2, 2)
    fig.tight_layout()
    return fig


# -------------------------
# Loop principal de atualização (roda enquanto sim estiver ativa)
# -------------------------
while True:
    sim = st.session_state.get('sim', None)
    # se não estiver rodando, limpa placeholders e sai do loop
    if sim is None:
        stat_placeholder.info('Simulação parada. Configure e pressione "Iniciar Simulação".')
        deadlock_placeholder.empty()
        vis_placeholder.empty()
        if show_logs:
            # mostra logs mesmo com sim parada (útil para inspeção)
            if st.session_state.logs:
                log_placeholder.code("\n".join(st.session_state.logs[-200:]))
            else:
                log_placeholder.empty()
        else:
            log_placeholder.empty()
        break

    # pega snapshot atual (rápido)
    snap = sim.snapshot()
    prev = st.session_state.last_snapshot
    now = time.time()

    # ---------- detecção de eventos para log (diferenças entre snapshots) ----------
    if prev is not None:
        # chegadas de clientes
        if snap['customer_count'] > prev['customer_count']:
            for cid in range(prev['customer_count'] + 1, snap['customer_count'] + 1):
                append_log(f"Cliente {cid} chegou.")

        # atendimentos
        if snap['served_count'] > prev['served_count']:
            append_log(f"Cliente atendido. (total atendidos: {snap['served_count']})")

        # mudanças de estado dos barbeiros
        for i, (old_s, new_s) in enumerate(zip(prev['barber_states'], snap['barber_states'])):
            if old_s != new_s:
                append_log(f"Barbeiro {i}: {old_s} -> {new_s}")

    # ---------- detecção simples de deadlock ----------
    # atualiza tempo de progresso quando existe avanço no served_count
    if snap['served_count'] > st.session_state.last_served_count:
        st.session_state.last_served_count = snap['served_count']
        st.session_state.last_progress_time = now
        if st.session_state.deadlock_detected:
            st.session_state.deadlock_detected = False
            append_log("Progresso detectado — possível deadlock resolvido.")
    else:
        # sem progresso recente -> avaliamos se é deadlock (apenas quando há clientes esperando)
        time_since_progress = now - st.session_state.last_progress_time
        waiting_len = len(snap['waiting'])
        barbers_serving = any('serving' in s for s in snap['barber_states'])
        if (time_since_progress > float(deadlock_timeout)) and (waiting_len > 0) and (not barbers_serving):
            # marca deadlock se ainda não marcado
            if not st.session_state.deadlock_detected:
                st.session_state.deadlock_detected = True
                # motivo baseado no modo buggy e nos estados
                if enable_solution:
                    reason = ("Apesar de o modo SAFE estar ativado, detectou-se falta de progresso — "
                              "isso pode indicar que a fila está cheia e nenhum barbeiro conseguiu processar clientes.")
                else:
                    reason = (
                        "Modo BUGGY: barbeiros possivelmente em sono sem sinalização correta enquanto há clientes na fila; "
                        "ou ordem inconsistente de locks entre clientes/barbeiros causando bloqueio."
                    )
                append_log(f"DEADLOCK detectado — motivo provável: {reason}")
    # ---------- fim detecção ----------

    # ---------- renderização estatísticas / alertas / visual ----------
    # Estatísticas (coluna direita)
    stat_placeholder.markdown(
        f"**Clientes chegados:** {snap['customer_count']}  \n"
        f"**Clientes atendidos:** {snap['served_count']}  \n"
        f"**Cadeiras:** {snap['num_chairs']}  \n"
        f"**Barbeiros:** {snap['num_barbers']}  \n"
        f"**Modo:** {'SAFE' if enable_solution else 'BUGGY - cuidado'}"
    )

    # Alerta bem perceptível em caso de deadlock
    if st.session_state.deadlock_detected:
        # construir motivo mais detalhado com base nos estados atuais
        barber_summary = ", ".join(f"B{i}:{s}" for i, s in enumerate(snap['barber_states']))
        reason_short = ("Barbeiros não estão atendendo apesar de existirem clientes na fila. "
                        "Isso acontece porque, no modo BUGGY, os barbeiros entram em sono sem serem notificados "
                        "e os clientes podem ficar presos tentando alocar recursos em ordem inconsistente.")
        html = (
            f'<div style="padding:14px;border-radius:8px;background:#b00020;color:white;">'
            f'<strong style="font-size:18px">⚠ DEADLOCK DETECTADO</strong><br>'
            f'<span style="font-size:13px">{reason_short}</span><br>'
            f'<small>Estados barbeiros: {barber_summary}</small><br>'
            f'<small>Detectado em: {_now_ts()}</small>'
            f'</div>'
        )
        deadlock_placeholder.markdown(html, unsafe_allow_html=True)
    else:
        deadlock_placeholder.empty()

    # Visualização (coluna esquerda)
    fig = draw_snapshot(snap)
    vis_placeholder.pyplot(fig)

    # Logs (coluna direita dentro do expander) — atualiza apenas o conteúdo do placeholder
    if show_logs:
        if st.session_state.logs:
            # exibe últimas 200 linhas em monoespaçado (não cria novos componentes por linha)
            log_text = "\n".join(st.session_state.logs[-200:])
            log_placeholder.code(log_text)
        else:
            log_placeholder.info("Sem eventos ainda.")
    else:
        log_placeholder.empty()

    # salva snapshot para próxima iteração
    st.session_state.last_snapshot = snap

    # pausa breve para reduzir uso de CPU e tornar atualização legível
    time.sleep(0.5)
