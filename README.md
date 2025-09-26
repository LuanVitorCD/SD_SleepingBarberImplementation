# Sleeping Barber - Streamlit Visualization

Projeto educativo que demonstra o problema do "Barbeiro Dorminhoco" com visualização ao vivo.
Permite configurar número de barbeiros, cadeiras de espera, taxa de chegada de clientes,
e ativar/desativar uma solução para evitar deadlocks (padrão: ativado).

Como executar:
1. Crie um ambiente virtual e instale as dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate    # Windows
   ```
2. Instale dependências:
   pip install -r requirements.txt
3. Rode o app:
   streamlit run app.py

Arquivos:
- app.py: aplicação Streamlit principal.
- barber_simulation.py: lógica da simulação (threads).
- requirements.txt: dependências.
- LICENSE: MIT.
