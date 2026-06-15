import os
import time
from playwright.sync_api import sync_playwright
from config import settings

def inspect():
    print("Iniciando inspeção da plataforma DaCopa real...")
    print(f"E-mail: {settings.DACOPA_EMAIL}")
    print(f"Grupo: {settings.DACOPA_GROUP_ID}")
    
    # Força a URL base real temporariamente para esta inspeção
    base_url = "https://app.dacopa.com"
    
    with sync_playwright() as p:
        # Lança em modo headless
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        # 1. Login
        login_url = f"{base_url}/signin"
        print(f"Navegando para {login_url}")
        page.goto(login_url)
        page.wait_for_load_state("networkidle")
        
        print("Preenchendo credenciais...")
        page.locator("input#email").fill(settings.DACOPA_EMAIL)
        page.locator("input#password").fill(settings.DACOPA_PASSWORD)
        
        print("Clicando em Entrar...")
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Salva screenshot pós-login para confirmar sucesso
        settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(settings.LOGS_DIR / "inspect_after_login.png"))
        print(f"URL atual após login: {page.url}")
        
        # 2. Página de Membros do Grupo
        members_url = f"{base_url}/groups/{settings.DACOPA_GROUP_ID}/members"
        print(f"Navegando para a página de membros: {members_url}")
        page.goto(members_url)
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Salva HTML e Screenshot de membros
        members_html = page.content()
        with open(settings.LOGS_DIR / "members_page.html", "w", encoding="utf-8") as f:
            f.write(members_html)
        page.screenshot(path=str(settings.LOGS_DIR / "members_page_real.png"))
        print("HTML e Screenshot da página de membros salvos em logs/")
        
        # 3. Página de Ranking do Grupo
        group_url = f"{base_url}/groups/{settings.DACOPA_GROUP_ID}"
        print(f"Navegando para a página do grupo/ranking: {group_url}")
        page.goto(group_url)
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Salva HTML e Screenshot do ranking
        ranking_html = page.content()
        with open(settings.LOGS_DIR / "ranking_page.html", "w", encoding="utf-8") as f:
            f.write(ranking_html)
        page.screenshot(path=str(settings.LOGS_DIR / "ranking_page_real.png"))
        print("HTML e Screenshot da página de ranking salvos em logs/")
        
        browser.close()
        print("Inspeção concluída com sucesso!")

if __name__ == "__main__":
    inspect()
