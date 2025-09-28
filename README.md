# Visualização do Problema do Barbeiro Dorminhoco 💈

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Streamlit-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Uma aplicação interativa desenvolvida com Streamlit para visualizar e entender o clássico problema de concorrência e sincronização: **O Barbeiro Dorminhoco**.

Este projeto permite simular uma barbearia com múltiplos barbeiros e cadeiras de espera, demonstrando em tempo real como a ausência de mecanismos de sincronização corretos pode levar a deadlocks.

## 🚀 Experimente Online!

**→ [Clique aqui para usar a versão web da aplicação](https://distributedsystems-sleepingbarber-project.streamlit.app/)**

Não precisa instalar nada! Use diretamente no seu navegador.

---

### Pré-visualização

![Pré-visualização da interface da simulação, mostrando as cadeiras de espera e os barbeiros em seus estados.](https://i.imgur.com/hV4oIdP.png)

---

## 🎯 Sobre o Problema

O "Problema do Barbeiro Dorminhoco" é um cenário canônico em ciência da computação usado para ilustrar questões de sincronização entre múltiplos processos ou threads. A simulação segue estas regras:

- Se não há clientes, o barbeiro dorme.
- Quando um cliente chega, ele deve acordar o barbeiro.
- Se o barbeiro estiver ocupado, os clientes que chegam sentam-se em uma cadeira de espera.
- Se todas as cadeiras estiverem ocupadas, o cliente vai embora.
- Quando o barbeiro termina um corte, ele verifica se há clientes esperando.

O desafio é gerenciar essas interações sem que ocorram condições de corrida (por exemplo, um cliente chegar e o barbeiro não "perceber", dormindo para sempre) ou deadlocks.

---

## ✨ Funcionalidades

- **Visualização em Tempo Real**: Acompanhe o estado de cada barbeiro (ocioso, atendendo) e a ocupação das cadeiras de espera.
- **Controles Interativos**: Altere o número de barbeiros, o número de cadeiras e a taxa de chegada de clientes para ver como a simulação se comporta sob diferentes cargas.
- **Modo SAFE (Solução Ativa)**: Executa a simulação com uma implementação correta usando semáforos, prevenindo deadlocks e garantindo que todos os clientes sejam atendidos.
- **Modo BUGGY (Propenso a Deadlock)**: Desativa a solução de sincronização para demonstrar como uma implementação ingênua pode falhar, resultando em barbeiros dormindo enquanto clientes esperam.
- **Detecção de Deadlock**: Um alerta visual é exibido na interface caso a simulação entre em um estado de deadlock no modo BUGGY.
- **Log de Eventos**: Um painel de logs detalha cada ação, como a chegada de um cliente, o início de um atendimento ou uma desistência.

---

## 🎓 Contexto Acadêmico

Este projeto foi desenvolvido para atender aos requisitos práticos de uma atividade sobre problemas clássicos de concorrência em sistemas operacionais. Ele aborda especificamente as etapas de **Implementação** e **Explicação do Código** do enunciado proposto.

#### Etapa 2: Implementação

O repositório contém uma implementação funcional e interativa do problema dos **Barbeiros Dorminhocos** utilizando Python. A simulação demonstra a concorrência através do módulo `threading`, onde cada barbeiro e o fluxo de chegada de clientes são representados por threads independentes.

O código permite demonstrar claramente:
- **A ocorrência de deadlock**: Através do **Modo BUGGY**, que intencionalmente omite mecanismos de sincronização adequados, levando a um cenário onde barbeiros dormem com clientes na fila.
- **A solução implementada**: Através do **Modo SAFE**, que utiliza semáforos (`threading.Semaphore`) para garantir a sincronização correta entre as threads, evitando a "condição de corrida" e o deadlock.

#### Etapa 3: Explicação do Código

A estrutura do projeto foi pensada para ser didática:

- **`barber_simulation.py`**: Contém a lógica central da concorrência.
    - **Implementação da Concorrência**: Utiliza a classe `threading.Thread` para simular os barbeiros e a chegada de clientes de forma paralela.
    - **Resolução do Deadlock**: No **Modo SAFE**, um `threading.Semaphore` é usado como um sinalizador. O cliente, ao chegar, "acorda" o barbeiro (`semaphore.release()`), e o barbeiro, quando ocioso, "dorme" esperando por este sinal (`semaphore.acquire()`), resolvendo o problema do "despertar perdido".
- **`app.py`**: Responsável pela interface visual com Streamlit. Ele consome os dados da simulação em tempo real e os exibe de forma gráfica, facilitando a compreensão do que está acontecendo internamente.

---

## 🛠️ Tecnologias Utilizadas

- **Python**: Linguagem principal da lógica da simulação.
- **Módulo `threading`**: Para criar e gerenciar os barbeiros e a chegada de clientes como threads concorrentes.
- **Streamlit**: Para construir a interface web interativa de forma rápida.
- **Matplotlib**: Para renderizar a visualização da barbearia e das cadeiras.

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.7 ou superior
- Pip (gerenciador de pacotes)

### 1. Clone o Repositório

```bash
git clone https://github.com/LuanVitorCD/SE_SleepingBarberImplementation.git
cd SE_SleepingBarberImplementation
```

### 2. Crie um ambiente virtual e instale as dependências:

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate    # Windows
```

### 3. Instale dependências:
```bash
pip install -r requirements.txt
```

### 4. Rode o app:
```bash
streamlit run app.py
```

---

## 📄 Licença

Este projeto está sob a licença MIT.
