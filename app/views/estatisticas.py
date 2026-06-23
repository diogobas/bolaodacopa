import streamlit as st
from app.utils import statistics
import pandas as pd


def render(df_historico: pd.DataFrame) -> None:
    st.markdown("<div class='section-title'>Estatísticas e Recordes do Bolão</div>", unsafe_allow_html=True)

    if df_historico.empty:
        st.info("Nenhum dado cadastrado.")
        return

    global_stats = statistics.calculate_global_statistics(df_historico)
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("<h4 style='margin-top:0;'>👑 Recordistas da Competição</h4>", unsafe_allow_html=True)

        subida = global_stats["maior_subida"]
        queda = global_stats["maior_queda"]
        seq = global_stats["melhor_sequencia"]
        pontos = global_stats["melhor_pontuacao"]
        cons = global_stats["mais_consistente"]
        pe_rec = global_stats["mais_placares_exatos"]
        sp_rec = global_stats["mais_sem_pontos"]

        st.markdown(f"""
            <div style="display:flex; flex-direction:column; gap:8px; color:#0f172a;">
                <div style="background:#ffffff; color:#0f172a; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #22c55e; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">📈 Maior Subida:</strong> {subida['participante']} 
                    <span style="color:#16a34a; font-weight:bold; float:right;">+{subida['valor']} pos</span>
                </div>
                <div style="background:#ffffff; color:#0f172a; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #ef4444; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">📉 Maior Queda:</strong> {queda['participante']} 
                    <span style="color:#dc2626; font-weight:bold; float:right;">-{queda['valor']} pos</span>
                </div>
                <div style="background:#ffffff; color:#0f172a; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #3b82f6; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">🔥 Melhor Sequência:</strong> {seq['participante']} 
                    <span style="color:#2563eb; font-weight:bold; float:right;">{seq['valor']} acertos</span>
                </div>
                <div style="background:#ffffff; color:#0f172a; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #eab308; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">⭐ Melhor Pontuação:</strong> {pontos['participante']} 
                    <span style="color:#ca8a04; font-weight:bold; float:right;">{pontos['valor']} pts</span>
                </div>
                <div style="background:#ffffff; color:#0f172a; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #64748b; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">🎯 Mais Consistente:</strong> {cons['participante']} 
                    <span style="color:#475569; font-weight:bold; float:right;">Desvio Padrão: {cons['desvio']}</span>
                </div>
                <div style="background:#ffffff; color:#0f172a; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #16a34a; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">🎯 Mais Placares Exatos:</strong> {pe_rec['participante']} 
                    <span style="color:#16a34a; font-weight:bold; float:right;">{pe_rec['valor']} acertos</span>
                </div>
                <div style="background:#ffffff; color:#0f172a; padding:12px; border-radius:8px; border:1px solid #e2e8f0; border-left:5px solid #dc2626; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <strong style="color:#0f172a;">❌ Pé-Frio (Sem Pontos):</strong> {sp_rec['participante']} 
                    <span style="color:#dc2626; font-weight:bold; float:right;">{sp_rec['valor']} erros</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c_right:
        st.markdown("<h4 style='margin-top:0;'>🥇 Dias na Liderança</h4>", unsafe_allow_html=True)

        dias = global_stats["dias_lideranca"]
        if not dias:
            st.info("Nenhum participante assumiu a liderança (1º lugar) até o momento.")
        else:
            df_dias = pd.DataFrame(dias).rename(columns={
                "participante": "Participante",
                "arroba": "Usuário (@)",
                "coleta_id": "Dias na Liderança"
            })
            st.dataframe(df_dias, use_container_width=True, hide_index=True, height=250)
