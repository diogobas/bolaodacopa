import logging
import random
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from config import settings

# Configuração do Logger para o coletor
logger = logging.getLogger("collector")
logger.setLevel(logging.INFO)

# Formato de log
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Handler para arquivo
file_handler = logging.FileHandler(settings.LOG_COLLECTOR_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Handler para console (caso rode localmente para debug)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def human_delay(page: Page, min_ms: int = 500, max_ms: int = 1500):
    """Introduz um pequeno atraso aleatório para simular comportamento humano."""
    delay = random.uniform(min_ms, max_ms)
    page.wait_for_timeout(delay)


def check_auth_valid(page: Page) -> bool:
    """
    Verifica se a sessão atual está autenticada.
    Tenta acessar a página principal e verifica se o indicador de login está presente.
    """
    try:
        logger.info("Validando integridade da sessão ativa...")
        page.goto(f"{settings.DACOPA_BASE_URL}/", timeout=15000)
        page.wait_for_load_state("networkidle")
        
        # Obtém o seletor do indicador de login
        selectors = settings.SELECTORS.get("login", {})
        indicator = selectors.get("logged_in_indicator", "button#user-profile-menu")
        
        # Verifica se o indicador está visível
        is_visible = page.locator(indicator).first.is_visible(timeout=5000)
        if is_visible:
            logger.info("Sessão autenticada válida.")
            return True
        else:
            logger.warning("Indicador de login não encontrado. Sessão expirada ou inválida.")
            return False
    except Exception as e:
        logger.warning(f"Erro ao validar a sessão ativa: {e}")
        return False


def perform_login(browser: Browser) -> BrowserContext:
    """
    Realiza o fluxo de login interativo preenchendo o formulário.
    Salva o estado da sessão ao finalizar com sucesso.
    """
    logger.info("Iniciando novo fluxo de login no DaCopa...")
    
    # Garante que as credenciais estão preenchidas
    if not settings.DACOPA_EMAIL or not settings.DACOPA_PASSWORD:
        error_msg = "Credenciais DACOPA_EMAIL ou DACOPA_PASSWORD não configuradas no .env."
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    
    selectors = settings.SELECTORS.get("login", {})
    login_url = f"{settings.DACOPA_BASE_URL}{selectors.get('url_path', '/signin')}"
    
    try:
        # Acessa a página de login
        logger.info(f"Navegando para {login_url}")
        page.goto(login_url, timeout=20000)
        page.wait_for_load_state("networkidle")
        
        # Preenche o e-mail
        email_selector = selectors.get("email_input", "input#email")
        logger.info(f"Preenchendo e-mail no seletor '{email_selector}'")
        page.locator(email_selector).fill(settings.DACOPA_EMAIL)
        human_delay(page)
        
        # Preenche a senha
        pass_selector = selectors.get("password_input", "input#password")
        logger.info(f"Preenchendo senha no seletor '{pass_selector}'")
        page.locator(pass_selector).fill(settings.DACOPA_PASSWORD)
        human_delay(page)
        
        # Clica no botão de enviar
        submit_selector = selectors.get("submit_button", "button[type='submit']")
        logger.info(f"Clicando no botão de login '{submit_selector}'")
        page.locator(submit_selector).click()
        
        # Aguarda carregamento
        page.wait_for_load_state("networkidle")
        human_delay(page, 1000, 2000)
        
        # Valida se logou com sucesso
        indicator = selectors.get("logged_in_indicator", "button#user-profile-menu")
        try:
            logger.info(f"Aguardando indicador de login '{indicator}' ficar visível...")
            page.locator(indicator).first.wait_for(state="visible", timeout=25000)
            logger.info("Login efetuado com sucesso!")
            
            # Salva o estado da sessão
            settings.AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=str(settings.AUTH_STATE_FILE))
            logger.info(f"Estado de autenticação salvo em: {settings.AUTH_STATE_FILE}")
            return context
        except Exception:
            # Captura tela de erro antes de falhar
            screenshot_path = settings.LOGS_DIR / "login_failed_screenshot.png"
            page.screenshot(path=str(screenshot_path))
            logger.error(f"Falha ao validar login: Indicador '{indicator}' não ficou visível. Screenshot salvo em {screenshot_path}")
            raise Exception("Autenticação malsucedida. Verifique suas credenciais ou seletores.")
            
    except Exception as e:
        screenshot_path = settings.LOGS_DIR / "login_exception_screenshot.png"
        try:
            page.screenshot(path=str(screenshot_path))
            logger.error(f"Exceção durante login. Screenshot salvo em {screenshot_path}")
        except Exception:
            pass
        logger.error(f"Erro ao realizar login no DaCopa: {e}")
        context.close()
        raise e


def get_authenticated_context(playwright_instance) -> BrowserContext:
    """
    Retorna um contexto de navegador autenticado.
    Tenta carregar a sessão existente; se falhar ou estiver expirada, realiza um novo login.
    """
    # Lança o navegador Chromium
    browser = playwright_instance.chromium.launch(headless=settings.HEADLESS)
    
    # Se já existir um estado de autenticação salvo
    if settings.AUTH_STATE_FILE.exists():
        logger.info("Carregando estado de autenticação salvo...")
        try:
            context = browser.new_context(
                storage_state=str(settings.AUTH_STATE_FILE),
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            
            # Valida se a sessão ainda está ativa
            if check_auth_valid(page):
                page.close()
                return context
            else:
                logger.info("Sessão salva expirou. Descartando contexto antigo...")
                page.close()
                context.close()
        except Exception as e:
            logger.warning(f"Falha ao carregar storage state existente: {e}")
            
    # Se não existir ou estiver inválida, realiza login novo
    try:
        return perform_login(browser)
    except Exception as e:
        browser.close()
        raise e
