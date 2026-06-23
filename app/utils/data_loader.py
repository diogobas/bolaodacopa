import json
import pandas as pd
import streamlit as st
from config import settings


def fetch_live_matches_from_api() -> list[dict]:
    if not settings.has_dacopa_config():
        return []

    try:
        from collectors import scraper, session_manager
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            context = session_manager.get_authenticated_context(p)
            page = context.new_page()
            api_data = scraper.fetch_leaderboard_api(page)
            context.close()

        live_matches = api_data.get("liveMatches", []) or []
        if live_matches:
            settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            with open(settings.LIVE_MATCHES_FILE, "w", encoding="utf-8") as f:
                json.dump(live_matches, f, ensure_ascii=False, indent=2)

        return live_matches

    except Exception as e:
        st.error(f"Erro ao buscar partidas ao vivo diretamente da API: {e}")
        return []


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

    live_matches = []

    if settings.PALPITES_EXCEL.exists():
        try:
            palpites = pd.read_excel(settings.PALPITES_EXCEL)
        except Exception as e:
            st.error(f"Erro ao ler palpites.xlsx: {e}")

    if settings.LIVE_MATCHES_FILE.exists():
        try:
            with open(settings.LIVE_MATCHES_FILE, "r", encoding="utf-8") as f:
                live_matches = json.load(f)
        except Exception as e:
            st.error(f"Erro ao ler live_matches.json: {e}")
    elif settings.has_dacopa_config():
        live_matches = fetch_live_matches_from_api()

    return membros, historico, palpites, live_matches
