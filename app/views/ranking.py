import streamlit as st
import pandas as pd


def render(df_historico: pd.DataFrame) -> None:
    st.markdown("<div class='section-title'>Classificação Geral da Copa</div>", unsafe_allow_html=True)

    if df_historico.empty:
        st.info("Nenhum dado cadastrado. Atualize o bolão no Painel Admin.")
        return

    ultimo_coleta_id = df_historico["coleta_id"].iloc[-1]
    df_ranking = df_historico[df_historico["coleta_id"] == ultimo_coleta_id].copy()
    df_ranking = df_ranking.sort_values(by="posicao")

    df_exibicao = df_ranking[[
        "posicao", "participante", "arroba", "pontos",
        "placar_exato", "gols_vencedor", "saldo_gols",
        "gols_perdedor", "vencedor_certo", "sem_pontos"
    ]].rename(columns={
        "posicao": "Posição",
        "participante": "Participante",
        "arroba": "Usuário (@)",
        "pontos": "Pontuação",
        "placar_exato": "🎯 Placar Exato (25 pts)",
        "gols_vencedor": "⚽ Gols Vencedor (18 pts)",
        "saldo_gols": "⚖️ Saldo Gols (15 pts)",
        "gols_perdedor": "📉 Gols Perdedor (12 pts)",
        "vencedor_certo": "🏆 Vencedor Certo (10 pts)",
        "sem_pontos": "❌ Sem Pontos (0 pts)"
    })

    def medalha(pos):
        if pos == 1:
            return "🥇 1º"
        if pos == 2:
            return "🥈 2º"
        if pos == 3:
            return "🥉 3º"
        if pos == 4:
            return "🎖️ 4º"
        if pos == 5:
            return "🎖️ 5º"
        return f"🏃 {pos}º"

    df_exibicao["Posição"] = df_exibicao["Posição"].apply(medalha)

    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        height=780
    )
