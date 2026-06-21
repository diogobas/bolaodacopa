import pandas as pd
import streamlit as st
from config import settings


@st.cache_data(ttl=5)
def load_data():
    membros = pd.DataFrame(columns=["nome", "arroba"])
    historico = pd.DataFrame(columns=[
        "data_hora", "coleta_id", "participante", "arroba", "posicao", "pontos",
        "placar_exato", "gols_vencedor", "saldo_gols", "gols_perdedor", "vencedor_certo", "sem_pontos"
    ])
    palpites = pd.DataFrame(columns=[
        "coleta_id", "partida_id", "mandante", "visitante",
        "placar_real_m", "placar_real_v",
        "participante", "arroba",
        "palpite_m", "palpite_v", "categoria"
    ])

    if settings.MEMBROS_EXCEL.exists():
        try:
            membros = pd.read_excel(settings.MEMBROS_EXCEL)
        except Exception as e:
            st.error(f"Erro ao ler membros.xlsx: {e}")

    if settings.HISTORICO_EXCEL.exists():
        try:
            historico = pd.read_excel(settings.HISTORICO_EXCEL)
            if not historico.empty:
                historico["data_hora"] = pd.to_datetime(historico["data_hora"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                for col in ["placar_exato", "gols_vencedor", "saldo_gols", "gols_perdedor", "vencedor_certo", "sem_pontos"]:
                    if col not in historico.columns:
                        historico[col] = 0
                    else:
                        historico[col] = historico[col].fillna(0).astype(int)
        except Exception as e:
            st.error(f"Erro ao ler historico.xlsx: {e}")

    if settings.PALPITES_EXCEL.exists():
        try:
            palpites = pd.read_excel(settings.PALPITES_EXCEL)
        except Exception as e:
            st.error(f"Erro ao ler palpites.xlsx: {e}")

    return membros, historico, palpites
