import threading
import time
import logging

from playwright.sync_api import sync_playwright

from config import settings

from collectors import session_manager, scraper


logger = logging.getLogger("bolao.live_listener")


def _listener_loop(poll_live_interval: int = 10, poll_idle_interval: int = 600):
    """Loop que mantém a conexão com a API em background e persiste `liveMatches`.

    - Quando há partidas ao vivo, verifica mais frequentemente (`poll_live_interval`).
    - Quando não há partidas, reduz frequência (`poll_idle_interval`).
    """
    if not settings.has_dacopa_config():
        logger.info("DaCopa config ausente; listener não iniciado.")
        return

    try:
        with sync_playwright() as p:
            context = session_manager.get_authenticated_context(p)
            page = context.new_page()
            logger.info("Live listener iniciado e autenticado.")

            while True:
                try:
                    api_data = scraper.fetch_leaderboard_api(page)
                    live_matches = api_data.get("liveMatches", []) or []
                    scraper.save_live_matches(live_matches)

                    if live_matches:
                        time.sleep(poll_live_interval)
                    else:
                        time.sleep(poll_idle_interval)

                except Exception as e:
                    logger.error(f"Erro no loop do live listener: {e}", exc_info=True)
                    time.sleep(30)

            # fecha contexto quando o loop terminar (teoricamente nunca)
            try:
                page.close()
            except Exception:
                pass
            try:
                context.close()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Falha ao iniciar live listener: {e}", exc_info=True)


def start_live_listener() -> bool:
    """Inicia a thread de background que escuta atualizações ao vivo.

    Retorna True se a thread foi criada com sucesso.
    """
    try:
        t = threading.Thread(target=_listener_loop, daemon=True, name="bolao-live-listener")
        t.start()
        logger.info("Thread do live listener iniciada.")
        return True
    except Exception as e:
        logger.error(f"Não foi possível iniciar a thread do live listener: {e}")
        return False
