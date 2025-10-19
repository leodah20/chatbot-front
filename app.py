from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from functools import wraps
import os # Para a secret key

app = Flask(__name__)
# É crucial definir uma chave secreta para usar sessions e flash messages
# Podes gerar uma chave aleatória (ex: import os; os.urandom(24))
# e guardá-la numa variável de ambiente por segurança.
app.secret_key = os.urandom(24) # Ou define uma chave fixa temporariamente

# URL base da tua API FastAPI (chatbot_api)
# Lembra-te de ajustar se estiver a correr noutra porta ou endereço
API_BASE_URL = "http://127.0.0.1:8000"

# --- Decorator para Proteger Rotas ---
def login_required(f):
    """
    Decorator para garantir que o utilizador está logado antes de aceder a uma rota.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Por favor, faça login para aceder a esta página.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas de Autenticação ---
@app.route('/')
def index():
    """ Rota para a página de login. """
    # Se o utilizador já estiver logado, redireciona para o dashboard
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """ Processa os dados do formulário de login. """
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Email e senha são obrigatórios.", "error")
        return redirect(url_for('index'))

    # Endpoint de autenticação da tua API (ajusta se for diferente)
    auth_url = f"{API_BASE_URL}/auth/login"
    credentials = {"username": username, "password": password}

    try:
        response = requests.post(auth_url, json=credentials)
        response.raise_for_status() # Lança erro para respostas 4xx/5xx

        # Se o login for bem-sucedido, a API deve retornar os dados do utilizador
        user_data = response.json()

        # Guarda as informações do utilizador na sessão
        # Adapta os nomes das chaves ('id_professor', 'nome', etc.)
        # conforme o que a tua API retorna
        session['user'] = {
            'id': user_data.get('id_professor') or user_data.get('id_coordenador') or user_data.get('id_aluno'), # Adapta conforme necessário
            'nome': user_data.get('nome'),
            'email': user_data.get('email'),
            'tipo': user_data.get('tipo', 'desconhecido') # Ex: 'professor', 'coordenador'
        }
        session.permanent = True # Torna a sessão mais duradoura (opcional)

        # Redireciona para o dashboard após login bem-sucedido
        return redirect(url_for('dashboard'))

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            flash("Credenciais inválidas. Verifique seu email e senha.", "error")
        else:
            flash(f"Erro ao tentar fazer login (HTTP {e.response.status_code}). Tente novamente.", "error")
        return redirect(url_for('index'))
    except requests.exceptions.RequestException as e:
        # Erro de conexão com a API
        print(f"Erro de conexão com a API de autenticação: {e}")
        flash("Não foi possível conectar ao servidor de autenticação. Tente novamente mais tarde.", "error")
        return redirect(url_for('index'))
    except Exception as e:
        # Outro erro inesperado
        print(f"Erro inesperado durante o login: {e}")
        flash("Ocorreu um erro inesperado durante o login.", "error")
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """ Limpa a sessão do utilizador (faz logout). """
    session.pop('user', None)
    flash("Logout realizado com sucesso.", "info")
    return redirect(url_for('index'))


# --- Rotas Protegidas (Exemplo: Dashboard) ---
@app.route('/dashboard')
@login_required # Aplica o decorator para exigir login
def dashboard():
    """ Rota para a página principal do dashboard. """
    # Tenta buscar dados da API para exibir nos cartões
    try:
        avisos_resp = requests.get(f"{API_BASE_URL}/aviso/")
        avisos_resp.raise_for_status()
        avisos = avisos_resp.json()

        disciplinas_resp = requests.get(f"{API_BASE_URL}/disciplina/")
        disciplinas_resp.raise_for_status()
        disciplinas = disciplinas_resp.json()

        professores_resp = requests.get(f"{API_BASE_URL}/professor/") # Assumindo endpoint /professor/
        professores_resp.raise_for_status()
        professores = professores_resp.json()

        alunos_resp = requests.get(f"{API_BASE_URL}/aluno/") # Assumindo endpoint /aluno/
        alunos_resp.raise_for_status()
        alunos = alunos_resp.json()

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados para o dashboard: {e}")
        flash("Erro ao carregar dados do dashboard. A API pode estar indisponível.", "error")
        # Define listas vazias para evitar erros no template
        avisos, disciplinas, professores, alunos = [], [], [], []

    # Renderiza o template do dashboard passando os dados
    return render_template('dashboard.html',
                           avisos=avisos,
                           disciplinas=disciplinas,
                           professores=professores,
                           alunos=alunos)

# --- Adiciona outras rotas protegidas aqui (ex: /avisos, /disciplinas, etc.) ---
# @app.route('/avisos')
# @login_required
# def manage_avisos():
#     # Lógica para buscar avisos da API e renderizar templates/avisos.html
#     pass


# --- Execução da Aplicação ---
if __name__ == '__main__':
    # debug=True é útil durante o desenvolvimento, mas DESATIVA em produção
    app.run(debug=True, port=5001) # Usa a porta 5001 para não conflitar com a API na 8000