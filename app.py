# app.py - Streamlit UI for Sleeping Barber Simulation
import streamlit as st
import time, threading
from barber_simulation import BarberSimulation
import matplotlib.pyplot as plt

st.set_page_config(page_title='Sleeping Barber - Visual', layout='wide')

st.title('🪒 Problema do Barbeiro Dorminhoco — Visualização ao vivo')

# Sidebar controls
st.sidebar.header('Configurações da Simulação')
num_barbers = st.sidebar.number_input('Número de barbeiros', min_value=1, max_value=10, value=2, step=1)
num_chairs = st.sidebar.number_input('Número de cadeiras na sala de espera', min_value=0, max_value=20, value=5, step=1)
arrival_rate = st.sidebar.slider('Tempo médio entre chegadas (segundos)', 0.1, 5.0, 1.0, 0.1)
enable_solution = st.sidebar.checkbox('Ativar soluções para evitar deadlock (recomendado)', value=True)
mode = 'SAFE' if enable_solution else 'BUGGY (pode deadlock)'
st.sidebar.markdown(f'**Modo:** {mode}')

col1, col2 = st.columns([2,1])

with col2:
    st.markdown('### Controles')
    if 'sim' not in st.session_state:
        st.session_state.sim = None
    if st.button('Iniciar Simulação'):
        if st.session_state.sim is None:
            sim = BarberSimulation(num_barbers=num_barbers, num_chairs=num_chairs, arrival_rate=arrival_rate, enable_solution=enable_solution)
            sim.start()
            st.session_state.sim = sim
        else:
            st.warning('Simulação já em execução. Pare primeiro para reiniciar com novas configurações.')
    if st.button('Parar Simulação'):
        if st.session_state.sim is not None:
            st.session_state.sim.stop()
            st.session_state.sim = None
    st.markdown('---')
    st.markdown('### Estatísticas')
    stat_placeholder = st.empty()
    st.markdown('### Notas')
    st.write('No modo **BUGGY**, a simulação tenta reproduzir comportamento incorreto (esperas/bloqueios) que pode levar a deadlock. Use com cuidado.')

vis_placeholder = st.empty()

def draw_snapshot(snap):
    fig, ax = plt.subplots(figsize=(6,4))
    ax.set_title('Sala de espera & Barbeiros')
    ax.axis('off')
    # draw waiting chairs
    chairs = snap['num_chairs']
    waiting = snap['waiting']
    barber_states = snap['barber_states']
    # chairs row
    for i in range(chairs):
        x = i
        y = 1
        if i < len(waiting):
            ax.add_patch(plt.Circle((x, y), 0.3))
            ax.text(x, y, str(waiting[i]), va='center', ha='center', color='white')
        else:
            ax.add_patch(plt.Circle((x, y), 0.3, fill=False))
    # barbers row below
    for i in range(len(barber_states)):
        x = i * 2
        y = -1
        state = barber_states[i]
        if 'serving' in state:
            ax.add_patch(plt.Rectangle((x-0.4, y-0.3), 0.8, 0.6))
            ax.text(x, y, f'B{i}\n{state}', va='center', ha='center', color='white')
        else:
            ax.add_patch(plt.Rectangle((x-0.4, y-0.3), 0.8, 0.6, fill=False))
            ax.text(x, y, f'B{i}\n{state}', va='center', ha='center')
    ax.set_xlim(-1, max(chairs, len(barber_states)*2))
    ax.set_ylim(-2, 2)
    return fig

# main loop to update visualization
last_snap = None
while True:
    sim = st.session_state.get('sim', None)
    if sim is None:
        stat_placeholder.info('Simulação parada. Configure e pressione "Iniciar Simulação".')
        vis_placeholder.empty()
        break
    snap = sim.snapshot()
    # update stats
    stat_placeholder.metric("Clientes chegados", snap['customer_count'], delta=None)
    stat_placeholder.metric("Clientes atendidos", snap['served_count'], delta=None)
    stat_placeholder.markdown(f"**Modo:** {'SAFE' if enable_solution else 'BUGGY - cuidado'}")  
    stat_placeholder.markdown(f"**Cadeiras:** {snap['num_chairs']}")
    fig = draw_snapshot(snap)
    vis_placeholder.pyplot(fig)
    time.sleep(0.5)
