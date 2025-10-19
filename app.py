# ===== IMPORTAÇÕES =====
from flask import Flask, render_template, request, redirect, url_for, session, flash # Importa o módulo Flask e as funções necessárias para criar a aplicação web
import requests  # Biblioteca para fazer chamadas HTTP para a API externa
import os  # Biblioteca para gerar chave secreta aleatória

# ===== CONFIGURAÇÃO DA APLICAÇÃO FLASK =====
app = Flask(__name__)

# IMPORTANTE: O Flask precisa de uma "chave secreta" para gerenciar sessões de forma segura.
# Sem isso, a sessão não funciona. Esta chave é usada para criptografar os dados da sessão.
app.secret_key = os.urandom(24)

# ===== CONFIGURAÇÕES DA API =====
# URL base da API externa que será consumida pelo frontend
# Esta URL deve ser substituída pela URL real da sua API
API_BASE_URL = "http://100.75.160.12:5005"


# ===== ROTAS DA APLICAÇÃO =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota para autenticação de usuários
    - GET: Exibe o formulário de login
    - POST: Processa os dados de login e autentica com a API externa
    """
    if request.method == 'POST':
        # Obtém os dados do formulário de login
        email = request.form.get('email')
        senha = request.form.get('senha')

        # --- INÍCIO DA LÓGICA DE AUTENTICAÇÃO REAL ---
        try:
            # Fazendo a chamada POST para o endpoint de login da API externa
            # Envia email e senha no formato JSON
            response = requests.post(
                f"{API_BASE_URL}/login",
                json={'email': email, 'password': senha}
            )

            # Verifica se a API respondeu com sucesso (status 200)
            if response.status_code == 200:
                # Login bem-sucedido!
                user_data = response.json()  # Converte a resposta JSON em dicionário Python

                # Armazena informações do usuário na sessão para mantê-lo logado
                # A sessão é mantida no servidor e associada ao navegador do usuário
                session['logged_in'] = True
                session['user_name'] = user_data.get('nome', 'Usuário')
                session['user_type'] = user_data.get('tipo', 'desconhecido')  # ex: 'coordenador' ou 'professor'

                # Redireciona para o dashboard após login bem-sucedido
                return redirect(url_for('dashboard'))
            else:
                # A API retornou um erro (ex: 401 - Não Autorizado)
                # Exibe uma mensagem de erro para o usuário
                flash('Email ou senha inválidos! Verifique suas credenciais e tente novamente.', 'error')
                return redirect(url_for('login'))

        except requests.exceptions.RequestException as e:
            # Falha ao conectar na API (problema de rede, API fora do ar, etc.)
            print(f"Erro ao conectar na API de login: {e}")
            flash('Erro ao conectar com o servidor. Tente novamente mais tarde.', 'error')
            return redirect(url_for('login'))
        # --- FIM DA LÓGICA DE AUTENTICAÇÃO ---

    # Se o método for GET, exibe o formulário de login
    return render_template('login.html')


# Rota principal que redireciona automaticamente para o login
@app.route('/')
def index():
    """
    Rota raiz da aplicação
    Redireciona automaticamente para a página de login
    """
    return redirect(url_for('login'))


# --- ROTAS PROTEGIDAS (REQUEREM AUTENTICAÇÃO) ---

@app.route('/dashboard')
def dashboard():
    """
    Rota para o Dashboard (página principal após o login)
    Exibe estatísticas e informações gerais do sistema
    """
    # Verifica se o usuário está logado antes de permitir o acesso
    # Se não estiver logado, redireciona para a página de login
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Se estiver logado, renderiza a página do dashboard
    # Passa o nome do usuário para o template poder exibir informações personalizadas
    return render_template('dashboard.html', user_name=session.get('user_name'))


@app.route('/logout')
def logout():
    """
    Rota para fazer logout do usuário
    Limpa todos os dados da sessão e redireciona para o login
    """
    # Limpa todos os dados da sessão (remove informações do usuário logado)
    session.clear()
    # Redireciona de volta para a tela de login
    return redirect(url_for('login'))


# ===== EXECUÇÃO DA APLICAÇÃO =====
if __name__ == '__main__':
    # Inicia o servidor Flask
    # host='0.0.0.0' permite acesso de qualquer IP
    # port=5000 define a porta do servidor
    # debug=True ativa o modo de debug (recarrega automaticamente em mudanças)
    app.run(host='0.0.0.0', port=5000, debug=True)
