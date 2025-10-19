from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from functools import wraps
import os # Para a secret key

app = Flask(__name__)
# É crucial definir uma chave secreta para usar sessions e flash messages
app.secret_key = os.urandom(24) # Ou define uma chave fixa temporariamente

# Configurações (Ajusta conforme necessário)
# URL base da tua API FastAPI (chatbot_api)
API_BASE_URL = "http://100.75.160.12:5005"
#  API_BASE_URL = os.environ.get("http://100.75.160.12:5005")
# --- Decorator para Proteger Rotas ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se 'user' existe E se tem um 'id' (mínimo para ser válido)
        if 'user' not in session or not session['user'].get('id'):
            session.pop('user', None) # Limpa sessão inválida
            flash("Por favor, faça login para aceder a esta página.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas de Autenticação ---
@app.route('/')
def index():
    """ Rota principal, exibe a página de login. """
    if 'user' in session and session['user'].get('id'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Exibe o formulário de login (GET) e processa os dados (POST). """
    if request.method == 'GET' and 'user' in session and session['user'].get('id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Email e senha são obrigatórios.", "error")
            return redirect(url_for('index'))

        auth_url = f"{API_BASE_URL}/login"
        credentials = {"email": email, "password": password}

        try:
            response = requests.post(auth_url, json=credentials, timeout=10)
            response.raise_for_status()
            user_data = response.json()

            # --- ALTERAÇÃO PRINCIPAL AQUI ---
            # Guarda informações na sessão usando .get() com valores padrão
            session['user'] = {
                'id': user_data.get('id_professor') or user_data.get('id_coordenador') or user_data.get('id_aluno'),
                'nome': user_data.get('nome', 'Usuário Desconhecido'), # <--- Valor Padrão
                'email': user_data.get('email'),
                'tipo': user_data.get('tipo', 'desconhecido')
            }
            # Verifica se pelo menos um ID foi obtido
            if not session['user']['id']:
                 flash("Erro ao processar dados do utilizador recebidos da API.", "error")
                 session.pop('user', None) # Limpa sessão inválida
                 return redirect(url_for('index'))

            session.permanent = True

            # Usa o nome obtido (ou o padrão) na mensagem flash
            flash(f"Bem-vindo(a), {session['user'].get('nome', 'Usuário')}!", "success")
            return redirect(url_for('dashboard'))

        # (Restante do tratamento de erros igual ao anterior)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                flash("Credenciais inválidas. Verifique seu email e senha.", "error")
            else:
                flash(f"Erro no servidor de autenticação (HTTP {e.response.status_code}). Tente novamente.", "error")
            return redirect(url_for('index'))
        except requests.exceptions.ConnectionError:
            print(f"Erro: Não foi possível conectar à API em {auth_url}")
            flash("Erro de conexão com o servidor de autenticação. Verifique se a API está online.", "error")
            return redirect(url_for('index'))
        except requests.exceptions.Timeout:
            print(f"Erro: Timeout ao conectar à API em {auth_url}")
            flash("O servidor de autenticação demorou muito para responder. Tente novamente.", "error")
            return redirect(url_for('index'))
        except requests.exceptions.RequestException as e:
            print(f"Erro inesperado de requisição durante o login: {e}")
            flash("Ocorreu um erro de comunicação durante o login. Tente novamente.", "error")
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Erro inesperado durante o login: {e}")
            flash("Ocorreu um erro inesperado durante o login.", "error")
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    """ Limpa a sessão do utilizador (faz logout). """
    session.pop('user', None)
    flash("Logout realizado com sucesso.", "info")
    return redirect(url_for('index'))

# --- Rotas Protegidas ---
@app.route('/dashboard')
@login_required  
def dashboard():
    """ Rota para a página principal do dashboard. Busca dados da API. """
    # Busca apenas o endpoint de avisos que está funcionando
    api_endpoints = {
        "avisos": f"{API_BASE_URL}/aviso/",
        "disciplinas": f"{API_BASE_URL}/disciplina/",
        "professores": f"{API_BASE_URL}/professor/",
        "alunos": f"{API_BASE_URL}/aluno/"
    }
    dashboard_data = {}
    error_occurred = False

    for key, url in api_endpoints.items():
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            # Se a resposta for uma lista, usa direto; se for dict, tenta extrair a lista
            dashboard_data[key] = data if isinstance(data, list) else data.get(key, [])
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar dados de '{key}' da API ({url}): {e}")
            dashboard_data[key] = []
            error_occurred = True

    # Calcula estatísticas baseadas nos dados disponíveis
    dashboard_data['total_avisos'] = len(dashboard_data.get('avisos', []))
    dashboard_data['total_disciplinas'] = len(dashboard_data.get('disciplinas', []))
    dashboard_data['total_professores'] = len(dashboard_data.get('professores', []))
    dashboard_data['total_alunos'] = len(dashboard_data.get('alunos', []))

    if error_occurred:
        flash("Alguns dados do dashboard não puderam ser carregados.", "warning")

    return render_template('dashboard.html', **dashboard_data)

# --- Adiciona outras rotas aqui ---
# Exemplo para a página de Avisos
# @app.route('/avisos')
# @login_required
# def manage_avisos():
#     try:
#         response = requests.get(f"{API_BASE_URL}/aviso/")
#         response.raise_for_status()
#         avisos = response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Erro ao buscar avisos: {e}")
#         flash("Não foi possível carregar os avisos.", "error")
#         avisos = []
#     return render_template('avisos.html', avisos=avisos) # Precisarias criar templates/avisos.html


# --- Execução da Aplicação ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)