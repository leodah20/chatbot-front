from flask import Flask, render_template, request, redirect, url_for, session
import requests  # Importamos a biblioteca para fazer chamadas HTTP
import os  # Importamos para gerar uma chave secreta

app = Flask(__name__)

# IMPORTANTE: O Flask precisa de uma "chave secreta" para gerenciar sessões de forma segura.
# Sem isso, a sessão não funciona.
app.secret_key = os.urandom(24)

# URL da sua API externa (substitua pelo valor real)
API_BASE_URL = "http://100.75.160.12:5005"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')


        # --- INÍCIO DA LÓGICA DE AUTENTICAÇÃO REAL ---
        try:
            # Fazendo a chamada POST para o endpoint de login da sua API
            response = requests.post(
                f"{API_BASE_URL}/login",
                json={'email': email, 'password': senha}
            )




            # Verifica se a API respondeu com sucesso (status 200)
            if response.status_code == 200:
                # Login bem-sucedido!
                user_data = response.json()  # Pega os dados do usuário (ex: nome, tipo)

                # Armazena informações do usuário na sessão para mantê-lo logado
                session['logged_in'] = True
                session['user_name'] = user_data.get('nome', 'Usuário')
                session['user_type'] = user_data.get('tipo', 'desconhecido')  # ex: 'coordenador' ou 'professor'

                # Redireciona para o dashboard
                return redirect(url_for('dashboard'))
            else:
                # A API retornou um erro (ex: 401 - Não Autorizado)
                # Aqui você pode exibir uma mensagem de erro
                return "<h1>Email ou senha inválidos!!</h1>"

        except requests.exceptions.RequestException as e:
            # Falha ao conectar na API
            print(f"Erro ao conectar na API de login: {e}")
            return "<h1>Erro no sistema. Tente novamente mais tarde.</h1>"
        # --- FIM DA LÓGICA DE AUTENTICAÇÃO ---

    return render_template('login.html')


# Rota principal que redireciona para o login
@app.route('/')
def index():
    return redirect(url_for('login'))


# --- NOVAS ROTAS ---


# Rota para o Dashboard (página principal após o login)
@app.route('/dashboard')
def dashboard():
    # Verifica se o usuário está logado antes de permitir o acesso
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Se estiver logado, renderiza a página do dashboard
    # Passamos o nome do usuário para o template poder exibir "Olá, [Nome]!"
    return render_template('dashboard.html', user_name=session.get('user_name'))


# Rota para fazer logout
@app.route('/logout')
def logout():
    # Limpa os dados da sessão
    session.clear()
    # Redireciona de volta para a tela de login
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
