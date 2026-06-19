"""
Módulo de Agendamento Automático — Bolão da Copa

Responsável por disparar a função run_coleta_completa() automaticamente
nos horários definidos, no fuso horário de Brasília (America/Sao_Paulo).

Estratégia: Thread Python em background iniciada via st.cache_resource.
O cache garante que a thread seja criada APENAS UMA VEZ por instância do app,
sendo compatível com o ambiente Streamlit Cloud.

Horários de execução automática (BRT):
  00:20 / 03:20 / 15:20 / 17:20 / 18:20 / 19:20 / 20:20 / 21:20 / 22:20
"""

import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo  # Python 3.9+

# Fuso horário de Brasília
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")

# Horários agendados (HH:MM no fuso de Brasília)
HORARIOS_AGENDADOS = [
    "00:20",
    "03:20",
    "15:20",
    "17:20",
    "18:20",
    "19:20",
    "20:20",
    "21:20",
    "22:20",
    "23:20",
]

# Arquivo de log (mesmo usado pelo collector)
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "collector.log"

# Logger dedicado ao agendador
logger = logging.getLogger("bolao.scheduler")
if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [SCHEDULER] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Estado compartilhado (thread-safe via lock)
_estado_lock = threading.Lock()
_estado = {
    "ultima_execucao_auto": None,    # datetime (BRT) da última sincronização automática
    "ultima_execucao_sucesso": None,  # bool — resultado da última execução
    "em_execucao": False,            # True enquanto a coleta estiver rodando
    "horario_disparado": None,       # Qual horário HH:MM foi o gatilho
    "proxima_execucao": None,        # str HH:MM do próximo horário
}


def _calcular_proxima_execucao() -> str:
    """Retorna o próximo horário agendado a partir do momento atual (BRT)."""
    agora = datetime.now(TZ_BRASILIA)
    hora_atual = agora.strftime("%H:%M")

    for h in sorted(HORARIOS_AGENDADOS):
        if h > hora_atual:
            return h

    # Se passou de todos os horários do dia, retorna o primeiro do dia seguinte
    return sorted(HORARIOS_AGENDADOS)[0]


def get_status() -> dict:
    """Retorna uma cópia do estado atual do agendador (thread-safe)."""
    with _estado_lock:
        return dict(_estado)


def _executar_coleta(horario_gatilho: str):
    """Executa a coleta completa em uma sub-thread dedicada."""
    with _estado_lock:
        if _estado["em_execucao"]:
            logger.warning(f"Tentativa de execução às {horario_gatilho} ignorada — coleta já em andamento.")
            return
        _estado["em_execucao"] = True
        _estado["horario_disparado"] = horario_gatilho

    logger.info("=" * 60)
    logger.info(f"SINCRONIZAÇÃO AUTOMÁTICA INICIADA (gatilho: {horario_gatilho} BRT)")
    logger.info("=" * 60)

    try:
        # Importação tardia para evitar ciclos e garantir que settings já está carregado
        from collectors import scraper
        sucesso = scraper.run_coleta_completa()

        with _estado_lock:
            _estado["ultima_execucao_auto"] = datetime.now(TZ_BRASILIA)
            _estado["ultima_execucao_sucesso"] = sucesso
            _estado["em_execucao"] = False
            _estado["proxima_execucao"] = _calcular_proxima_execucao()

        status_str = "SUCESSO ✅" if sucesso else "FALHA ❌"
        logger.info(f"SINCRONIZAÇÃO AUTOMÁTICA FINALIZADA — {status_str}")

    except Exception as e:
        logger.error(f"ERRO INESPERADO na sincronização automática: {e}", exc_info=True)
        with _estado_lock:
            _estado["em_execucao"] = False
            _estado["ultima_execucao_sucesso"] = False
            _estado["proxima_execucao"] = _calcular_proxima_execucao()


def _loop_agendador():
    """
    Loop principal da thread de background.
    Verifica a cada 30 segundos se o horário atual (BRT) corresponde
    a um dos horários agendados, disparando a coleta quando necessário.
    """
    logger.info("Thread de agendamento iniciada.")
    logger.info(f"Horários programados (BRT): {', '.join(sorted(HORARIOS_AGENDADOS))}")

    # Inicializa o próximo horário
    with _estado_lock:
        _estado["proxima_execucao"] = _calcular_proxima_execucao()

    ultimo_horario_disparado = None  # Evita disparar duas vezes no mesmo minuto

    while True:
        try:
            agora_brt = datetime.now(TZ_BRASILIA)
            hora_atual = agora_brt.strftime("%H:%M")

            if hora_atual in HORARIOS_AGENDADOS and hora_atual != ultimo_horario_disparado:
                ultimo_horario_disparado = hora_atual
                logger.info(f"Horário agendado detectado: {hora_atual} BRT — disparando coleta...")

                # Executa em sub-thread para não bloquear o loop de agendamento
                t = threading.Thread(
                    target=_executar_coleta,
                    args=(hora_atual,),
                    daemon=True,
                    name=f"coleta-auto-{hora_atual.replace(':', '')}"
                )
                t.start()

            # Reseta o controle de "já disparado" quando o minuto muda para outro horário
            elif hora_atual != ultimo_horario_disparado:
                ultimo_horario_disparado = None

        except Exception as e:
            logger.error(f"Erro no loop do agendador: {e}", exc_info=True)

        # Aguarda 30 segundos antes da próxima verificação
        time.sleep(30)


def start_scheduler() -> bool:
    """
    Inicia a thread de agendamento em background.
    Deve ser chamada via st.cache_resource para garantir execução única.

    Returns:
        True se a thread foi iniciada com sucesso.
    """
    try:
        thread = threading.Thread(
            target=_loop_agendador,
            daemon=True,  # Thread daemon: é encerrada automaticamente quando o processo principal termina
            name="bolao-scheduler"
        )
        thread.start()
        logger.info("Agendador de sincronização automática iniciado com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Falha ao iniciar thread do agendador: {e}")
        return False
