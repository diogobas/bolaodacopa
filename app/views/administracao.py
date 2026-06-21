from pathlib import Path
import streamlit as st
from config import settings
from app import scheduler


def render(missing_dacopa_env: list[str]) -> None:
    st.markdown("<div class='section-title'>Painel Administrativo do Bolão</div>", unsafe_allow_html=True)

    sched_status = scheduler.get_status()
    ultima_exec = sched_status.get("ultima_execucao_auto")
    ultima_sucesso = sched_status.get("ultima_execucao_sucesso")
    em_execucao = sched_status.get("em_execucao", False)
    proxima = sched_status.get("proxima_execucao", "—")
    horario_gatilho = sched_status.get("horario_disparado", "—")

    if ultima_exec:
        ultima_exec_str = ultima_exec.strftime("%d/%m/%Y às %H:%M:%S")
        icone_sucesso = "✅" if ultima_sucesso else "❌"
        ultima_label = f"{icone_sucesso} {ultima_exec_str} (gatilho: {horario_gatilho} BRT)"
    else:
        ultima_label = "Nenhuma execução automática desde que o app foi iniciado."

    status_cor = "#f59e0b" if em_execucao else "#16a34a"
    status_txt = "⏳ Sincronizando agora..." if em_execucao else "✅ Aguardando próximo horário"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; border: 1px solid #334155;">
        <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 8px;">🤖 Agendador Automático</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
            <div>
                <div style="color: #64748b; font-size: 0.75rem; margin-bottom: 2px;">Status</div>
                <div style="color: {status_cor}; font-weight: 700; font-size: 0.95rem;">{status_txt}</div>
            </div>
            <div>
                <div style="color: #64748b; font-size: 0.75rem; margin-bottom: 2px;">Última Execução Automática</div>
                <div style="color: #f8fafc; font-weight: 600; font-size: 0.85rem;">{ultima_label}</div>
            </div>
            <div>
                <div style="color: #64748b; font-size: 0.75rem; margin-bottom: 2px;">Próximo Horário (BRT)</div>
                <div style="color: #eab308; font-weight: 700; font-size: 1.1rem;">🕐 {proxima}</div>
            </div>
        </div>
        <div style="margin-top: 10px; color: #475569; font-size: 0.75rem;">
            Horários programados (BRT): {' · '.join(sorted(scheduler.HORARIOS_AGENDADOS))}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_info = st.columns([1, 2])

    with col_btn:
        st.markdown("<h4 style='margin-top:0;'>Coletas Manuais</h4>", unsafe_allow_html=True)

        if missing_dacopa_env:
            st.error(
                "Configuração DaCopa incompleta. Preencha no `.env`: "
                + ", ".join(missing_dacopa_env)
                + ". Depois reinicie o Streamlit."
            )

        if st.button(
            "🔄 Sincronizar Tudo (Membros + Ranking + Palpites)",
            use_container_width=True,
            disabled=bool(missing_dacopa_env),
        ):
            with st.spinner("Conectando ao DaCopa via Playwright..."):
                st.info("Iniciando sincronização completa de membros, classificação e palpites detalhados...")
                try:
                    from collectors import scraper
                except Exception as e:
                    st.error(
                        "Não foi possível carregar o módulo de coleta (Playwright ausente).\n"
                        "Instale as dependências: `pip install -r requirements.txt` e execute `playwright install chromium`.\n"
                        f"Erro: {e}"
                    )
                    success = False
                else:
                    try:
                        success = scraper.run_coleta_completa()
                    except Exception as e:
                        st.error(f"Erro durante a coleta: {e}")
                        success = False

                if success:
                    st.success("Dados reais sincronizados e gravados no Excel com sucesso! 🎉")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Ocorreu uma falha durante a sincronização. Verifique os logs.")

        st.markdown("---")
        st.markdown("**Status do Excel**")
        st.write(f"📁 `membros.xlsx`: {'Sim' if settings.MEMBROS_EXCEL.exists() else 'Não'}")
        st.write(f"📁 `historico.xlsx`: {'Sim' if settings.HISTORICO_EXCEL.exists() else 'Não'}")

    with col_info:
        st.markdown("<h4 style='margin-top:0;'>Últimos Registros do Sistema (Logs)</h4>", unsafe_allow_html=True)

        log_file = Path(settings.LOG_COLLECTOR_FILE)
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    linhas = f.readlines()
                    ultimas_linhas = linhas[-12:] if len(linhas) > 12 else linhas
                    st.code("".join(ultimas_linhas), language="text")
            except Exception as e:
                st.error(f"Erro ao ler arquivo de logs: {e}")
        else:
            st.info("Nenhum log gerado no momento.")
