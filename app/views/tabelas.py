import html

import streamlit as st
import pandas as pd


RODADAS = [
    {
        "titulo": "Primeira Rodada",
        "data_inicio": "2026-06-11",
        "data_fim": "2026-06-17",
    },
    {
        "titulo": "Segunda Rodada",
        "data_inicio": "2026-06-18",
        "data_fim": "2026-06-23",
    },
    {
        "titulo": "Terceira Rodada",
        "data_inicio": "2026-06-24",
        "data_fim": "2026-06-27",
    },
    {
        "titulo": "Playoffs",
        "data_inicio": "2026-06-28",
        "data_fim": "2026-07-19",
    },
]

RODADA_SELECT_KEY = "tabelas_rodada_selecionada"
RODADA_LAST_ENABLED_KEY = "tabelas_ultima_rodada_habilitada"
RODADA_BLOCKED_MESSAGE_KEY = "tabelas_rodada_bloqueada_msg"


def hoje_brt() -> pd.Timestamp:
    return pd.Timestamp.now(tz="America/Sao_Paulo").normalize().tz_localize(None)


def is_rodada_disponivel(rodada: dict, hoje: pd.Timestamp) -> bool:
    return hoje >= pd.to_datetime(rodada["data_inicio"])


def format_rodada_label(rodada: dict, hoje: pd.Timestamp) -> str:
    inicio = pd.to_datetime(rodada["data_inicio"])
    fim = pd.to_datetime(rodada["data_fim"])
    label = f"{rodada['titulo']} ({inicio.strftime('%d/%m')} a {fim.strftime('%d/%m')})"
    if not is_rodada_disponivel(rodada, hoje):
        label += " - indisponível"
    return label


def get_default_rodada_index(rodadas: list[dict], hoje: pd.Timestamp) -> int:
    default_index = 0
    for index, rodada in enumerate(rodadas):
        if is_rodada_disponivel(rodada, hoje):
            default_index = index
    return default_index


def get_rodada_bloqueada_message(rodada: dict) -> str:
    rodada_inicio = pd.to_datetime(rodada["data_inicio"])
    return (
        f"A opção '{rodada['titulo']}' estará disponível a partir de "
        f"{rodada_inicio.strftime('%d/%m/%Y')}, após o primeiro jogo da fase."
    )


