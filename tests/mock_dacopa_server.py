import http.server
import socketserver
import urllib.parse
import threading
import time

PORT = 8080

class MockDaCopaHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suprime logs padrão no terminal para manter a saída limpa
        pass

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Lê cookies do header
        cookies_header = self.headers.get('Cookie', '')
        is_authenticated = 'auth_session=12345' in cookies_header

        if path == '/signin':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Entrar - DaCopa Mock</title></head>
            <body style="font-family: sans-serif; background: #fafafa; display: flex; justify-content: center; align-items: center; height: 100vh;">
                <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 300px;">
                    <h2 style="margin-top:0; color:#333;">Login DaCopa</h2>
                    <form method="POST" action="/signin">
                        <div style="margin-bottom: 15px;">
                            <label style="display:block; margin-bottom:5px;">E-mail</label>
                            <input id="email" type="email" name="email" required style="width:100%; padding:8px; box-sizing:border-box;">
                        </div>
                        <div style="margin-bottom: 15px;">
                            <label style="display:block; margin-bottom:5px;">Senha</label>
                            <input id="password" type="password" name="password" required style="width:100%; padding:8px; box-sizing:border-box;">
                        </div>
                        <button type="submit" style="width:100%; padding:10px; background:#22c55e; border:none; color:white; font-weight:bold; border-radius:4px; cursor:pointer;">Entrar</button>
                    </form>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif path == '/':
            if not is_authenticated:
                # Redireciona para o login se não autenticado
                self.send_response(302)
                self.send_header('Location', '/signin')
                self.end_headers()
                return

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Dashboard - DaCopa Mock</title></head>
            <body>
                <header style="padding: 10px 20px; background: #1e3a8a; color: white; display: flex; justify-content: space-between;">
                    <h3>DaCopa</h3>
                    <button id="user-profile-menu">Meu Perfil</button>
                </header>
                <main style="padding: 20px;">
                    <h1>Bem-vindo à área autenticada</h1>
                    <p>Você está logado no mock da plataforma.</p>
                </main>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

        elif path.startswith('/groups/'):
            if not is_authenticated:
                self.send_response(302)
                self.send_header('Location', '/signin')
                self.end_headers()
                return
            
            group_id = path.split('/')[-1]
            is_members = False
            
            if group_id == 'members':
                is_members = True
                # Pega a parte anterior para o group_id
                group_id = path.split('/')[-2]

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            if is_members:
                # Retorna página de membros do grupo
                html = """
                <!DOCTYPE html>
                <html>
                <head><title>Membros do Grupo - DaCopa Mock</title></head>
                <body>
                    <button id="user-profile-menu">Meu Perfil</button>
                    <h1>Membros do Bolão #{group_id}</h1>
                    <ul class="members-list">
                        <li class="member-item">
                            <span class="member-name">Neymar Junior</span>
                            <span class="member-handle">@neymarjr</span>
                        </li>
                        <li class="member-item">
                            <span class="member-name">Lionel Messi</span>
                            <span class="member-handle">@leomessi</span>
                        </li>
                        <li class="member-item">
                            <span class="member-name">Cristiano Ronaldo</span>
                            <span class="member-handle">@cr7</span>
                        </li>
                        <li class="member-item">
                            <span class="member-name">Vinicius Junior</span>
                            <span class="member-handle">@vini_jr</span>
                        </li>
                    </ul>
                </body>
                </html>
                """.replace('{group_id}', group_id)
            else:
                # Retorna página principal do grupo com ranking
                html = """
                <!DOCTYPE html>
                <html>
                <head><title>Bolão Copa 2026 - DaCopa Mock</title></head>
                <body>
                    <button id="user-profile-menu">Meu Perfil</button>
                    <h1>Grupo do Bolão #{group_id}</h1>
                    <div id="ranking-section">
                        <h2>Classificação Atual</h2>
                        <table id="ranking-table" border="1" cellpadding="5" style="border-collapse: collapse; width: 100%;">
                            <thead>
                                <tr>
                                    <th>Posição</th>
                                    <th>Nome</th>
                                    <th>Arroba</th>
                                    <th>Pontos</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="ranking-list-item">
                                    <td class="rank-column">1</td>
                                    <td class="name-column">Neymar Junior</td>
                                    <td class="handle-column">@neymarjr</td>
                                    <td class="score-column">150</td>
                                </tr>
                                <tr class="ranking-list-item">
                                    <td class="rank-column">2</td>
                                    <td class="name-column">Lionel Messi</td>
                                    <td class="handle-column">@leomessi</td>
                                    <td class="score-column">145</td>
                                </tr>
                                <tr class="ranking-list-item">
                                    <td class="rank-column">3</td>
                                    <td class="name-column">Cristiano Ronaldo</td>
                                    <td class="handle-column">@cr7</td>
                                    <td class="score-column">130</td>
                                </tr>
                                <tr class="ranking-list-item">
                                    <td class="rank-column">4</td>
                                    <td class="name-column">Vinicius Junior</td>
                                    <td class="handle-column">@vini_jr</td>
                                    <td class="score-column">120</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </body>
                </html>
                """.replace('{group_id}', group_id)
                
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/signin':
            # Lê o corpo do POST
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            
            email = params.get('email', [''])[0]
            password = params.get('password', [''])[0]
            
            # Aceita qualquer credencial no mock (para facilitar os testes)
            self.send_response(302)
            self.send_header('Set-Cookie', 'auth_session=12345; Path=/; HttpOnly')
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def run_mock_server():
    handler = MockDaCopaHandler
    # Permite reutilizar o endereço para evitar erro de Address already in use
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    print(f"Iniciando servidor mock do DaCopa na porta {PORT}...")
    run_mock_server()
