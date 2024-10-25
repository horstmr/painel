import streamlit as st
import pandas as pd
from datetime import datetime
import os
import pygame
import time
import numpy as np

pygame.mixer.init()
CSV_FILE = 'agenda.csv'

def carregar_campainha():
    return "bell_sound.mp3"  # Caminho para o som da campainha

pessoas_chamadas = []

def tocar_campainha_e_dizer_nome(nome, mesa_numero):
    bell_audio = carregar_campainha()
    pygame.mixer.music.load(bell_audio)
    pygame.mixer.music.play()

def format_name(name):
    name_parts = name.split()
    if len(name_parts) > 1:
        return f"{name_parts[0].capitalize()} {name_parts[1][0].upper()}."
    else:
        return name_parts[0].capitalize()
    
def monitorar_agenda_para_novas_chamadas():
    placeholder = st.empty()

    if 'page_loaded' not in st.session_state:
        st.session_state['page_loaded'] = False

    if not st.session_state['page_loaded']:
        with placeholder.container():
            st.write("Carregando a página...")  
        st.session_state['page_loaded'] = True
        st.rerun()  # Rerun após o carregamento

    while True:
        try:
            agenda_df = pd.read_csv(CSV_FILE)

            # Ensure 'Horário de Chegada' exists
            if 'Horário de Chegada' not in agenda_df.columns:
                agenda_df['Horário de Chegada'] = None  # or pd.NaT for datetime
            if 'Mesa' not in agenda_df.columns:
                agenda_df['Mesa'] = None  # or pd.NaT for datetime
            if 'Status' not in agenda_df.columns:
                agenda_df['Status'] = None  # or pd.NaT for datetime

            # Convert 'Horário de Chegada' to datetime format, ignore errors
            agenda_df['Horário de Chegada'] = pd.to_datetime(agenda_df['Horário de Chegada'], errors='coerce', dayfirst=True)

        except Exception as e:
            st.write(f'Sem agenda disponível. Erro: {e}')
            continue

        with placeholder.container():
            try:
                # Sort by 'Horário de Chegada' if available
                sorted_data = agenda_df.sort_values(by='Horário de Chegada').reset_index(drop=True)
            except KeyError:
                st.write("Erro: 'Horário de Chegada' não disponível.")
                continue

            st.markdown(
                """
                <style>
                .full-width {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 100%;
                    margin-top: 0px; /* Reduz espaço acima do primeiro nome */
                }
                .name-column {
                    flex: 1;
                    text-align: center;
                    padding-right: 20px; /* Espaçamento à direita da coluna de nome */
                }
                .mesa-column {
                    flex: 0.5;
                    text-align: right;
                    padding-left: 20px; /* Espaçamento à esquerda da coluna da mesa */
                }
                .big-text {
                    font-size: 250px; /* Aumentar o tamanho da fonte */
                    font-weight: bold;
                    margin-bottom: 0px; /* Reduz o espaço entre o título e o nome grande */
                }
                .mesa-label {
                    font-size: 150px; /* Aumentar o tamanho do texto "Mesa" */
                    font-weight: bold;
                    margin: 0px;
                }
                .mesa-number {
                    font-size: 250px; /* Aumentar o tamanho do número da mesa */
                    font-weight: bold;
                    margin: 0px;
                }
                .small-text {
                    font-size: 40px; /* Aumentar o tamanho do texto para os últimos chamados */
                    text-align: left;
                    margin-bottom: 0px; /* Reduz o espaço entre o título e o primeiro nome menor */
                }
                .stacked-text {
                    font-size: 100px; /* Aumentar o tamanho dos nomes empilhados */
                    text-align: left;
                    padding-right: 20px; /* Espaçamento à direita dos nomes na parte inferior */
                    margin-bottom: 0px; /* Remove o espaço entre os nomes empilhados */
                    line-height: 0.8; /* Reduz o espaço vertical entre as linhas de texto */
                }
                .stacked-table-number {
                    font-size: 80px; /* Aumentar o tamanho dos números de mesa empilhados */
                    text-align: left;
                    padding-left: 20px; /* Espaçamento à esquerda dos números de mesa na parte inferior */
                    margin-bottom: 10px;
                    font-weight: bold;
                }
                </style>
                """, unsafe_allow_html=True
            )

            if pessoas_chamadas:
                nome_grande, mesa_grande = pessoas_chamadas[0]
                st.image('logo.png', width=500)
                st.markdown(f"""
                <div class='full-width'>
                    <div class='name-column'>
                        <div class='big-text'>{nome_grande}</div>
                    </div>
                    <div class='mesa-column'>
                        <div class='mesa-label'>Mesa</div>
                        <div class='mesa-number'>{mesa_grande}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if len(pessoas_chamadas) > 1:
                st.markdown("<div class='small-text'>Últimos chamados:</div>", unsafe_allow_html=True)
                for i in range(1, min(4, len(pessoas_chamadas))):
                    nome = pessoas_chamadas[i][0]
                    mesa = pessoas_chamadas[i][1]
                    st.markdown(f"""
                    <div class='full-width'>
                        <div class='stacked-text'>{nome}</div>
                        <div class='stacked-table-number'>Mesa {mesa}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Ensure status is fetched only if 'Nome' exists
                if nome_grande in agenda_df['Nome'].values:
                    status_pessoa = agenda_df.loc[agenda_df['Nome'] == nome_grande, 'Status'].values[0]
                    if status_pessoa != "Em atendimento":
                        tocar_campainha_e_dizer_nome(nome_grande, mesa_grande)

            # Fetch new people to call
            pessoas_para_chamar = agenda_df[(agenda_df['Status'] == "Aguardando atendimento") & (agenda_df['Mesa'].notnull())]
            novas_chamadas = []
            for index, pessoa in pessoas_para_chamar.iterrows():
                nome = pessoa['Nome']
                mesa = pessoa['Mesa']
                if (nome, mesa) not in pessoas_chamadas:
                    pessoas_chamadas.insert(0, (nome, mesa))  
                    if len(pessoas_chamadas) > 4:
                        pessoas_chamadas.pop()
                    novas_chamadas.append((nome, mesa))
                    break

        time.sleep(10)

def carregar_agenda():
    try:
        if os.path.exists(CSV_FILE):
            agenda_df = pd.read_csv('agenda.csv', encoding='utf')
            if 'Prioritária' not in agenda_df.columns:
                agenda_df['Prioritária'] = False

            if 'Status' not in agenda_df.columns:
                agenda_df['Status'] = "Aguardando chegada"
            if 'Horário de Chegada' not in agenda_df.columns:
                agenda_df['Horário de Chegada'] = None
            if 'Mesa' not in agenda_df.columns:
                agenda_df['Mesa'] = None
            if 'Posição na fila' not in agenda_df.columns:
                agenda_df['Posição na fila'] = None
            if 'Atendimento iniciado em' not in agenda_df.columns:
                agenda_df['Atendimento iniciado em'] = None  # New column for when service starts
            if 'Atendimento encerrado em' not in agenda_df.columns:
                agenda_df['Atendimento encerrado em'] = None  

            agenda_df['Mesa'] = pd.to_numeric(agenda_df['Mesa'], errors='coerce').fillna(0).astype('Int64')
            agenda_df['Nome'] = agenda_df['Nome'].apply(format_name)
            agenda_df['Atendimento iniciado em'] = agenda_df['Atendimento iniciado em'].astype(str)
            agenda_df['Data'] = agenda_df['Data'].astype(str)
            return agenda_df

        else:
            agenda_df = pd.DataFrame({
                "Nome": ["José", "João", "Ana", "Pedro", "José", "Luiza"],
                "Data": ["17/09/2024", "17/09/2024", "17/09/2024", "17/09/2024", "17/09/2024", "17/09/2024"],
                "Horário": ["08:10:00", "08:30:00", "09:00:00", "09:30:00", "10:00:00", "10:30:00"],
                "Status": ["Aguardando chegada", "Aguardando chegada", "Aguardando chegada", "Aguardando chegada", "Aguardando chegada", "Aguardando chegada"],
                "Horário de Chegada": [None, None, None, None, None, None],
                "Posição na fila": [None, None, None, None, None, None],
                "Mesa": [None, None, None, None, None, None],
                "Atendimento iniciado em": [None, None, None, None, None, None],
                "Prioritária": [False, False, False, False, False, False]
            })
            agenda_df.to_csv(CSV_FILE, index=False)
        return agenda_df
            
    except Exception as e:
        st.error(f"Erro ao carregar a agenda: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def salvar_agenda(df):
    try:
        df_chegada_confirmada = df[df['Status'] == "Chegada confirmada"].sort_values(
            by=['Prioritária', 'Horário de Chegada'], 
            ascending=[False, True]
        ).reset_index(drop=True)
        df.loc[df['Status'] == "Chegada confirmada", 'Posição na fila'] = df_chegada_confirmada.index + 1
        df.to_csv(CSV_FILE, index=False)
        st.success("Agenda salva com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar a agenda: {e}")

def iniciar_atendimento(nome):
    agenda_df = carregar_agenda()
    if nome in agenda_df['Nome'].values:
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")  # Ensure the format 'dd/mm/yyyy hh:mm'
        agenda_df.loc[agenda_df['Nome'] == nome, 'Atendimento iniciado em'] = current_time
        agenda_df.loc[agenda_df['Nome'] == nome, 'Status'] = "Em atendimento"
        salvar_agenda(agenda_df)
        st.success(f"Atendimento iniciado para {nome.capitalize()} às {current_time}")
        st.rerun()
    else:
        st.error(f"Nome {nome.capitalize()} não encontrado na agenda.")
        
def chamar_proxima_pessoa(mesa_numero):
    agenda_df = carregar_agenda()
    pessoas_para_chamar = agenda_df[agenda_df['Status'] == "Chegada confirmada"]
    pessoas_para_chamar = pessoas_para_chamar.sort_values(by=["Horário Agendado", "Horário de Chegada"])
    if not pessoas_para_chamar.empty:
        pessoa_para_chamar = pessoas_para_chamar.iloc[0]
        agenda_df.loc[agenda_df['Nome'] == pessoa_para_chamar['Nome'], 'Status'] = "Aguardando atendimento"
        agenda_df.loc[agenda_df['Nome'] == pessoa_para_chamar['Nome'], 'Mesa'] = mesa_numero
        salvar_agenda(agenda_df)
        return pessoa_para_chamar['Nome'], mesa_numero
    return None, None

st.set_page_config(page_title="Painel de Atendimento", layout='wide')
with st.sidebar:
    funcao_selecionada = st.selectbox("Selecione o tipo de acesso", ["Recepcionista", "Atendente", "Painel de Chamada"])

agenda_df = carregar_agenda()

if funcao_selecionada in ["Recepcionista", "Atendente"]:
    st.markdown("## Agenda do Dia")
    if 'Horário de Chegada' not in agenda_df.columns:
        agenda_df['Horário de Chegada'] = pd.Series(dtype='object')
    else:
        agenda_df['Horário de Chegada'] = agenda_df['Horário de Chegada'].astype('str')
    data_selecionada = st.selectbox("Selecione a Data", agenda_df['Data'].unique())
    agenda_filtrada = agenda_df[agenda_df['Data'] == data_selecionada]
    st.dataframe(agenda_filtrada, use_container_width=True)

if funcao_selecionada == "Recepcionista":
    st.markdown("### Recepcionista")
    col1, col2 = st.columns([3, 1])
    with col1:
        waiting_people = agenda_df[agenda_df['Status'] == "Aguardando chegada"].sort_values(by='Horário')
        if not waiting_people.empty:
            nome_selecionado = st.selectbox(
                "Selecione a pessoa para confirmar chegada",
                waiting_people.apply(lambda row: f"{row['Nome']} - {row['Horário']}", axis=1)
            )
        else:
            nome_selecionado = None
    with col2:
        is_prioritaria = st.checkbox("Prioritária", value=False)
        if st.button("Confirmar chegada") and nome_selecionado:
            selected_name = nome_selecionado.split(" - ")[0]  # Obter nome da pessoa
            agenda_df.loc[agenda_df['Nome'] == selected_name, 'Status'] = "Chegada confirmada"
            agenda_df.loc[agenda_df['Nome'] == selected_name, 'Horário de Chegada'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            agenda_df.loc[agenda_df['Nome'] == selected_name, 'Prioritária'] = is_prioritaria
            salvar_agenda(agenda_df)
            st.success(f"Chegada de {selected_name} confirmada.")
            st.rerun()

    confirmed_people = agenda_df[agenda_df['Status'] == "Chegada confirmada"]
    with st.expander("Desconfirmar chegada"):
        if not confirmed_people.empty:
            nome_desconfirmado = st.selectbox(
                "Selecione a pessoa para desconfirmar chegada",
                confirmed_people.apply(lambda row: f"{row['Nome']} - {row['Horário']}", axis=1)
            )
            if st.button("Desconfirmar chegada") and nome_desconfirmado:
                selected_name = nome_desconfirmado.split(" - ")[0]
                agenda_df.loc[agenda_df['Nome'] == selected_name, 'Status'] = "Aguardando chegada"
                agenda_df.loc[agenda_df['Nome'] == selected_name, 'Horário de Chegada'] = None
                agenda_df.loc[agenda_df['Nome'] == selected_name, 'Posição na fila'] = None
                agenda_df.loc[agenda_df['Nome'] == selected_name, 'Atendimento iniciado em'] = None
                agenda_df.loc[agenda_df['Nome'] == selected_name, 'Prioritária'] = False
                salvar_agenda(agenda_df)
    # Adding "Encaixes" (extra appointments)
    with st.expander("Adicionar Encaixe"):
        nome_encaixe = st.text_input("Nome")
        if st.button("Adicionar Encaixe") and nome_encaixe:
            new_row = pd.DataFrame({
                'Nome': [nome_encaixe],
                'Data': [datetime.now().strftime("%d/%m/%Y")],
                'Horário': [datetime.now().strftime("%H:%M:%S")],
                'Status': ['Chegada confirmada'],
                'Horário de Chegada': [datetime.now().strftime("%d/%m/%Y %H:%M:%S")],
                'Mesa': [None]
            })
            agenda_df = pd.concat([agenda_df, new_row], ignore_index=True)  # Use pd.concat instead of append
            salvar_agenda(agenda_df)
            st.success(f"Encaixe de {nome_encaixe} adicionado.")
            
elif funcao_selecionada == "Atendente":
    
    st.markdown("### Atendente")
    with st.sidebar:
        atendente_selecionado = st.selectbox("Selecione o atendente", ["Atendente 1", "Atendente 2", "Atendente 3", "Atendente 4", "Atendente 5", "Atendente 6"])
    mesa_numero = int(atendente_selecionado.split()[-1])
    atendimentos_iniciados = agenda_df[(agenda_df['Status'] == "Atendimento encerrado") & (agenda_df['Mesa'] == mesa_numero)]
    total_atendimentos = len(atendimentos_iniciados)
    st.markdown(f"**Total de atendimentos hoje: {total_atendimentos}**")

    atendente_key = f"atendimento_iniciado_{atendente_selecionado}"
    pessoas_chamadas_key = f"pessoas_chamadas_{atendente_selecionado}"
    
    if atendente_key not in st.session_state:
        st.session_state[atendente_key] = None
    
    
    if pessoas_chamadas_key not in st.session_state:
        st.session_state[pessoas_chamadas_key] = []

    if (
        st.session_state[atendente_key] is None or 
        agenda_df.loc[agenda_df['Nome'] == st.session_state[atendente_key], 'Status'].values[0] in ["Atendimento encerrado", "Chegada confirmada"]
    ):
        if st.button("Chamar próxima pessoa"):
            pessoas_prioritarias = agenda_df[
                (agenda_df['Status'] == "Chegada confirmada") & 
                (agenda_df['Prioritária'] == True)
            ].sort_values(by='Horário de Chegada')

            pessoas_nao_prioritarias = agenda_df[
                (agenda_df['Status'] == "Chegada confirmada") & 
                (agenda_df['Prioritária'] == False)
            ].sort_values(by='Horário de Chegada')

            if not pessoas_prioritarias.empty:
                proxima_pessoa = pessoas_prioritarias.iloc[0]
            elif not pessoas_nao_prioritarias.empty:
                proxima_pessoa = pessoas_nao_prioritarias.iloc[0]
            else:
                proxima_pessoa = None

            if proxima_pessoa is not None:
                nome_chamado = proxima_pessoa['Nome']
                agenda_df.loc[agenda_df['Nome'] == nome_chamado, 'Status'] = "Aguardando atendimento"
                agenda_df.loc[agenda_df['Nome'] == nome_chamado, 'Mesa'] = mesa_numero
                salvar_agenda(agenda_df)
                st.session_state[atendente_key] = nome_chamado
                st.session_state[pessoas_chamadas_key].insert(0, (nome_chamado, mesa_numero))
                if len(st.session_state[pessoas_chamadas_key]) > 4:
                    st.session_state[pessoas_chamadas_key].pop()  # Keep only the last 4 entries
                st.success(f"{nome_chamado} foi chamado para a mesa {mesa_numero}.")
                st.rerun()
            else:
                st.warning("Nenhuma pessoa disponível para chamar.")
    else:
        st.warning("Finalize o atendimento atual antes de chamar uma nova pessoa.")

    if len(st.session_state[pessoas_chamadas_key]) > 0:
        ultimas_pessoas_chamadas = st.session_state[pessoas_chamadas_key][:4]
        st.markdown("### Últimas 4 pessoas chamadas:")
        for i, pessoa in enumerate(ultimas_pessoas_chamadas):
            st.markdown(f"{i+1}. {pessoa[0]} - Mesa {pessoa[1]}")

        ultima_pessoa = st.session_state[pessoas_chamadas_key][0][0]
        mesa_ultima_pessoa = st.session_state[pessoas_chamadas_key][0][1]

        if mesa_numero == mesa_ultima_pessoa:
            st.markdown(f"### Última pessoa chamada: **{ultima_pessoa}**")
            if st.button(f"Cancelar chamada de {ultima_pessoa}"):
                agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Status'] = "Chegada confirmada"
                agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Mesa'] = None
                agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Atendimento iniciado em'] = None
                agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Atendimento encerrado em'] = None
                salvar_agenda(agenda_df)
                st.session_state[pessoas_chamadas_key].pop(0)  # Remove from the list
                st.session_state[atendente_key] = None
                st.success(f"Chamada de {ultima_pessoa} foi cancelada.")
                st.rerun()

            if agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Status'].values[0] == "Aguardando atendimento":
                if st.button(f"Iniciar atendimento de {ultima_pessoa}"):
                    agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Status'] = "Em atendimento"
                    agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Atendimento iniciado em'] = pd.Timestamp.now()
                    salvar_agenda(agenda_df)
                    st.session_state[atendente_key] = ultima_pessoa
                    st.success(f"Atendimento de {ultima_pessoa} foi iniciado.")
                    st.rerun()

            if agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Status'].values[0] == "Em atendimento":
                if st.button(f"Encerrar atendimento de {ultima_pessoa}"):
                    agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Status'] = "Atendimento encerrado"
                    agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Posição na fila'] = 0
                    agenda_df.loc[agenda_df['Nome'] == ultima_pessoa, 'Atendimento encerrado em'] = pd.Timestamp.now()
                    salvar_agenda(agenda_df)
                    st.session_state[atendente_key] = None
                    st.success(f"Atendimento de {ultima_pessoa} foi encerrado.")
                    st.rerun()

if funcao_selecionada == "Painel de Chamada":
    monitorar_agenda_para_novas_chamadas()