def render_rodada_bloqueada_message(message: str) -> None:
    st.markdown(
        f"""
        <div style="
            background:#fef3c7;
            color:#78350f;
            border:1px solid #f59e0b;
            border-left:6px solid #d97706;
            border-radius:8px;
            padding:12px 16px;
            font-weight:700;
            line-height:1.45;
        ">
            {html.escape(message)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(df_historico: pd.DataFrame) -> None:
    st.markdown("<div class='section-title'>Rankings por Rodada</div>", unsafe_allow_html=True)

    if df_historico.empty:
        st.info("Nenhum dado cadastrado. Atualize o bolão no Painel Admin.")
        return

    df_rounds = df_historico.copy()
    df_rounds["data_hora"] = pd.to_datetime(df_rounds["data_hora"], errors="coerce")
    df_rounds = df_rounds.sort_values(by=["data_hora", "coleta_id"])

    def render_ranking_table(titulo: str, data_inicio: str, data_fim: str):
        inicio = pd.to_datetime(data_inicio)
        fim = pd.to_datetime(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_faixa = df_rounds[(df_rounds["data_hora"] >= inicio) & (df_rounds["data_hora"] <= fim)].copy()

        if df_faixa.empty:
            st.info(f"Nenhum ranking registrado para {titulo} ({data_inicio} a {data_fim}).")
            return

        idx_ultima = df_faixa.sort_values(["participante", "arroba", "data_hora"]).groupby(["participante", "arroba"])["data_hora"].idxmax()
        df_ultima = df_faixa.loc[idx_ultima, ["participante", "arroba", "posicao", "pontos"]].copy()
        df_ultima = df_ultima.rename(columns={"posicao": "posicao_ultima", "pontos": "pontos_ultima"})

        df_antes = df_rounds[df_rounds["data_hora"] < inicio].copy()
        if not df_antes.empty:
            idx_antes = df_antes.sort_values(["participante", "arroba", "data_hora"]).groupby(["participante", "arroba"])["data_hora"].idxmax()
            df_antes = df_antes.loc[idx_antes, ["participante", "arroba", "pontos"]].copy()
            df_antes = df_antes.rename(columns={"pontos": "pontos_antes"})
        else:
            df_antes = pd.DataFrame(columns=["participante", "arroba", "pontos_antes"])

        df_ranking = df_ultima.merge(df_antes, on=["participante", "arroba"], how="left")
        df_ranking["pontos_antes"] = df_ranking["pontos_antes"].fillna(0)
        df_ranking["Pontuação"] = (df_ranking["pontos_ultima"] - df_ranking["pontos_antes"]).clip(lower=0)
        df_ranking = df_ranking.sort_values(
            by=["Pontuação", "posicao_ultima", "participante", "arroba"],
            ascending=[False, True, True, True],
        ).reset_index(drop=True)
        df_ranking.insert(0, "Posição", range(1, len(df_ranking) + 1))
        df_ranking = df_ranking[["Posição", "participante", "arroba", "Pontuação"]].rename(columns={
            "participante": "Participante",
            "arroba": "Usuário (@)"
        })

        st.markdown(
            f"<div style='font-weight:700; margin-bottom:8px;'>{titulo} <span style='font-weight:400; color:#64748b; font-size:0.95rem;'>{data_inicio} a {data_fim}</span></div>",
            unsafe_allow_html=True,
        )
        st.dataframe(df_ranking, use_container_width=True, hide_index=True, height=520)

    rodadas = RODADAS
    hoje = hoje_brt()
    labels = [format_rodada_label(rodada, hoje) for rodada in rodadas]
    label_to_rodada = dict(zip(labels, rodadas))
    default_index = get_default_rodada_index(rodadas, hoje)
    default_label = labels[default_index]
    enabled_labels = [
        label
        for label, rodada in zip(labels, rodadas)
        if is_rodada_disponivel(rodada, hoje)
    ]

    if st.session_state.get(RODADA_SELECT_KEY) not in labels:
        st.session_state[RODADA_SELECT_KEY] = default_label
    if enabled_labels and st.session_state.get(RODADA_LAST_ENABLED_KEY) not in enabled_labels:
        st.session_state[RODADA_LAST_ENABLED_KEY] = default_label

    def validate_rodada_selection() -> None:
        selected_label = st.session_state.get(RODADA_SELECT_KEY)
        selected_rodada = label_to_rodada.get(selected_label)
        if selected_rodada is None:
            st.session_state[RODADA_SELECT_KEY] = default_label
            return

        if is_rodada_disponivel(selected_rodada, hoje):
            st.session_state[RODADA_LAST_ENABLED_KEY] = selected_label
            return

        st.session_state[RODADA_BLOCKED_MESSAGE_KEY] = get_rodada_bloqueada_message(selected_rodada)
        fallback_label = st.session_state.get(RODADA_LAST_ENABLED_KEY, default_label)
        if fallback_label in enabled_labels:
            st.session_state[RODADA_SELECT_KEY] = fallback_label

    blocked_message = st.session_state.pop(RODADA_BLOCKED_MESSAGE_KEY, None)
    if blocked_message:
        render_rodada_bloqueada_message(blocked_message)

    selecionado = st.selectbox(
        "Selecione a rodada",
        labels,
        index=default_index,
        key=RODADA_SELECT_KEY,
        on_change=validate_rodada_selection,
    )
    rodada_escolhida = label_to_rodada[selecionado]

    if not is_rodada_disponivel(rodada_escolhida, hoje):
        render_rodada_bloqueada_message(get_rodada_bloqueada_message(rodada_escolhida))
        return

    st.session_state[RODADA_LAST_ENABLED_KEY] = selecionado

    render_ranking_table(
        rodada_escolhida["titulo"],
        rodada_escolhida["data_inicio"],
        rodada_escolhida["data_fim"],
    )
