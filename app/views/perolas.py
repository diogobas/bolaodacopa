import streamlit as st
from app.utils import statistics


def render(df_palpites, df_historico) -> None:
    st.markdown("""
    <style>
    .perola-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        margin-bottom: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        border: 1px solid rgba(255,255,255,0.08);
        transition: transform 0.2s;
        position: relative;
        overflow: hidden;
    }
    .perola-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }
    .perola-card-visionario::before   { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
    .perola-card-nostradamus::before  { background: linear-gradient(90deg, #f59e0b, #eab308); }
    .perola-card-ousado::before       { background: linear-gradient(90deg, #f59e0b, #ef4444); }
    .perola-card-maria::before        { background: linear-gradient(90deg, #a78bfa, #ec4899); }
    .perola-card-retr::before         { background: linear-gradient(90deg, #10b981, #06b6d4); }
    .perola-card-futebolarte::before  { background: linear-gradient(90deg, #f97316, #eab308); }
    .perola-card-zicado::before       { background: linear-gradient(90deg, #f97316, #dc2626); }
    .perola-card-pefrio::before       { background: linear-gradient(90deg, #64748b, #475569); }
    .perola-card-golfinho::before     { background: linear-gradient(90deg, #3b82f6, #0ea5e9); }
    .perola-card-rocha::before        { background: linear-gradient(90deg, #78716c, #57534e); }
    .perola-card-diplomata::before    { background: linear-gradient(90deg, #14b8a6, #0d9488); }
    .perola-card-arroz::before        { background: linear-gradient(90deg, #84cc16, #65a30d); }
    .perola-emoji  { font-size: 3rem; margin-bottom: 8px; display: block; }
    .perola-titulo { font-size: 1.1rem; font-weight: 700; letter-spacing: 0.05em;
                     text-transform: uppercase; margin-bottom: 4px; opacity: 0.7; }
    .perola-nome   { font-size: 1.6rem; font-weight: 800; margin: 4px 0; }
    .perola-arroba { font-size: 0.9rem; opacity: 0.6; }
    .perola-valor  { font-size: 1.2rem; font-weight: 600; margin-top: 8px;
                     background: rgba(255,255,255,0.1); border-radius: 8px;
                     padding: 4px 12px; display: inline-block; }
    .perola-desc   { font-size: 0.82rem; opacity: 0.55; margin-top: 10px;
                     font-style: italic; line-height: 1.4; }
    .perola-placares { margin-top: 10px; font-size: 0.8rem; opacity: 0.7;
                       background: rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 12px; }
    .perola-placares-item { margin: 2px 0; }
    .perola-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 14px; padding: 16px 24px; color: white;
        margin-bottom: 20px; text-align: center;
        border: 1px solid rgba(255,255,255,0.06);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="perola-banner">
        <div style="font-size:2.2rem; font-weight:900; letter-spacing:0.04em;">💎 Pérolas do Bolão</div>
        <div style="opacity:0.6; margin-top:4px; font-size:0.95rem;">
            Os apelidos que o bolão deu a cada palpiteiro
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df_palpites.empty:
        st.info("ℹ️ Dados de palpites individuais ainda não coletados. Acesse o **Painel de Administração** e clique em **Atualizar Agora** para coletar os palpites de cada participante.")
        return

    def render_top3(lista, unidade, emoji_medalhas=None):
        if emoji_medalhas is None:
            emoji_medalhas = ["🥇", "🥈", "🥉"]
        if not lista:
            return "<div style='opacity:0.6; padding: 10px 0;'>Nenhum participante qualificado.</div>"

        html = '<div style="margin-top: 16px;">'
        for i, p in enumerate(lista):
            medalha = emoji_medalhas[i] if i < len(emoji_medalhas) else "🏅"
            font_size = "1.2rem" if i == 0 else "1.1rem"
            val_padding = "4px 12px" if i == 0 else "2px 8px"
            val_font = "1.1rem" if i == 0 else "1.0rem"
            html += (
                f'<div style="display: flex; justify-content: space-between; align-items: center; '
                f'margin-bottom: 8px; background: rgba(255,255,255,0.04); padding: 8px 12px; '
                f'border-radius: 8px; border-left: 3px solid rgba(255,255,255,0.2);">'
            )
            html += (
                f'<div><span style="font-size: {font_size};">{medalha}</span> '
                f'<strong style="font-size: {font_size};">{p["participante"]}</strong> '
                f'<span style="font-size:0.8rem; opacity:0.7;">{p["arroba"]}</span></div>'
            )
            html += (
                f'<div class="perola-valor" style="margin-top: 0; padding: {val_padding}; '
                f'font-size: {val_font};">{p["valor"]} '
                f'<span style="font-size: 0.7em; opacity:0.8;">{unidade}</span></div>'
            )
            html += '</div>'
            if i == 0 and p.get("placares"):
                items = "".join(
                    f'<div class="perola-placares-item">⚽ {pl}</div>' for pl in p["placares"]
                )
                html += f'<div class="perola-placares" style="margin-bottom: 12px; margin-top: -4px;">{items}</div>'
            if i == 0 and p.get("info_extra"):
                html += (
                    f'<div class="perola-placares" style="margin-bottom: 12px; margin-top: -4px;">'
                    f'<div class="perola-placares-item">🔁 {p["info_extra"]}</div></div>'
                )
        html += '</div>'
        return html

    perolas = statistics.calculate_perolas(df_palpites, df_historico)

    PEROLAS_CONFIG = [
        {
            "chave": "visionario",
            "css": "perola-card-visionario",
            "emoji": "🔮",
            "titulo": "Visionário",
            "desc": "Acertou resultados improváveis que mais ninguém conseguiu cravar.",
            "unidade": "palpite(s) único(s)"
        },
        {
            "chave": "nostradamus",
            "css": "perola-card-nostradamus",
            "emoji": "🌟",
            "titulo": "Nostradamus",
            "desc": "Quando ele fala, a FIFA escuta.",
            "unidade": "placar(es) exato(s)"
        },
        {
            "chave": "ousado",
            "css": "perola-card-ousado",
            "emoji": "🦅",
            "titulo": "Ousadia e Alegria",
            "desc": "Apostou sozinho, sem mais ninguém com o mesmo placar. O mais ousado e criativo do grupo!",
            "unidade": "palpite(s)"
        },
        {
            "chave": "maria",
            "css": "perola-card-maria",
            "emoji": "🐑",
            "titulo": "Maria vai com as outras",
            "desc": "Mais vezes apostou o mesmo placar que a maioria do grupo. Segurança em números!",
            "unidade": "vez(es)"
        },
        {
            "chave": "retranqueiro",
            "css": "perola-card-retr",
            "emoji": "🧱",
            "titulo": "Retranqueiro",
            "desc": "Apostou menos gols que qualquer outro participante. Amor pelo 0x0!",
            "unidade": "gol(s)"
        },
        {
            "chave": "futebol_arte",
            "css": "perola-card-futebolarte",
            "emoji": "🎨",
            "titulo": "Futebol Arte",
            "desc": "Apostou mais gols que qualquer outro participante. O negócio é sacudir a roseira!",
            "unidade": "gol(s)"
        },
        {
            "chave": "zicado",
            "css": "perola-card-zicado",
            "emoji": "🤦",
            "titulo": "Zicado",
            "desc": "Mais vezes errou o placar por apenas um gol de diferença no total. Quase lá... mas não!",
            "unidade": "vez(es)"
        },
        {
            "chave": "pe_frio",
            "css": "perola-card-pefrio",
            "emoji": "🥶",
            "titulo": "Pé Frio",
            "desc": "Uma máquina de errar! Mais vezes não marcou ponto algum na rodada.",
            "unidade": "rodada(s) zerada(s)"
        },
        {
            "chave": "golfinho",
            "css": "perola-card-golfinho",
            "emoji": "🐬",
            "titulo": "Golfinho",
            "desc": "Participantes que mais alternaram posições ao longo do tempo. Sobe e desce sem parar!",
            "unidade": "posições movidas"
        },
        {
            "chave": "rocha",
            "css": "perola-card-rocha",
            "emoji": "🪨",
            "titulo": "Rocha",
            "desc": "Nem sobe, nem desce. A estabilidade em pessoa.",
            "unidade": "mudança(s) de posição"
        },
        {
            "chave": "diplomata",
            "css": "perola-card-diplomata",
            "emoji": "🤝",
            "titulo": "Diplomata",
            "desc": "Para ele, todo mundo merece um pontinho. O Rei do empate!",
            "unidade": "empate(s) apostado(s)"
        },
        {
            "chave": "arroz_feijao",
            "css": "perola-card-arroz",
            "emoji": "🍚",
            "titulo": "Arroz com Feijão",
            "desc": "Não inventa moda. Sempre o mesmo padrão.",
            "unidade": "placar(es) distinto(s)"
        },
    ]

    for i in range(0, len(PEROLAS_CONFIG), 2):
        cols = st.columns(2)
        for j, cfg in enumerate(PEROLAS_CONFIG[i:i+2]):
            dados = perolas.get(cfg["chave"], [])
            with cols[j]:
                st.markdown(f"""
<div class="perola-card {cfg['css']}">
    <span class="perola-emoji">{cfg['emoji']}</span>
    <div class="perola-titulo">{cfg['titulo']}</div>
    <div class="perola-desc">{cfg['desc']}</div>
{render_top3(dados, cfg['unidade'])}
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='section-title'>📋 Detalhe dos Palpites Coletados</div>", unsafe_allow_html=True)

    ultimo_coleta = df_palpites["coleta_id"].iloc[-1]
    df_detalhe = df_palpites[df_palpites["coleta_id"] == ultimo_coleta].copy()
    df_detalhe["Jogo"] = df_detalhe["mandante"] + " x " + df_detalhe["visitante"]
    df_detalhe["Placar Real"] = df_detalhe["placar_real_m"].astype(str) + " x " + df_detalhe["placar_real_v"].astype(str)
    df_detalhe["Palpite"] = df_detalhe["palpite_m"].astype(str) + " x " + df_detalhe["palpite_v"].astype(str)
    df_detalhe = df_detalhe[["participante", "arroba", "Jogo", "Placar Real", "Palpite", "categoria"]]
    df_detalhe.columns = ["Participante", "Arroba", "Jogo", "Placar Real", "Palpite", "Categoria"]
    st.dataframe(df_detalhe, use_container_width=True, height=400)
