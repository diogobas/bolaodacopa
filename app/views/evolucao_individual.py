from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px

from app.utils import statistics


def render(df_historico: pd.DataFrame) -> None:
    st.markdown("<div class='section-title'>Análise de Desempenho Individual</div>", unsafe_allow_html=True)

    if df_historico.empty:
        st.info("Nenhum dado cadastrado.")
        return

    df_diario = df_historico.copy()
    df_diario["data"] = pd.to_datetime(df_diario["data_hora"]).dt.date

    data_inicio = date(2026, 6, 11)
    df_diario["dia_copa"] = df_diario["data"].apply(lambda d: (d - data_inicio).days + 1)

    df_diario = df_diario.sort_values(by="data_hora")
    df_diario_grouped = df_diario.groupby(["participante", "arroba", "dia_copa"]).last().reset_index()

    lista_participantes = sorted(df_diario_grouped["participante"].unique())

    c_title, c_selects = st.columns([1.5, 2.5])
    with c_title:
        st.markdown("<p style='margin-top:5px; color:#64748b;'>Selecione o participante principal e escolha se deseja comparar com outro.</p>", unsafe_allow_html=True)
        comparar = st.checkbox("Comparar com outro participante", key="chk_comparar")

    participante_comp = None
    arroba_comp = None

    with c_selects:
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            participante_selecionado = st.selectbox("Participante Principal:", lista_participantes)
        with col_sel2:
            if comparar:
                lista_comparar = [p for p in lista_participantes if p != participante_selecionado]
                participante_comp = st.selectbox("Comparar com:", lista_comparar)

    arroba_selecionado = df_diario_grouped[df_diario_grouped["participante"] == participante_selecionado]["arroba"].iloc[0]
    ind_stats = statistics.calculate_individual_statistics(df_diario_grouped, arroba_selecionado)

    if not comparar:
        st.markdown(f"""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 15px;">
                <div class="metric-card" style="border-left-color: #1e3a8a;">
                    <div class="metric-label">📌 Posição Atual</div>
                    <div class="metric-value">{ind_stats['posicao_atual']}º</div>
                </div>
                <div class="metric-card" style="border-left-color: #16a34a;">
                    <div class="metric-label">⭐ Melhor Posição</div>
                    <div class="metric-value">{ind_stats['melhor_posicao']}º</div>
                </div>
                <div class="metric-card" style="border-left-color: #ef4444;">
                    <div class="metric-label">⚠️ Pior Posição</div>
                    <div class="metric-value">{ind_stats['pior_posicao']}º</div>
                </div>
                <div class="metric-card" style="border-left-color: #94a3b8;">
                    <div class="metric-label">📊 Média de Posição</div>
                    <div class="metric-value">{ind_stats['media_posicao']}º</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        if participante_comp:
            arroba_comp = df_diario_grouped[df_diario_grouped["participante"] == participante_comp]["arroba"].iloc[0]
            ind_stats_comp = statistics.calculate_individual_statistics(df_diario_grouped, arroba_comp)

            col_card1, col_card2 = st.columns(2)
            with col_card1:
                st.markdown(f"<p style='margin: 0 0 5px 0; font-weight:bold; color:#15803d;'>👤 {participante_selecionado}</p>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px;">
                        <div class="metric-card" style="border-left-color: #1e3a8a; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">📌 Posição Atual</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats['posicao_atual']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #16a34a; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">⭐ Melhor Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats['melhor_posicao']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #ef4444; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">⚠️ Pior Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats['pior_posicao']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #94a3b8; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">📊 Média Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats['media_posicao']}º</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            with col_card2:
                st.markdown(f"<p style='margin: 0 0 5px 0; font-weight:bold; color:#1e3a8a;'>👤 {participante_comp}</p>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px;">
                        <div class="metric-card" style="border-left-color: #1e3a8a; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">📌 Posição Atual</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats_comp['posicao_atual']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #16a34a; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">⭐ Melhor Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats_comp['melhor_posicao']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #ef4444; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">⚠️ Pior Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats_comp['pior_posicao']}º</div>
                        </div>
                        <div class="metric-card" style="border-left-color: #94a3b8; padding: 8px 12px !important;">
                            <div class="metric-label" style="font-size:0.75rem;">📊 Média Posição</div>
                            <div class="metric-value" style="font-size:1.15rem;">{ind_stats_comp['media_posicao']}º</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    df_ind1 = df_diario_grouped[df_diario_grouped["arroba"] == arroba_selecionado].copy()
    if comparar and arroba_comp:
        df_ind2 = df_diario_grouped[df_diario_grouped["arroba"] == arroba_comp].copy()
        df_plot = pd.concat([df_ind1, df_ind2], ignore_index=True)
    else:
        df_plot = df_ind1

    if not df_plot.empty:
        fig_rank = px.line(
            df_plot,
            x="dia_copa",
            y="posicao",
            color="participante",
            markers=True,
            title="Evolução de Ranking",
            labels={"dia_copa": "Dia da Copa", "posicao": "Posição", "participante": "Participante"}
        )

        fig_rank.update_yaxes(range=[21.5, 0.5], tickmode="linear", tick0=1, dtick=1)
        fig_rank.update_xaxes(range=[0.5, 39.5], tickmode="linear", tick0=1, dtick=1)

        fig_rank.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#e2e8f0"),
            xaxis=dict(gridcolor="#e2e8f0"),
            font=dict(family="Outfit, sans-serif", size=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                title_text=None
            )
        )

        if not comparar:
            fig_rank.update_traces(line_color="#15803d", marker=dict(size=6, color="#eab308"))
        else:
            fig_rank.update_traces(marker=dict(size=6))

        st.plotly_chart(fig_rank, use_container_width=True)
