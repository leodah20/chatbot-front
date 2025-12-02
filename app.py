# Imports necessários
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
from functools import wraps
import os
import re
import uuid
import json
from dotenv import load_dotenv
import sys

# ===== CARREGAMENTO E VALIDAÇÃO DE VARIÁVEIS DE AMBIENTE =====
# Carrega as variáveis do arquivo .env
load_dotenv()

# Validação obrigatória: SECRET_KEY
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    print("=" * 80)
    print("ERRO CRÍTICO: Variável de ambiente SECRET_KEY não encontrada!")
    print("=" * 80)
    print("\nPor favor, configure o arquivo .env na raiz do projeto com:")
    print("  SECRET_KEY=sua-chave-secreta-aqui")
    print("\nPara gerar uma chave segura, execute:")
    print("  python -c \"import secrets; print(secrets.token_hex(32))\"")
    print("\nConsulte o README.md para mais informações.")
    print("=" * 80)
    sys.exit(1)

# Validação obrigatória: API_BASE_URL
API_BASE_URL = os.getenv('API_BASE_URL')
if not API_BASE_URL:
    print("=" * 80)
    print("ERRO CRÍTICO: Variável de ambiente API_BASE_URL não encontrada!")
    print("=" * 80)
    print("\nPor favor, configure o arquivo .env na raiz do projeto com:")
    print("  API_BASE_URL=http://127.0.0.1:8000")
    print("\nAjuste a URL conforme necessário se a API estiver em outro servidor.")
    print("\nConsulte o README.md para mais informações.")
    print("=" * 80)
    sys.exit(1)

# Validação: Verifica se o arquivo .env existe
if not os.path.exists('.env'):
    print("=" * 80)
    print("AVISO: Arquivo .env não encontrado na raiz do projeto!")
    print("=" * 80)
    print("\nO arquivo .env é OBRIGATÓRIO para executar esta aplicação.")
    print("\nCrie o arquivo .env na raiz do projeto com as seguintes variáveis:")
    print("  FLASK_APP=app.py")
    print("  FLASK_ENV=development")
    print("  SECRET_KEY=sua-chave-secreta-aqui")
    print("  API_BASE_URL=http://127.0.0.1:8000")
    print("\nPara gerar uma chave segura, execute:")
    print("  python -c \"import secrets; print(secrets.token_hex(32))\"")
    print("\nConsulte o README.md para instruções detalhadas.")
    print("=" * 80)
    sys.exit(1)

# Validação de formato da URL da API
if not API_BASE_URL.startswith(('http://', 'https://')):
    print("=" * 80)
    print("ERRO: API_BASE_URL deve começar com 'http://' ou 'https://'")
    print("=" * 80)
    print(f"Valor atual: {API_BASE_URL}")
    print("\nExemplo correto: http://127.0.0.1:8000")
    print("=" * 80)
    sys.exit(1)

# Configurações opcionais com valores padrão
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# ===== CONFIGURAÇÃO DA APLICAÇÃO FLASK =====
app = Flask(__name__)
app.secret_key = SECRET_KEY  # Chave secreta para sessões (obrigatória)

# Configuração do modo debug baseado na variável de ambiente
if FLASK_ENV == 'development':
    app.config['DEBUG'] = True
    print(f"[INFO] Modo de desenvolvimento ativado")
else:
    app.config['DEBUG'] = DEBUG
    print(f"[INFO] Modo de produção ativado (DEBUG={DEBUG})")

# Log de configuração bem-sucedida
print(f"[INFO] Configuração carregada com sucesso!")
print(f"[INFO] API_BASE_URL: {API_BASE_URL}")
print(f"[INFO] SECRET_KEY configurada: {'*' * 20}...{SECRET_KEY[-8:]}")

# ===== FUNÇÃO HELPER PARA AUTENTICAÇÃO =====
def get_auth_headers():
    # Retorna os headers de autenticação com o access_token da sessão atual.
    # Usado para todas as requisições autenticadas à API.
    headers = {
        "Content-Type": "application/json"
    }
    
    # Adiciona o token Bearer se existir na sessão
    if 'user' in session and session['user'].get('access_token'):
        headers["Authorization"] = f"Bearer {session['user']['access_token']}"
        print(f"[DEBUG] Token incluído nos headers: {session['user']['access_token'][:20]}...")
    else:
        print("[DEBUG] ATENÇÃO: Nenhum access_token encontrado na sessão!")
    
    return headers

# Decorator para proteger rotas que precisam de login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or not session['user'].get('id'):
            session.pop('user', None)
            flash("Por favor, faça login para aceder a esta página.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator para verificar roles permitidos
def role_required(allowed_roles):
    """
    Decorator que verifica se o usuário tem um dos roles permitidos.
    
    Args:
        allowed_roles: Lista de roles permitidos (ex: ['admin', 'professor', 'coordenador'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Primeiro verifica se está logado
            if 'user' not in session or not session['user'].get('id'):
                session.pop('user', None)
                flash("Por favor, faça login para aceder a esta página.", "error")
                return redirect(url_for('index'))
            
            # Verifica o role do usuário
            user_role = session['user'].get('tipo', '').lower()
            
            # Normaliza os roles permitidos para minúsculas para comparação
            allowed_roles_lower = [role.lower() for role in allowed_roles]
            
            if user_role not in allowed_roles_lower:
                flash("Acesso negado. Você não tem permissão para aceder a esta página.", "error")
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ===== ROTAS DE AUTENTICAÇÃO =====

@app.route('/')
def index():
    """ Página inicial - redireciona para login ou dashboard """
    if 'user' in session and session['user'].get('id'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Processa login do usuário via API """
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
            print(f"[DEBUG] Tentando login com: {email}")
            response = requests.post(auth_url, json=credentials, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            # Verifica o status code antes de processar
            if response.status_code != 200:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_text)
                except:
                    error_detail = error_text
                
                print(f"[ERROR] Login falhou com status {response.status_code}: {error_detail}")
                flash(f"Erro ao fazer login: {error_detail}", "error")
                return redirect(url_for('index'))
            
            api_response = response.json()
            print(f"[DEBUG] API Response JSON: {api_response}")

            # A API retorna os dados do usuário dentro de um objeto 'user'
            # Estrutura esperada: {"message": "...", "access_token": "...", "user": {"id": "...", "email": "...", "name": "...", "role": "..."}}
            user_data = api_response.get('user', {})
            
            if not user_data:
                print("[ERROR] Resposta da API não contém objeto 'user'")
                print(f"[DEBUG] Estrutura recebida: {list(api_response.keys())}")
                flash("Erro: Resposta da API em formato inesperado.", "error")
                return redirect(url_for('index'))

            print(f"[DEBUG] User Data extraído: {user_data}")

            # Extrai o ID do usuário - a API sempre retorna 'id' dentro de 'user'
            user_id = user_data.get('id')
            
            if not user_id:
                print("[ERROR] ID do usuário não encontrado na resposta")
                print(f"[DEBUG] User data keys: {list(user_data.keys())}")
                flash("Erro: ID do usuário não encontrado na resposta da API.", "error")
                return redirect(url_for('index'))
            
            # Extrai o nome do usuário
            # A API retorna 'name' que pode ser um nome completo ou separado
            nome_completo = user_data.get('name', '')
            
            # Se o nome estiver vazio, tenta outros campos ou usa email como fallback
            if not nome_completo:
                nome_completo = (
                    user_data.get('nome_aluno') or 
                    user_data.get('nome') or 
                    email.split('@')[0]  # Fallback: parte do email
                )
            
            # Extrai o tipo/role do usuário
            user_tipo = user_data.get('role', 'usuario')
            
            # Extrai o email
            user_email = user_data.get('email', email)

            # Extrai o access_token
            access_token = api_response.get('access_token', '')
            
            if not access_token:
                print("[ERROR] Access token não encontrado na resposta")
                flash("Erro: Token de acesso não encontrado na resposta da API.", "error")
                return redirect(url_for('index'))

            # Guarda informações na sessão
            session['user'] = {
                'id': user_id,
                'nome': nome_completo,
                'email': user_email,
                'tipo': user_tipo,
                'matricula': user_data.get('matricula_ra', ''),
                'access_token': access_token,
                'raw_data': api_response  # Guarda dados brutos para debug
            }
            
            print(f"[INFO] ====== LOGIN REALIZADO COM SUCESSO ======")
            print(f"[INFO] User ID: {user_id}")
            print(f"[INFO] User Email: {user_email}")
            print(f"[INFO] User Name: {nome_completo}")
            print(f"[INFO] User Role: {user_tipo}")
            print(f"[INFO] Access Token: {access_token[:50]}...")
            print(f"[INFO] ===========================================")

            # Login bem-sucedido - configurar sessão
            session.permanent = True
            flash(f"Bem-vindo(a), {session['user'].get('nome', 'Usuário')}!", "success")
            return redirect(url_for('dashboard'))

        except requests.exceptions.HTTPError as e:
            print(f"[DEBUG] HTTPError: {e}")
            error_detail = "Erro desconhecido"
            
            if hasattr(e, 'response') and e.response is not None:
                print(f"[DEBUG] Response Text: {e.response.text}")
                try:
                    error_json = e.response.json()
                    error_detail = error_json.get('detail', e.response.text)
                except:
                    error_detail = e.response.text or str(e)
                
                status_code = e.response.status_code
                
                if status_code == 401:
                    print(f"[ERROR] Status 401 - Credenciais inválidas")
                    flash("Credenciais inválidas. Verifique seu email e senha.", "error")
                elif status_code == 404:
                    flash("Endpoint de login não encontrado na API. Verifique a configuração.", "error")
                elif status_code == 422:
                    flash(f"Dados inválidos: {error_detail}", "error")
                else:
                    flash(f"Erro no servidor de autenticação (HTTP {status_code}): {error_detail}", "error")
            else:
                flash(f"Erro de comunicação: {str(e)}", "error")
            
            return redirect(url_for('index'))
        except requests.exceptions.ConnectionError as e:
            print(f"[DEBUG] ConnectionError: Não foi possível conectar à API em {auth_url}")
            print(f"[DEBUG] Erro: {e}")
            flash("Erro de conexão com o servidor de autenticação. Verifique se a API está online.", "error")
            return redirect(url_for('index'))
        except requests.exceptions.Timeout as e:
            print(f"[DEBUG] Timeout: Timeout ao conectar à API em {auth_url}")
            print(f"[DEBUG] Erro: {e}")
            flash("O servidor de autenticação demorou muito para responder. Tente novamente.", "error")
            return redirect(url_for('index'))
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] RequestException: {e}")
            flash("Ocorreu um erro de comunicação durante o login. Tente novamente.", "error")
            return redirect(url_for('index'))
        except Exception as e:
            print(f"[DEBUG] Exception Inesperada: {e}")
            print(f"[DEBUG] Tipo: {type(e)}")
            import traceback
            traceback.print_exc()
            flash("Ocorreu um erro inesperado durante o login.", "error")
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    """ Limpa a sessão do utilizador (faz logout). """
    print(f"[DEBUG] Logout realizado por: {session.get('user', {}).get('nome', 'Desconhecido')}")
    # Limpa toda a sessão para garantir que nenhum dado permaneça
    session.clear()
    flash("Logout realizado com sucesso. Até logo!", "info")
    return redirect(url_for('index'))

# Rota de debug para visualizar o access_token da sessão atual
@app.route('/debug/token')
@login_required
def debug_token():
    user = session.get('user', {})
    token = user.get('access_token', 'N/A')
    
    debug_info = {
        'access_token': token,
        'token_length': len(token) if token != 'N/A' else 0,
        'token_preview': token[:50] + '...' if token != 'N/A' and len(token) > 50 else token,
        'user_id': user.get('id', 'N/A'),
        'user_email': user.get('email', 'N/A'),
        'user_role': user.get('tipo', 'N/A'),
        'session_exists': 'user' in session
    }
    
    # Retorna como JSON para fácil visualização
    return jsonify(debug_info), 200

# ===== ROTAS PROTEGIDAS =====

@app.route('/dashboard')
@login_required  
def dashboard():
    """ Dashboard principal - busca avisos da API """
    print(f"[DEBUG] Dashboard acessado por: {session.get('user', {}).get('nome', 'Desconhecido')}")
    
    # Inicializa estrutura de dados do dashboard
    dashboard_data = {
        'avisos': [],
        'disciplinas': [],
        'professores': [],
        'alunos': [],
        'user': session.get('user', {})
    }
    
    # Busca avisos da API
    try:
        print(f"[DEBUG] Buscando avisos em: {API_BASE_URL}/aviso/get_lista_aviso/")
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/aviso/get_lista_aviso/", headers=headers, timeout=5)
        print(f"[DEBUG] Avisos - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[DEBUG] Avisos - Tipo de dados: {type(data)}")
            
            if isinstance(data, list):
                dashboard_data['avisos'] = data
                print(f"[DEBUG] {len(data)} avisos encontrados")
            else:
                print(f"[DEBUG] Formato inesperado de avisos: {data}")
        elif response.status_code == 403:
            print(f"[WARN] Avisos - Status 403 - Acesso negado")
            try:
                error_detail = response.json()
                print(f"[WARN] Detalhes do erro: {error_detail}")
                user_role = session.get('user', {}).get('tipo', 'unknown')
                print(f"[WARN] User role: {user_role}")
            except:
                print(f"[WARN] Resposta: {response.text[:200]}")
            # Continua sem avisos, mas não bloqueia o dashboard
        elif response.status_code == 401:
            print(f"[ERROR] Avisos - Status 401 - Token inválido ou expirado")
            flash("Sua sessão expirou. Por favor, faça login novamente.", "error")
            return redirect(url_for('index'))
        else:
            print(f"[WARN] Avisos retornou status {response.status_code}")
            try:
                print(f"[WARN] Resposta: {response.text[:200]}")
            except:
                pass
            
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar avisos: {e}")
    
    # Calcula totais
    dashboard_data['total_avisos'] = len(dashboard_data['avisos'])
    dashboard_data['total_disciplinas'] = 0  # Placeholder
    dashboard_data['total_professores'] = 0  # Placeholder
    dashboard_data['total_alunos'] = 0  # Placeholder
    
    print(f"[DEBUG] Dashboard pronto - Total de avisos: {dashboard_data['total_avisos']}")
    print(f"[DEBUG] Usuário: {dashboard_data['user'].get('nome', 'N/A')} ({dashboard_data['user'].get('email', 'N/A')})")

    return render_template('dashboard.html', **dashboard_data)

@app.route('/test-api')
@login_required
def test_api():
    """ Testa conectividade com a API - útil para debug """
    try:
        print(f"[DEBUG] Testando API em: {API_BASE_URL}")
        
        # Teste básico de conectividade
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"[DEBUG] API Root - Status: {response.status_code}")
        
        # Teste do endpoint de avisos (que sabemos que funciona)
        headers = get_auth_headers()
        response_avisos = requests.get(f"{API_BASE_URL}/aviso/get_lista_aviso/", headers=headers, timeout=5)
        print(f"[DEBUG] Avisos - Status: {response_avisos.status_code}")
        if response_avisos.status_code == 403:
            try:
                error_detail = response_avisos.json()
                print(f"[WARN] Erro 403 ao buscar avisos: {error_detail}")
            except:
                print(f"[WARN] Resposta: {response_avisos.text[:200]}")
        
        # Teste do endpoint de professores (GET não existe)
        try:
            headers = get_auth_headers()
            response_professores = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=5)
            print(f"[DEBUG] Professores GET - Status: {response_professores.status_code}")
            professores_get_status = response_professores.status_code
        except:
            professores_get_status = "Erro de conexão"
        
        # Teste POST com dados mínimos
        test_data = {
            'id_funcional': 'TEST123',
            'nome_professor': 'Teste',
            'sobrenome_professor': 'API',
            'email_institucional': 'teste@docente.unip.br',
            'password': '123456'
        }
        
        try:
            response_post = requests.post(f"{API_BASE_URL}/professores/", json=test_data, timeout=5)
            print(f"[DEBUG] Professores POST - Status: {response_post.status_code}")
            print(f"[DEBUG] Professores POST - Response: {response_post.text}")
            professores_post_status = response_post.status_code
            professores_post_response = response_post.text
        except Exception as e:
            professores_post_status = f"Erro: {e}"
            professores_post_response = "Erro de conexão"
        
        return f"""
        <h1>Teste da API - Professores</h1>
        <p><strong>API Base URL:</strong> {API_BASE_URL}</p>
        <p><strong>API Root:</strong> {response.status_code}</p>
        <p><strong>Avisos GET:</strong> {response_avisos.status_code}</p>
        <p><strong>Professores GET:</strong> {professores_get_status} (Esperado: 405 - Method Not Allowed)</p>
        <p><strong>Professores POST:</strong> {professores_post_status}</p>
        <p><strong>Response POST:</strong> {professores_post_response}</p>
        <hr>
        <h2>Endpoints Disponíveis para Professores:</h2>
        <ul>
            <li>✅ <strong>POST /professores/</strong> - Criar professor</li>
            <li>✅ <strong>PUT /professores/{{id}}</strong> - Atualizar professor</li>
            <li>✅ <strong>DELETE /professores/{{id}}</strong> - Remover professor</li>
            <li>❌ <strong>GET /professores/</strong> - Listar professores (não existe)</li>
            <li>❌ <strong>GET /professores/{{id}}</strong> - Buscar professor (não existe)</li>
        </ul>
        <h3>Campos Suportados:</h3>
        <ul>
            <li><strong>POST:</strong> id_funcional, nome_professor, sobrenome_professor, email_institucional, password</li>
            <li><strong>PUT:</strong> nome_professor, sobrenome_professor, email_institucional</li>
        </ul>
        <p><em>Nota: O frontend usa dados mock para listagem e visualização.</em></p>
        <a href="/docentes">Voltar para Docentes</a>
        """
        
    except Exception as e:
        return f"<h1>Erro no teste da API</h1><p>Erro: {e}</p><a href='/docentes'>Voltar para Docentes</a>"

# ===== ROTAS DE DOCENTES =====
@app.route('/docentes')
@login_required
def docentes_list():
    """ Lista docentes - busca da API """
    try:
        print(f"[DEBUG] Buscando professores em: {API_BASE_URL}/professores/lista_professores/")
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            docentes = response.json()
            print(f"[DEBUG] {len(docentes)} professores encontrados")
            # Salva na sessão para uso posterior
            session['docentes_list'] = docentes
        else:
            print(f"[DEBUG] Professores retornou status {response.status_code}")
            docentes = []  # Retorna lista vazia se não houver dados da API
            flash("Nenhum professor encontrado.", "info")
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar professores: {e}")
        flash("Erro ao carregar professores da API.", "error")
        docentes = []  # Retorna lista vazia em caso de erro
    
    user = session.get('user', {})
    return render_template('docentes/list.html', docentes=docentes, user=user)

@app.route('/docentes/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'coordenador'])
def docentes_add():
    """ Adiciona novo docente via API """
    # Buscar disciplinas da API para popular select
    disciplinas = []
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/disciplinas/lista_disciplina/", headers=headers, timeout=10)
        if response.status_code == 200:
            disciplinas = response.json()
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar disciplinas: {e}")
        disciplinas = []
    
    if request.method == 'POST':
        try:
            # Coleta e valida dados do formulário
            nome_completo = request.form.get('nome', '').strip()
            partes_nome = nome_completo.split(' ', 1)
            nome_professor = partes_nome[0] if partes_nome else ''
            sobrenome_professor = partes_nome[1] if len(partes_nome) > 1 else ''
            
            # Monta dados para API conforme documentação
            docente_data = {
                'id_funcional': request.form.get('matricula', '').strip(),
                'nome_professor': nome_professor.strip(),
                'sobrenome_professor': sobrenome_professor.strip(),
                'email_institucional': request.form.get('email', '').strip(),
                'password': '123456'  # Senha padrão
            }
            
            # Validação obrigatória
            if not docente_data['id_funcional'] or not docente_data['nome_professor'] or not docente_data['email_institucional']:
                flash("Todos os campos obrigatórios devem ser preenchidos.", "error")
                return render_template('docentes/add.html', disciplinas=disciplinas)
            
            # Validação do ID funcional (máximo 7 caracteres)
            if len(docente_data['id_funcional']) > 7:
                flash("ID Funcional deve ter no máximo 7 caracteres.", "error")
                return render_template('docentes/add.html', disciplinas=disciplinas)
            
            # Validação de formato de email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, docente_data['email_institucional']):
                flash("Formato de email inválido.", "error")
                return render_template('docentes/add.html', disciplinas=disciplinas)
            
            # Coleta dados extras (não enviados para API ainda)
            dados_extras = {
                'nivel_acesso': request.form.get('nivel_acesso', ''),
                'disciplinas': request.form.getlist('disciplinas'),
                'dia_semana': request.form.get('dia_semana', ''),
                'horario_inicio': request.form.get('horario_inicio', ''),
                'horario_fim': request.form.get('horario_fim', '')
            }
            
            print(f"[DEBUG] Criando docente: {docente_data}")
            print(f"[DEBUG] URL da API: {API_BASE_URL}/professores/")
            headers = get_auth_headers()
            response = requests.post(f"{API_BASE_URL}/professores/", json=docente_data, headers=headers, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response Headers: {dict(response.headers)}")
            print(f"[DEBUG] Response Text: {response.text}")
            
            if response.status_code == 201:
                try:
                    response_data = response.json()
                    print(f"[DEBUG] Resposta da API: {response_data}")
                    # Adiciona o novo docente à lista da sessão com dados da API
                    add_docente_to_list(docente_data, response_data)
                    flash("Docente cadastrado com sucesso!", "success")
                    return redirect(url_for('docentes_list'))
                except Exception as e:
                    print(f"[ERROR] Erro ao processar resposta da API: {e}")
                    # Tenta adicionar mesmo sem a resposta completa
                    add_docente_to_list(docente_data)
                    flash("Docente cadastrado com sucesso!", "success")
                    return redirect(url_for('docentes_list'))
            elif response.status_code == 400:
                try:
                    error_detail = response.json()
                    flash(f"Dados inválidos: {error_detail}", "error")
                except:
                    flash("Dados inválidos. Verifique se todos os campos estão preenchidos corretamente.", "error")
            else:
                response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            print(f"[DEBUG] HTTPError: {e}")
            if e.response.status_code == 422:
                try:
                    error_detail = e.response.json()
                    flash(f"Dados inválidos: {error_detail}", "error")
                except:
                    flash("Dados inválidos. Verifique o formato.", "error")
            else:
                flash(f"Erro no servidor (HTTP {e.response.status_code}).", "error")
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] RequestException: {e}")
            flash("Erro de comunicação com o servidor.", "error")
        except Exception as e:
            print(f"[DEBUG] Exception: {e}")
            flash("Erro inesperado ao cadastrar docente.", "error")
    
    return render_template('docentes/add.html', disciplinas=disciplinas)

@app.route('/docentes/view/<id>')
@login_required
def docentes_view(id):
    """ Visualiza docente - busca da API ou sessão """
    try:
        print(f"[DEBUG] Buscando professor {id} (tipo: {type(id)})")
        headers = get_auth_headers()
        # Tenta buscar da API primeiro
        response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
        
        docente = None
        if response.status_code == 200:
            professores = response.json()
            print(f"[DEBUG] Professores encontrados: {len(professores)}")
            # Compara IDs como string (suporta UUID e números)
            id_str = str(id).strip()
            for p in professores:
                p_id = p.get('id')
                if p_id is not None:
                    p_id_str = str(p_id).strip()
                    if p_id_str == id_str:
                        docente = p
                        print(f"[DEBUG] Docente encontrado na API: {docente.get('nome_professor', 'N/A')}")
                        break
                    # Tenta também comparar como int se ambos forem numéricos
                    try:
                        if str(p_id_str).isdigit() and str(id_str).isdigit():
                            if int(p_id_str) == int(id_str):
                                docente = p
                                print(f"[DEBUG] Docente encontrado na API (comparação numérica): {docente.get('nome_professor', 'N/A')}")
                                break
                    except (ValueError, TypeError):
                        pass
        
        # Se não encontrou na API, tenta da sessão
        if not docente:
            docentes_list = get_docentes_list()
            id_str = str(id).strip()
            for d in docentes_list:
                d_id = d.get('id')
                if d_id is not None:
                    d_id_str = str(d_id).strip()
                    if d_id_str == id_str:
                        docente = d
                        print(f"[DEBUG] Docente encontrado na sessão: {docente.get('nome_professor', 'N/A')}")
                        break
                    # Tenta também comparar como int se ambos forem numéricos
                    try:
                        if str(d_id_str).isdigit() and str(id_str).isdigit():
                            if int(d_id_str) == int(id_str):
                                docente = d
                                print(f"[DEBUG] Docente encontrado na sessão (comparação numérica): {docente.get('nome_professor', 'N/A')}")
                                break
                    except (ValueError, TypeError):
                        pass
        
        if not docente:
            print(f"[DEBUG] Docente {id} não encontrado na API nem na sessão")
            flash("Docente não encontrado.", "error")
            return redirect(url_for('docentes_list'))
        
        print(f"[DEBUG] Docente encontrado: ID={docente.get('id')}, Nome={docente.get('nome_professor', 'N/A')}")
        return render_template('docentes/view.html', docente=docente, user=session.get('user', {}))
        
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar professor: {e}")
        flash("Erro ao carregar dados do docente.", "error")
        return redirect(url_for('docentes_list'))

@app.route('/docentes/edit/<id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'coordenador'])
def docentes_edit(id):
    """ Edita docente - GET usa mock, POST envia para API """
    # Buscar disciplinas da API para popular select
    disciplinas = []
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/disciplinas/lista_disciplina/", headers=headers, timeout=10)
        if response.status_code == 200:
            disciplinas = response.json()
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar disciplinas: {e}")
        disciplinas = []
    
    if request.method == 'POST':
        try:
            # Coleta dados do formulário e mapeia para a API
            nome_completo = request.form.get('nome', '').strip()
            partes_nome = nome_completo.split(' ', 1)
            nome_professor = partes_nome[0] if partes_nome else ''
            sobrenome_professor = partes_nome[1] if len(partes_nome) > 1 else ''
            
            # Dados para API PUT (apenas campos editáveis conforme documentação)
            docente_data = {
                'nome_professor': nome_professor,
                'sobrenome_professor': sobrenome_professor,
                'email_institucional': request.form.get('email', '')
            }
            
            # Dados extras para futura implementação (armazenados localmente)
            dados_extras = {
                'nivel_acesso': request.form.get('nivel_acesso', ''),
                'disciplinas': request.form.getlist('disciplinas'),
                'dia_semana': request.form.get('dia_semana', ''),
                'horario_inicio': request.form.get('horario_inicio', ''),
                'horario_fim': request.form.get('horario_fim', '')
            }
            
            print(f"[DEBUG] Dados extras (futura implementação): {dados_extras}")
            
            print(f"[DEBUG] Atualizando docente {id}: {docente_data}")
            headers = get_auth_headers()
            response = requests.put(f"{API_BASE_URL}/professores/update/{id}", json=docente_data, headers=headers, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            response.raise_for_status()
            
            # Obtém o docente atualizado da resposta
            docente_atualizado = response.json()
            docente_id_atualizado = docente_atualizado.get('id')
            
            # Atualiza o docente na lista da sessão
            if 'docentes_list' in session and docente_id_atualizado:
                for i, d in enumerate(session['docentes_list']):
                    if d.get('id') == docente_id_atualizado or str(d.get('id')) == str(docente_id_atualizado):
                        session['docentes_list'][i] = docente_atualizado
                        session.modified = True
                        print(f"[DEBUG] Docente atualizado na sessão")
                        break
            
            # Usa o ID retornado pela API para o redirect
            id_para_redirect = docente_id_atualizado if docente_id_atualizado else id
            print(f"[DEBUG] Redirecionando para visualização com ID: {id_para_redirect}")
            
            flash("Docente atualizado com sucesso!", "success")
            return redirect(url_for('docentes_view', id=id_para_redirect))
            
        except requests.exceptions.HTTPError as e:
            print(f"[DEBUG] HTTPError: {e}")
            if e.response.status_code == 422:
                try:
                    error_detail = e.response.json()
                    flash(f"Dados inválidos: {error_detail}", "error")
                except:
                    flash("Dados inválidos. Verifique o formato.", "error")
            else:
                flash(f"Erro no servidor (HTTP {e.response.status_code}).", "error")
            # Em caso de erro, redireciona de volta para a página de edição para que o usuário possa corrigir
            return redirect(url_for('docentes_edit', id=id))
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] RequestException: {e}")
            flash("Erro de comunicação com o servidor.", "error")
            # Em caso de erro, redireciona de volta para a página de edição
            return redirect(url_for('docentes_edit', id=id))
        except Exception as e:
            print(f"[DEBUG] Exception: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            flash("Erro inesperado ao atualizar docente.", "error")
            # Em caso de erro, redireciona de volta para a página de edição
            return redirect(url_for('docentes_edit', id=id))
    
    # GET - Buscar dados do docente para edição
    print(f"[DEBUG] Buscando professor {id} para edição (tipo: {type(id)})")
    try:
        headers = get_auth_headers()
        # Tenta buscar da API primeiro
        response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
        
        docente = None
        if response.status_code == 200:
            professores = response.json()
            print(f"[DEBUG] Professores encontrados: {len(professores)}")
            # Tenta encontrar o docente comparando IDs como string (suporta UUID e números)
            id_str = str(id).strip()
            for p in professores:
                p_id = p.get('id')
                if p_id is not None:
                    p_id_str = str(p_id).strip()
                    # Compara como string (funciona para UUID e números)
                    if p_id_str == id_str:
                        docente = p
                        print(f"[DEBUG] Docente encontrado na API: {docente.get('nome_professor', 'N/A')}")
                        break
                    # Tenta também comparar como int se ambos forem numéricos
                    try:
                        if str(p_id_str).isdigit() and str(id_str).isdigit():
                            if int(p_id_str) == int(id_str):
                                docente = p
                                print(f"[DEBUG] Docente encontrado na API (comparação numérica): {docente.get('nome_professor', 'N/A')}")
                                break
                    except (ValueError, TypeError):
                        pass
        
        # Se não encontrou na API, tenta da sessão
        if not docente:
            docentes_list = get_docentes_list()
            id_str = str(id).strip()
            for d in docentes_list:
                d_id = d.get('id')
                if d_id is not None:
                    d_id_str = str(d_id).strip()
                    if d_id_str == id_str:
                        docente = d
                        print(f"[DEBUG] Docente encontrado na sessão: {docente.get('nome_professor', 'N/A')}")
                        break
                    # Tenta também comparar como int se ambos forem numéricos
                    try:
                        if str(d_id_str).isdigit() and str(id_str).isdigit():
                            if int(d_id_str) == int(id_str):
                                docente = d
                                print(f"[DEBUG] Docente encontrado na sessão (comparação numérica): {docente.get('nome_professor', 'N/A')}")
                                break
                    except (ValueError, TypeError):
                        pass
        
        if not docente:
            print(f"[DEBUG] Docente {id} não encontrado na API nem na sessão")
            print(f"[DEBUG] IDs disponíveis na API: {[str(p.get('id', 'N/A')) for p in professores[:5]]}")
            flash("Docente não encontrado.", "error")
            return redirect(url_for('docentes_list'))
        
        print(f"[DEBUG] Docente encontrado para edição: ID={docente.get('id')}, Nome={docente.get('nome_professor', 'N/A')}")
        return render_template('docentes/edit.html', docente=docente, disciplinas=disciplinas, user=session.get('user', {}))
        
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar professor: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        flash("Erro ao carregar dados do docente.", "error")
        return redirect(url_for('docentes_list'))
    except Exception as e:
        print(f"[DEBUG] Erro inesperado: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        flash("Erro inesperado ao carregar dados do docente.", "error")
        return redirect(url_for('docentes_list'))

@app.route('/docentes/delete/<id>', methods=['POST'])
@login_required
@role_required(['admin', 'coordenador'])
def docentes_delete(id):
    """ Remove docente via API """
    try:
        print(f"[DEBUG] Removendo docente {id} (tipo: {type(id)})")
        # DELETE /professores/delete/{id} - endpoint correto da API
        headers = get_auth_headers()
        url = f"{API_BASE_URL}/professores/delete/{id}"
        print(f"[DEBUG] URL da requisição: {url}")
        print(f"[DEBUG] Headers: {headers}")
        
        response = requests.delete(url, headers=headers, timeout=10)
        print(f"[DEBUG] Status Code: {response.status_code}")
        print(f"[DEBUG] Response Text: {response.text}")
        
        # Status 204 (No Content) é o esperado para delete bem-sucedido
        if response.status_code == 204:
            # Remove o docente da lista da sessão
            remove_docente_from_list(id)
            flash("Docente removido com sucesso!", "success")
        else:
            response.raise_for_status()
        
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] HTTPError: {e}")
        print(f"[DEBUG] Response: {e.response.text if e.response else 'N/A'}")
        if e.response and e.response.status_code == 404:
            flash("Docente não encontrado.", "error")
        elif e.response and e.response.status_code == 403:
            flash("Você não tem permissão para remover este docente.", "error")
        else:
            flash(f"Erro ao remover docente (HTTP {e.response.status_code if e.response else 'N/A'}).", "error")
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] RequestException: {e}")
        flash("Erro de comunicação com o servidor.", "error")
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        flash("Erro inesperado ao remover docente.", "error")
    
    return redirect(url_for('docentes_list'))

# ===== FUNÇÕES AUXILIARES PARA DOCENTES =====

def get_docentes_list():
    """ Retorna a lista de docentes da sessão (vem da API) ou lista vazia """
    return session.get('docentes_list', [])

def add_docente_to_list(docente_data, response_data=None):
    """ Adiciona um novo docente à lista da sessão """
    if 'docentes_list' not in session:
        session['docentes_list'] = []
    
    # Usa o ID da resposta da API se disponível, senão gera um UUID
    if response_data and response_data.get('id'):
        novo_id = response_data.get('id')
    else:
        import uuid
        novo_id = str(uuid.uuid4())
    
    novo_docente = {
        'id': novo_id,
        'nome_professor': docente_data['nome_professor'],
        'sobrenome_professor': docente_data['sobrenome_professor'],
        'email_institucional': docente_data['email_institucional'],
        'id_funcional': docente_data['id_funcional']
    }
    
    # Atualiza com dados da resposta da API se disponível
    if response_data:
        novo_docente.update({
            'id': response_data.get('id', novo_id),
            'disciplina_nomes': response_data.get('disciplina_nomes', []),
            'dias_atendimento': response_data.get('dias_atendimento', []),
            'atendimento_hora_inicio': response_data.get('atendimento_hora_inicio'),
            'atendimento_hora_fim': response_data.get('atendimento_hora_fim')
        })
    
    session['docentes_list'].append(novo_docente)
    session.modified = True
    return novo_docente

def remove_docente_from_list(docente_id):
    """ Remove um docente da lista da sessão """
    if 'docentes_list' in session:
        original_count = len(session['docentes_list'])
        # Compara IDs como string para garantir que funcione independente do tipo
        session['docentes_list'] = [
            d for d in session['docentes_list'] 
            if d.get('id') is not None and str(d.get('id')) != str(docente_id)
        ]
        session.modified = True
        removed_count = original_count - len(session['docentes_list'])
        print(f"[DEBUG] Docente {docente_id} removido da sessão. {removed_count} removido(s), restam {len(session['docentes_list'])} docentes.")

# ===== ROTAS DE CONTEÚDO =====

CONTENT_ENDPOINT_CANDIDATES = [
    "/conteudo",
    "/materiais",
    "/material",
]

def _join_url(base, path):
    return f"{base}{path if path.startswith('/') else '/' + path}"

def resolve_content_endpoint():
    """
    Tenta detectar qual endpoint de conteúdo está disponível na API.
    Retorna o primeiro endpoint que responder (mesmo com erro 400 ou 405, pois indica que existe).
    Se nenhum for encontrado, retorna '/conteudo' como padrão.
    """
    print(f"[DEBUG] Tentando detectar endpoint de conteúdo em {API_BASE_URL}")
    for cand in CONTENT_ENDPOINT_CANDIDATES:
        try:
            url = _join_url(API_BASE_URL, f"{cand}/")
            # Usa headers de autenticação para verificar o endpoint
            headers = get_auth_headers()
            resp = requests.get(url, headers=headers, timeout=5)
            # 200, 204 = sucesso
            # 400, 401, 403 = endpoint existe mas com erro de validação/auth
            # 405 = método não permitido, mas endpoint existe
            # 404 = endpoint não existe
            if resp.status_code in (200, 204, 400, 401, 403, 405):
                print(f"[INFO] Endpoint de conteúdo detectado: {cand} (Status: {resp.status_code})")
                return cand
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Endpoint {cand} não acessível: {e}")
            continue
    print(f"[WARN] Nenhum endpoint de conteúdo encontrado. Usando padrão: /conteudo")
    print(f"[WARN] ATENÇÃO: O endpoint /conteudo pode não existir na API em {API_BASE_URL}")
    return "/conteudo"

def get_conteudos_api():
    """Busca conteúdo da base de conhecimento da API"""
    try:
        headers = get_auth_headers()
        # Usa o endpoint correto para listar todos os conhecimentos
        resp = requests.get(f"{API_BASE_URL}/baseconhecimento/get_lista_conhecimento", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list):
                # Busca todas as disciplinas de uma vez para mapear IDs para nomes
                disciplinas_map = {}
                try:
                    disc_response = requests.get(f"{API_BASE_URL}/disciplinas/lista_disciplina/", headers=headers, timeout=10)
                    if disc_response.status_code == 200:
                        disciplinas = disc_response.json()
                        for disc in disciplinas:
                            disc_id = str(disc.get('id_disciplina', ''))
                            disciplinas_map[disc_id] = disc.get('nome_disciplina', 'Sem Disciplina')
                except Exception as e:
                    print(f"[WARN] Erro ao buscar disciplinas: {e}")
                
                # Transforma dados da base de conhecimento para o formato do frontend
                conteudos = []
                for item in items:
                    # Busca nome da disciplina se tiver id_disciplina
                    disciplina_nome = 'Sem Disciplina'
                    id_disciplina = item.get('id_disciplina')
                    if id_disciplina:
                        id_disciplina_str = str(id_disciplina)
                        disciplina_nome = disciplinas_map.get(id_disciplina_str, 'Sem Disciplina')
                    
                    # Extrai link e URL do arquivo do conteúdo processado
                    link = ''
                    url_arquivo = item.get('url_documento', '')  # Campo direto do banco
                    conteudo_texto = item.get('conteudo_processado', '') or ''
                    
                    # Tenta extrair link do conteúdo processado
                    if conteudo_texto and 'Link:' in conteudo_texto:
                        link_parts = conteudo_texto.split('Link:')
                        if len(link_parts) > 1:
                            link = link_parts[1].split('\n')[0].strip()
                    
                    # Tenta extrair URL do arquivo do conteúdo processado se não tiver no campo direto
                    if not url_arquivo and conteudo_texto and 'Arquivo:' in conteudo_texto:
                        arquivo_parts = conteudo_texto.split('Arquivo:')
                        if len(arquivo_parts) > 1:
                            url_arquivo = arquivo_parts[1].split('\n')[0].strip()
                    
                    # Determina o tipo baseado na categoria
                    categoria = item.get('categoria', 'Material de Aula')
                    if categoria in ['Material Complementar', 'complementar', 'Material Complementar']:
                        tipo = 'complementar'
                    else:
                        tipo = 'aula'  # Default para Material de Aula
                    
                    # Título pode vir do nome_arquivo_origem ou do conteúdo processado
                    titulo = item.get('nome_arquivo_origem', 'Sem título')
                    if (titulo == 'Sem título' or not titulo) and conteudo_texto:
                        # Tenta extrair título do conteúdo processado
                        if 'Material:' in conteudo_texto:
                            titulo_parts = conteudo_texto.split('Material:')
                            if len(titulo_parts) > 1:
                                titulo = titulo_parts[1].split('\n')[0].strip()
                    
                    # Se ainda não tem título, usa o nome do arquivo de origem
                    if not titulo or titulo == 'Sem título':
                        titulo = item.get('nome_arquivo_origem', 'Sem título') or 'Sem título'
                    
                    conteudo = {
                        'id': str(item.get('id_conhecimento', '')),
                        'titulo': titulo,
                        'disciplina': disciplina_nome,
                        'tipo': tipo,
                        'link': link,
                        'url_arquivo': url_arquivo,
                        'categoria': categoria
                    }
                    conteudos.append(conteudo)
                
                print(f"[INFO] {len(conteudos)} conteúdos encontrados na base de conhecimento")
                return conteudos
            else:
                print(f"[WARN] Resposta da API não é uma lista: {type(items)}")
        else:
            print(f"[WARN] Erro ao buscar base de conhecimento: Status {resp.status_code}")
            if resp.status_code == 401:
                print(f"[ERROR] Não autorizado - verifique o token de autenticação")
            elif resp.status_code == 403:
                print(f"[ERROR] Acesso negado")
            else:
                try:
                    error_detail = resp.json()
                    print(f"[ERROR] Detalhes do erro: {error_detail}")
                except:
                    print(f"[ERROR] Resposta: {resp.text[:200]}")
                    
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] Erro HTTP ao buscar base de conhecimento: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[ERROR] Status: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erro de requisição ao buscar base de conhecimento: {e}")
    except Exception as e:
        print(f"[ERROR] Erro inesperado ao buscar base de conhecimento: {e}")
        import traceback
        traceback.print_exc()
    
    return []

def get_disciplina_id_by_name(disciplina_nome):
    """Busca o ID da disciplina pelo nome usando a API"""
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/disciplinas/lista_disciplina/", headers=headers, timeout=10)
        if response.status_code == 200:
            disciplinas = response.json()
            # Busca disciplina por nome (case-insensitive)
            for disc in disciplinas:
                if disc.get('nome_disciplina', '').lower() == disciplina_nome.lower():
                    disciplina_id = disc.get('id_disciplina')
                    print(f"[INFO] Disciplina '{disciplina_nome}' encontrada - ID: {disciplina_id}")
                    return disciplina_id
            print(f"[WARN] Disciplina '{disciplina_nome}' não encontrada na API")
        else:
            print(f"[WARN] Erro ao buscar disciplinas: Status {response.status_code}")
            try:
                print(f"[DEBUG] Resposta: {response.text[:200]}")
            except:
                pass
    except Exception as e:
        print(f"[ERROR] Erro ao buscar disciplina: {e}")
        import traceback
        traceback.print_exc()
    return None

def create_conteudo_api(data, file_storage=None):
    """
    Cria conteúdo usando os endpoints existentes:
    - /documentos/upload para arquivos
    - /baseconhecimento/ para metadados
    """
    user_email = session.get('user', {}).get('email', 'unknown')
    print(f"[INFO] Criando conteúdo - Usuário: {user_email}")
    print(f"[DEBUG] Dados recebidos: {data}")
    print(f"[DEBUG] Arquivo: {file_storage.filename if file_storage and file_storage.filename else 'Nenhum'}")
    
    try:
        headers = get_auth_headers()
        titulo = data.get('titulo', '')
        disciplina_nome = data.get('disciplina', '')
        tipo = data.get('tipo', 'aula')  # aula ou complementar
        link = data.get('link', '')
        
        # 1. Upload do arquivo se houver
        nome_arquivo_final = titulo
        conteudo_para_base = f"Material: {titulo}"
        
        # Mapear tipo para categoria
        categoria_map = {
            'aula': 'Material de Aula',
            'complementar': 'Material Complementar'
        }
        categoria = categoria_map.get(tipo, 'Material de Aula')
        
        # 1. CASO 1: Upload de arquivo (o endpoint já cria na baseconhecimento automaticamente)
        if file_storage and file_storage.filename:
            print(f"[INFO] Fazendo upload do arquivo: {file_storage.filename}")
            
            # Usa upload_disciplina que já salva na baseconhecimento
            if disciplina_nome and disciplina_nome != 'Sem Disciplina':
                success, result = upload_documento_por_categoria(
                    file_storage,
                    'disciplina',
                    nome_disciplina=disciplina_nome
                )
                
                if success:
                    # O endpoint já criou o registro na baseconhecimento
                    base_conhecimento = result.get('base_conhecimento', {})
                    id_conhecimento = base_conhecimento.get('id_conhecimento')
                    url_documento = result.get('url_documento', '') or base_conhecimento.get('url_documento', '')
                    
                    if id_conhecimento:
                        # Atualiza o registro criado com título e categoria corretos
                        update_data = {
                            "nome_arquivo_origem": titulo or file_storage.filename,
                            "categoria": categoria,
                            "palavra_chave": json.dumps([titulo.lower()] if titulo else []),
                        }
                        
                        # Atualiza o conteúdo processado para incluir título
                        conteudo_existente = base_conhecimento.get('resumo', '')
                        conteudo_atualizado = f"{conteudo_existente}\nMaterial: {titulo}" if conteudo_existente else f"Material: {titulo}"
                        update_data["conteudo_processado"] = conteudo_atualizado
                        
                        update_response = requests.put(
                            f"{API_BASE_URL}/baseconhecimento/update/{id_conhecimento}",
                            json=update_data,
                            headers=headers,
                            timeout=10
                        )
                        
                        if update_response.status_code in (200, 204):
                            print(f"[INFO] ✅ Registro atualizado com título e categoria")
                        
                        return True, {
                            'id': str(id_conhecimento),
                            'titulo': titulo or file_storage.filename,
                            'disciplina': disciplina_nome,
                            'tipo': tipo,
                            'link': '',
                            'url_arquivo': url_documento,
                            'message': 'Conteúdo salvo com sucesso na API e armazenado no Supabase'
                        }
                    else:
                        print(f"[WARN] Upload bem-sucedido mas ID não retornado. Dados: {result}")
                        return False, "Erro: Upload concluído mas ID do conhecimento não foi retornado."
                else:
                    error_msg = f"Erro ao fazer upload do arquivo: {result}"
                    print(f"[ERROR] {error_msg}")
                    return False, error_msg
            else:
                # Sem disciplina: precisa criar diretamente na baseconhecimento
                error_msg = "Disciplina é obrigatória para upload de arquivos."
                print(f"[ERROR] {error_msg}")
                return False, error_msg
        
        # CASO 2: Apenas link (cria diretamente na baseconhecimento)
        elif link:
            print(f"[INFO] Criando conteúdo com apenas link (sem arquivo)")
            
            # Buscar ID da disciplina
            id_disciplina = None
            if disciplina_nome and disciplina_nome != 'Sem Disciplina':
                id_disciplina = get_disciplina_id_by_name(disciplina_nome)
            
            # Preparar dados para base de conhecimento
            base_conhecimento_data = {
                "nome_arquivo_origem": titulo,
                "conteudo_processado": f"Link: {link}\nMaterial: {titulo}",
                "palavra_chave": [titulo.lower()] if titulo else [],
                "categoria": categoria,
                "status": "publicado",
            }
            
            if id_disciplina:
                base_conhecimento_data["id_disciplina"] = str(id_disciplina)
            
            # Salvar na base de conhecimento
            base_response = requests.post(
                f"{API_BASE_URL}/baseconhecimento/",
                json=base_conhecimento_data,
                headers=headers,
                timeout=10
            )
            
            print(f"[INFO] POST /baseconhecimento/ - Status: {base_response.status_code}")
            
            if base_response.status_code == 201:
                response_data = base_response.json()
                id_conhecimento = response_data.get('id_conhecimento', '')
                print(f"[INFO] ✅ Conteúdo salvo com sucesso na base de conhecimento")
                
                return True, {
                    'id': str(id_conhecimento),
                    'titulo': titulo,
                    'disciplina': disciplina_nome,
                    'tipo': tipo,
                    'link': link,
                    'url_arquivo': '',
                    'message': 'Conteúdo salvo com sucesso na API e armazenado no Supabase'
                }
            else:
                try:
                    error_detail = base_response.json()
                    error_msg = error_detail.get('detail', base_response.text)
                except:
                    error_msg = base_response.text or f"Erro HTTP {base_response.status_code}"
                print(f"[ERROR] POST /baseconhecimento/ - Status: {base_response.status_code} - {error_msg}")
                return False, error_msg
        else:
            # Nem arquivo nem link - retorna erro
            error_msg = "É necessário fornecer um arquivo ou um link."
            print(f"[ERROR] {error_msg}")
            return False, error_msg
            
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Não foi possível conectar à API em {API_BASE_URL}. Verifique se a API está rodando e acessível."
        print(f"[ERROR] Erro de conexão: {e}")
        return False, error_msg
    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout ao conectar com a API em {API_BASE_URL}. O servidor pode estar sobrecarregado."
        print(f"[ERROR] Timeout: {e}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Erro inesperado ao criar conteúdo: {str(e)}"
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False, error_msg

def update_conteudo_api(conteudo_id, data, file_storage=None):
    """Atualiza conteúdo usando /baseconhecimento/update/{item_id}"""
    try:
        headers = get_auth_headers()
        titulo = data.get('titulo', '')
        disciplina_nome = data.get('disciplina', '')
        tipo = data.get('tipo', 'aula')
        link = data.get('link', '')
        
        # Mapear tipo para categoria
        categoria_map = {
            'aula': 'Material de Aula',
            'complementar': 'Material Complementar'
        }
        categoria = categoria_map.get(tipo, 'Material de Aula')
        
        # Buscar ID da disciplina
        id_disciplina = None
        if disciplina_nome and disciplina_nome != 'Sem Disciplina':
            id_disciplina = get_disciplina_id_by_name(disciplina_nome)
        
        # CASO 1: Upload de novo arquivo (cria novo registro, depois atualiza o antigo e deleta o novo)
        novo_id_conhecimento = None
        url_documento_novo = None
        
        if file_storage and file_storage.filename:
            print(f"[INFO] Fazendo upload do novo arquivo: {file_storage.filename}")
            
            if disciplina_nome and disciplina_nome != 'Sem Disciplina':
                success, result = upload_documento_por_categoria(
                    file_storage,
                    'disciplina',
                    nome_disciplina=disciplina_nome
                )
                
                if success:
                    # O upload criou um novo registro na baseconhecimento
                    base_conhecimento = result.get('base_conhecimento', {})
                    novo_id_conhecimento = base_conhecimento.get('id_conhecimento')
                    url_documento_novo = result.get('url_documento', '') or base_conhecimento.get('url_documento', '')
                    
                    if novo_id_conhecimento and url_documento_novo:
                        print(f"[INFO] ✅ Novo arquivo enviado. Novo registro criado: {novo_id_conhecimento}")
                        print(f"[INFO] URL do documento: {url_documento_novo}")
                    else:
                        print(f"[WARN] Upload concluído mas dados incompletos: {result}")
                else:
                    print(f"[WARN] Erro ao fazer upload do novo arquivo: {result}")
                    return False
        
        # Preparar dados para atualização
        update_data = {
            "nome_arquivo_origem": titulo,
            "categoria": categoria,
            "palavra_chave": json.dumps([titulo.lower()] if titulo else []),
        }
        
        # Se houver novo arquivo, atualiza com o novo url_documento
        if url_documento_novo:
            update_data["url_documento"] = url_documento_novo
        
        # Se houver link, atualiza o conteúdo processado
        if link:
            update_data["conteudo_processado"] = f"Link: {link}\nMaterial: {titulo}"
        elif url_documento_novo:
            # Atualiza com informação do novo arquivo
            update_data["conteudo_processado"] = f"Arquivo: {titulo}\nMaterial: {titulo}"
        
        if id_disciplina:
            update_data["id_disciplina"] = str(id_disciplina)
        
        # Atualizar registro existente na base de conhecimento
        resp = requests.put(
            f"{API_BASE_URL}/baseconhecimento/update/{conteudo_id}",
            json=update_data,
            headers=headers,
            timeout=10
        )
        
        print(f"[INFO] PUT /baseconhecimento/update/{conteudo_id} - Status: {resp.status_code}")
        
        if resp.status_code in (200, 204):
            print(f"[INFO] ✅ Conteúdo atualizado com sucesso no Supabase")
            
            # Se um novo registro foi criado pelo upload, deleta ele (já que atualizamos o antigo)
            if novo_id_conhecimento and str(novo_id_conhecimento) != str(conteudo_id):
                print(f"[INFO] Deletando registro duplicado criado pelo upload: {novo_id_conhecimento}")
                try:
                    delete_resp = requests.delete(
                        f"{API_BASE_URL}/baseconhecimento/delete/{novo_id_conhecimento}",
                        headers=headers,
                        timeout=10
                    )
                    if delete_resp.status_code in (200, 204):
                        print(f"[INFO] ✅ Registro duplicado deletado com sucesso")
                except Exception as e:
                    print(f"[WARN] Erro ao deletar registro duplicado: {e}")
            
            return True
        else:
            print(f"[ERROR] Erro ao atualizar conteúdo: Status {resp.status_code}")
            try:
                error_detail = resp.json()
                print(f"[ERROR] Detalhes: {error_detail}")
            except:
                print(f"[ERROR] Resposta: {resp.text[:200]}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Conteúdo PUT falhou: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"[ERROR] Erro inesperado ao atualizar conteúdo: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_conteudo_api(conteudo_id):
    """Deleta conteúdo usando /baseconhecimento/delete/{item_id}"""
    try:
        headers = get_auth_headers()
        resp = requests.delete(
            f"{API_BASE_URL}/baseconhecimento/delete/{conteudo_id}",
            headers=headers,
            timeout=8
        )
        print(f"[INFO] DELETE /baseconhecimento/delete/{conteudo_id} - Status: {resp.status_code}")
        if resp.status_code in (200, 204):
            print(f"[INFO] ✅ Conteúdo deletado com sucesso do Supabase")
        return resp.status_code in (200, 204)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Conteúdo DELETE falhou: {e}")
        return False

# ===== Sessão (fallback local) =====

def get_conteudo_list_session():
    """ Retorna lista de conteúdos da sessão ou lista vazia se não houver dados """
    return session.get('conteudos_list', [])

def set_conteudo_list_session(items):
    session['conteudos_list'] = items
    session.modified = True

def add_conteudo_session(item):
    items = get_conteudo_list_session()
    max_id = max([i.get('id', 0) for i in items], default=0)
    item = { **item, 'id': item.get('id') or (max_id + 1) }
    items.append(item)
    session.modified = True
    return item

def update_conteudo_session(conteudo_id, updates):
    items = get_conteudo_list_session()
    for i, it in enumerate(items):
        if str(it.get('id')) == str(conteudo_id):
            items[i] = { **it, **updates }
            session.modified = True
            return items[i]
    return None

def find_conteudo_session(conteudo_id):
    items = get_conteudo_list_session()
    return next((it for it in items if str(it.get('id')) == str(conteudo_id)), None)

from collections import defaultdict

def group_by_disciplina(items):
    groups = defaultdict(list)
    for it in items:
        disc = it.get('disciplina') or 'Sem Disciplina'
        # normaliza campo tipo
        tipo = it.get('tipo') or it.get('tipo_material') or ''
        if isinstance(tipo, dict) and 'nome' in tipo:
            tipo = tipo['nome']
        it['tipo'] = tipo
        it['id'] = it.get('id') or it.get('id_conteudo') or it.get('id_material') or it.get('pk')
        it['titulo'] = it.get('titulo') or it.get('nome') or it.get('titulo_material') or 'Sem Título'
        it['url_arquivo'] = it.get('url_arquivo') or it.get('arquivo_url') or it.get('arquivo') or ''
        it['link'] = it.get('link') or it.get('url') or ''
        groups[disc].append(it)
    return groups

@app.route('/conteudo')
@login_required
def conteudo_list():
    # Sempre busca da API primeiro
    api_items = get_conteudos_api()
    
    # Se conseguir buscar da API, usa esses dados
    if api_items and len(api_items) > 0:
        set_conteudo_list_session(api_items)
        items = api_items
        print(f"[INFO] Carregados {len(items)} conteúdos da API")
    else:
        # Fallback para sessão apenas se a API não retornar nada
        items = get_conteudo_list_session()
        if items:
            print(f"[INFO] Usando {len(items)} conteúdos da sessão (fallback)")
        else:
            print(f"[INFO] Nenhum conteúdo encontrado na API nem na sessão")

    grouped = group_by_disciplina(items)
    disciplina = request.args.get('disciplina') or (next(iter(grouped.keys()), 'Sem Disciplina') if grouped else 'Sem Disciplina')

    return render_template('conteudo/list.html', grouped=grouped, disciplina_selecionada=disciplina, user=session.get('user', {}))

@app.route('/conteudo/add', methods=['GET', 'POST'])
@login_required
def conteudo_add():
    print(f"[DEBUG] Rota /conteudo/add acessada - Método: {request.method}")
    
    # Buscar disciplinas da API para popular select
    disciplinas = []
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/disciplinas/lista_disciplina/", headers=headers, timeout=10)
        if response.status_code == 200:
            disciplinas = response.json()
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar disciplinas: {e}")
        disciplinas = []
    
    if request.method == 'POST':
        print(f"[DEBUG] Processando POST /conteudo/add")
        tipo = request.form.get('tipo', 'aula')
        titulo = request.form.get('titulo', '').strip()
        disciplina = request.form.get('disciplina', '').strip() or 'Sem Disciplina'
        link = request.form.get('link', '').strip()
        arquivo = request.files.get('arquivo')
        
        print(f"[DEBUG] Dados do formulário - tipo: {tipo}, titulo: {titulo}, disciplina: {disciplina}, link: {link}")
        print(f"[DEBUG] Arquivo recebido: {arquivo.filename if arquivo and arquivo.filename else 'Nenhum'}")

        if not titulo:
            print(f"[WARN] POST /conteudo/add - Título não fornecido")
            flash('Título é obrigatório.', 'error')
            return render_template('conteudo/add.html', disciplinas=disciplinas)

        if not link and (not arquivo or not arquivo.filename):
            print(f"[WARN] POST /conteudo/add - Nem arquivo nem link fornecido")
            flash('Envie um arquivo ou informe um link.', 'error')
            return render_template('conteudo/add.html', disciplinas=disciplinas)

        payload = { 'tipo': tipo, 'titulo': titulo, 'disciplina': disciplina, 'link': link }
        print(f"[DEBUG] Chamando create_conteudo_api com payload: {payload}")
        ok, resp = create_conteudo_api(payload, arquivo)
        print(f"[DEBUG] Resposta de create_conteudo_api - ok: {ok}, resp: {resp}")
        if ok:
            # Conteúdo já foi salvo na API (base de conhecimento + documentos)
            # Adiciona à sessão para exibição imediata
            added = { 
                **payload, 
                'url_arquivo': resp.get('url_arquivo', '') if isinstance(resp, dict) else '',
                'id': (resp.get('id') if isinstance(resp, dict) else None)
            }
            add_conteudo_session(added)
            
            flash('✅ Conteúdo cadastrado com sucesso na API! O chatbot RASA já pode consultar este material.', 'success')
            return redirect(url_for('conteudo_list', disciplina=disciplina))
        else:
            # Melhora a mensagem de erro para o usuário
            error_message = resp if isinstance(resp, str) else str(resp)
            flash(f'Erro ao cadastrar conteúdo: {error_message}', 'error')

    return render_template('conteudo/add.html', disciplinas=disciplinas)

@app.route('/conteudo/edit/<conteudo_id>', methods=['GET', 'POST'])
@login_required
def conteudo_edit(conteudo_id):
    item = find_conteudo_session(conteudo_id)
    if not item:
        flash('Conteúdo não encontrado.', 'error')
        return redirect(url_for('conteudo_list'))
    
    # Buscar disciplinas da API para popular select
    disciplinas = []
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/disciplinas/lista_disciplina/", headers=headers, timeout=10)
        if response.status_code == 200:
            disciplinas = response.json()
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar disciplinas: {e}")
        disciplinas = []

    if request.method == 'POST':
        tipo = request.form.get('tipo', item.get('tipo'))
        titulo = request.form.get('titulo', item.get('titulo', ''))
        disciplina = request.form.get('disciplina', item.get('disciplina', ''))
        link = request.form.get('link', item.get('link', ''))
        arquivo = request.files.get('arquivo')

        updates = { 'tipo': tipo, 'titulo': titulo, 'disciplina': disciplina, 'link': link }
        api_ok = update_conteudo_api(conteudo_id, updates, arquivo)
        if api_ok:
            update_conteudo_session(conteudo_id, updates)
            flash('Conteúdo atualizado com sucesso!', 'success')
            return redirect(url_for('conteudo_list', disciplina=disciplina))
        else:
            flash('Erro ao atualizar conteúdo.', 'error')

    return render_template('conteudo/edit.html', conteudo=item, disciplinas=disciplinas)

@app.route('/conteudo/delete/<conteudo_id>', methods=['POST'])
@login_required
def conteudo_delete(conteudo_id):
    """ Remove conteúdo via API (Supabase) """
    try:
        print(f"[DEBUG] Removendo conteúdo {conteudo_id}")
        
        # Deletar na API (Supabase)
        api_ok = delete_conteudo_api(conteudo_id)
        
        if api_ok:
            # Remove da sessão local
            items = get_conteudo_list_session()
            items[:] = [item for item in items if str(item.get('id')) != str(conteudo_id)]
            set_conteudo_list_session(items)
            
            flash('Conteúdo removido com sucesso do Supabase!', 'success')
        else:
            flash('Erro ao remover conteúdo da API.', 'error')
            
    except Exception as e:
        print(f"[DEBUG] Erro ao remover conteúdo: {e}")
        flash('Erro inesperado ao remover conteúdo.', 'error')
    
    return redirect(url_for('conteudo_list'))

# ===== ROTAS DE AVISOS =====

@app.route('/avisos')
@login_required
def avisos_list():
    """ Lista avisos - busca da API """
    try:
        print(f"[DEBUG] Buscando avisos em: {API_BASE_URL}/aviso/get_lista_aviso/")
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/aviso/get_lista_aviso/", headers=headers, timeout=10)
        print(f"[DEBUG] Avisos - Status: {response.status_code}")
        
        if response.status_code == 200:
            avisos = response.json()
            print(f"[DEBUG] {len(avisos)} avisos encontrados")
        else:
            print(f"[DEBUG] Avisos retornou status {response.status_code}")
            avisos = []
            
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar avisos: {e}")
        flash("Erro ao carregar avisos. Tente novamente.", "error")
        avisos = []
    
    return render_template('avisos/list.html', avisos=avisos)

@app.route('/avisos/add', methods=['GET', 'POST'])
@login_required
def avisos_add():
    """ Adiciona novo aviso via API """
    # Carregar professores e coordenadores para o formulário
    professores = []
    coordenadores = []
    
    try:
        headers = get_auth_headers()
        # Buscar professores
        prof_response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
        if prof_response.status_code == 200:
            professores = prof_response.json()
        
        # Buscar coordenadores
        coord_response = requests.get(f"{API_BASE_URL}/coordenador/get_list_coordenador/", headers=headers, timeout=10)
        if coord_response.status_code == 200:
            coordenadores = coord_response.json()
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao carregar professores/coordenadores: {e}")
        # Continua com listas vazias
    
    if request.method == 'POST':
        try:
            # Coleta dados do formulário
            id_professor = request.form.get('id_professor', '').strip()
            id_coordenador = request.form.get('id_coordenador', '').strip()
            
            # Validar UUIDs - se vazio ou inválido, usar None
            id_professor_uuid = None
            id_coordenador_uuid = None
            
            if id_professor:
                try:
                    id_professor_uuid = str(uuid.UUID(id_professor))
                except (ValueError, AttributeError):
                    flash(f"ID do professor inválido: {id_professor}. Use um UUID válido ou deixe em branco.", "error")
                    return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
            
            if id_coordenador:
                try:
                    id_coordenador_uuid = str(uuid.UUID(id_coordenador))
                except (ValueError, AttributeError):
                    flash(f"ID do coordenador inválido: {id_coordenador}. Use um UUID válido ou deixe em branco.", "error")
                    return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
            
            aviso_data = {
                'titulo': request.form.get('titulo', '').strip(),
                'conteudo': request.form.get('conteudo', '').strip(),
                'data': request.form.get('data', '').strip(),
                'id_professor': id_professor_uuid,
                'id_coordenador': id_coordenador_uuid
            }
            
            # Validação obrigatória
            if not aviso_data['titulo'] or not aviso_data['conteudo'] or not aviso_data['data']:
                flash("Título, conteúdo e data são obrigatórios.", "error")
                return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
            
            # Validação de data
            try:
                from datetime import datetime
                datetime.strptime(aviso_data['data'], '%Y-%m-%d')
            except ValueError:
                flash("Formato de data inválido. Use YYYY-MM-DD.", "error")
                return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
            
            # Log do usuário que está criando o aviso
            user_role = session.get('user', {}).get('tipo', 'unknown')
            user_email = session.get('user', {}).get('email', 'unknown')
            print(f"[INFO] POST /aviso/ - Usuário: {user_email}, Role: {user_role}")
            print(f"[DEBUG] Criando aviso: {aviso_data}")
            
            headers = get_auth_headers()
            response = requests.post(f"{API_BASE_URL}/aviso/", json=aviso_data, headers=headers, timeout=10)
            
            print(f"[INFO] POST /aviso/ - Status: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            if response.status_code == 201:
                print(f"[INFO] POST /aviso/ - Status: 201 - Aviso criado com sucesso")
                print(f"[DEBUG] User role: {user_role}")
                print(f"[DEBUG] Aviso criado com sucesso")
                flash("Aviso criado com sucesso!", "success")
                return redirect(url_for('avisos_list'))
            elif response.status_code == 400:
                print(f"[ERROR] POST /aviso/ - Status: 400 - Dados inválidos")
                try:
                    error_detail = response.json()
                    flash(f"Dados inválidos: {error_detail}", "error")
                except:
                    flash("Dados inválidos. Verifique se todos os campos estão preenchidos corretamente.", "error")
                return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
            elif response.status_code == 403:
                print(f"[WARN] POST /aviso/ - Status: 403 - Acesso negado")
                print(f"[WARN] User role: {user_role}")
                try:
                    error_detail = response.json()
                    detail_msg = error_detail.get('detail', 'Acesso negado')
                    print(f"[WARN] Acesso negado. Roles permitidos: admin, coordenador. Seu role: {user_role}")
                    flash(f"Acesso negado: {detail_msg}", "error")
                except:
                    flash("Acesso negado. Apenas administradores e coordenadores podem criar avisos.", "error")
                return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
            elif response.status_code == 401:
                print(f"[ERROR] POST /aviso/ - Status: 401 - Token inválido ou não fornecido")
                flash("Sua sessão expirou. Por favor, faça login novamente.", "error")
                return redirect(url_for('index'))
            else:
                response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else 'N/A'
            print(f"[ERROR] POST /aviso/ - HTTPError: Status {status_code}")
            print(f"[DEBUG] HTTPError: {e}")
            if e.response.status_code == 422:
                try:
                    error_detail = e.response.json()
                    flash(f"Dados inválidos: {error_detail}", "error")
                except:
                    flash("Dados inválidos. Verifique o formato.", "error")
                return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
            elif e.response.status_code == 403:
                print(f"[WARN] POST /aviso/ - Status: 403 - Acesso negado")
                user_role = session.get('user', {}).get('tipo', 'unknown')
                print(f"[WARN] User role: {user_role}")
                try:
                    error_detail = e.response.json()
                    detail_msg = error_detail.get('detail', 'Acesso negado')
                    print(f"[WARN] Acesso negado. Roles permitidos: admin, coordenador. Seu role: {user_role}")
                    flash(f"Acesso negado: {detail_msg}", "error")
                except:
                    flash("Acesso negado. Apenas administradores e coordenadores podem criar avisos.", "error")
                return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
            elif e.response.status_code == 401:
                print(f"[ERROR] POST /aviso/ - Status: 401 - Token inválido ou não fornecido")
                flash("Sua sessão expirou. Por favor, faça login novamente.", "error")
                return redirect(url_for('index'))
            else:
                flash(f"Erro no servidor (HTTP {e.response.status_code}).", "error")
                return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] RequestException: {e}")
            flash("Erro de comunicação com o servidor.", "error")
        except Exception as e:
            print(f"[DEBUG] Exception: {e}")
            flash("Erro inesperado ao criar aviso.", "error")
    
    return render_template('avisos/add.html', professores=professores, coordenadores=coordenadores)

@app.route('/avisos/view/<aviso_id>')
@login_required
def avisos_view(aviso_id):
    """ Visualiza aviso espec��fico """
    try:
        print(f"[DEBUG] Buscando aviso {aviso_id}")
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/aviso/get_aviso_id/{aviso_id}", headers=headers, timeout=10)
        print(f"[DEBUG] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            aviso = response.json()
            print(f"[DEBUG] Aviso encontrado: {aviso}")
            return render_template('avisos/view.html', aviso=aviso)
        elif response.status_code == 404:
            flash("Aviso não encontrado.", "error")
        else:
            response.raise_for_status()
            
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] HTTPError: {e}")
        flash(f"Erro ao buscar aviso (HTTP {e.response.status_code}).", "error")
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] RequestException: {e}")
        flash("Erro de comunicação com o servidor.", "error")
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        flash("Erro inesperado ao buscar aviso.", "error")
    
    return redirect(url_for('avisos_list'))

@app.route('/avisos/edit/<aviso_id>', methods=['GET', 'POST'])
@login_required
def avisos_edit(aviso_id):
    """ Edita aviso existente """
    if request.method == 'POST':
        try:
            # Coleta dados do formulário
            aviso_data = {
                'titulo': request.form.get('titulo', '').strip(),
                'conteudo': request.form.get('conteudo', '').strip(),
                'data': request.form.get('data', '').strip(),
                'id_professor': request.form.get('id_professor', '').strip() or None,
                'id_coordenador': request.form.get('id_coordenador', '').strip() or None
            }
            
            # Validação obrigatória
            if not aviso_data['titulo'] or not aviso_data['conteudo'] or not aviso_data['data']:
                flash("Título, conteúdo e data são obrigatórios.", "error")
                # Recarregar professores e coordenadores em caso de erro
                professores = []
                coordenadores = []
                try:
                    headers = get_auth_headers()
                    prof_response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
                    if prof_response.status_code == 200:
                        professores = prof_response.json()
                    coord_response = requests.get(f"{API_BASE_URL}/coordenador/get_list_coordenador/", headers=headers, timeout=10)
                    if coord_response.status_code == 200:
                        coordenadores = coord_response.json()
                except:
                    pass
                return render_template('avisos/edit.html', aviso={'id_aviso': aviso_id, **aviso_data}, professores=professores, coordenadores=coordenadores)
            
            # Validar UUIDs - se vazio ou inválido, usar None
            id_professor_uuid = None
            id_coordenador_uuid = None
            
            if aviso_data['id_professor']:
                try:
                    id_professor_uuid = str(uuid.UUID(aviso_data['id_professor']))
                except (ValueError, AttributeError):
                    flash(f"ID do professor inválido: {aviso_data['id_professor']}. Use um UUID válido ou deixe em branco.", "error")
                    # Recarregar professores e coordenadores em caso de erro
                    professores = []
                    coordenadores = []
                    try:
                        headers = get_auth_headers()
                        prof_response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
                        if prof_response.status_code == 200:
                            professores = prof_response.json()
                        coord_response = requests.get(f"{API_BASE_URL}/coordenador/get_list_coordenador/", headers=headers, timeout=10)
                        if coord_response.status_code == 200:
                            coordenadores = coord_response.json()
                    except:
                        pass
                    return render_template('avisos/edit.html', aviso={'id_aviso': aviso_id, **aviso_data}, professores=professores, coordenadores=coordenadores)
            
            if aviso_data['id_coordenador']:
                try:
                    id_coordenador_uuid = str(uuid.UUID(aviso_data['id_coordenador']))
                except (ValueError, AttributeError):
                    flash(f"ID do coordenador inválido: {aviso_data['id_coordenador']}. Use um UUID válido ou deixe em branco.", "error")
                    # Recarregar professores e coordenadores em caso de erro
                    professores = []
                    coordenadores = []
                    try:
                        headers = get_auth_headers()
                        prof_response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
                        if prof_response.status_code == 200:
                            professores = prof_response.json()
                        coord_response = requests.get(f"{API_BASE_URL}/coordenador/get_list_coordenador/", headers=headers, timeout=10)
                        if coord_response.status_code == 200:
                            coordenadores = coord_response.json()
                    except:
                        pass
                    return render_template('avisos/edit.html', aviso={'id_aviso': aviso_id, **aviso_data}, professores=professores, coordenadores=coordenadores)
            
            # Atualizar aviso_data com UUIDs validados
            aviso_data['id_professor'] = id_professor_uuid
            aviso_data['id_coordenador'] = id_coordenador_uuid
            
            # Validação de data
            try:
                from datetime import datetime
                datetime.strptime(aviso_data['data'], '%Y-%m-%d')
            except ValueError:
                flash("Formato de data inválido. Use YYYY-MM-DD.", "error")
                # Recarregar professores e coordenadores em caso de erro
                professores = []
                coordenadores = []
                try:
                    headers = get_auth_headers()
                    prof_response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
                    if prof_response.status_code == 200:
                        professores = prof_response.json()
                    coord_response = requests.get(f"{API_BASE_URL}/coordenador/get_list_coordenador/", headers=headers, timeout=10)
                    if coord_response.status_code == 200:
                        coordenadores = coord_response.json()
                except:
                    pass
                return render_template('avisos/edit.html', aviso={'id_aviso': aviso_id, **aviso_data}, professores=professores, coordenadores=coordenadores)
            
            print(f"[DEBUG] Atualizando aviso {aviso_id}: {aviso_data}")
            headers = get_auth_headers()
            response = requests.put(f"{API_BASE_URL}/aviso/update/{aviso_id}", json=aviso_data, headers=headers, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            if response.status_code == 200:
                flash("Aviso atualizado com sucesso!", "success")
                return redirect(url_for('avisos_view', aviso_id=aviso_id))
            elif response.status_code == 404:
                flash("Aviso não encontrado.", "error")
                return redirect(url_for('avisos_list'))
            else:
                response.raise_for_status()
            
        except requests.exceptions.HTTPError as e:
            print(f"[DEBUG] HTTPError: {e}")
            if e.response.status_code == 422:
                try:
                    error_detail = e.response.json()
                    flash(f"Dados inválidos: {error_detail}", "error")
                except:
                    flash("Dados inválidos. Verifique o formato.", "error")
            else:
                flash(f"Erro no servidor (HTTP {e.response.status_code}).", "error")
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] RequestException: {e}")
            flash("Erro de comunicação com o servidor.", "error")
        except Exception as e:
            print(f"[DEBUG] Exception: {e}")
            flash("Erro inesperado ao atualizar aviso.", "error")
    
    # GET - Buscar dados do aviso para edição
    # Carregar professores e coordenadores para o formulário
    professores = []
    coordenadores = []
    
    try:
        headers = get_auth_headers()
        # Buscar professores
        prof_response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
        if prof_response.status_code == 200:
            professores = prof_response.json()
        
        # Buscar coordenadores
        coord_response = requests.get(f"{API_BASE_URL}/coordenador/get_list_coordenador/", headers=headers, timeout=10)
        if coord_response.status_code == 200:
            coordenadores = coord_response.json()
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao carregar professores/coordenadores: {e}")
        # Continua com listas vazias
    
    try:
        print(f"[DEBUG] Buscando aviso {aviso_id} para edição")
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/aviso/get_aviso_id/{aviso_id}", headers=headers, timeout=10)
        print(f"[DEBUG] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            aviso = response.json()
            print(f"[DEBUG] Aviso encontrado para edição: {aviso}")
            return render_template('avisos/edit.html', aviso=aviso, professores=professores, coordenadores=coordenadores)
        elif response.status_code == 404:
            flash("Aviso não encontrado.", "error")
            return redirect(url_for('avisos_list'))
        else:
            response.raise_for_status()
            
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] HTTPError: {e}")
        flash(f"Erro ao buscar aviso (HTTP {e.response.status_code}).", "error")
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] RequestException: {e}")
        flash("Erro de comunicação com o servidor.", "error")
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        flash("Erro inesperado ao buscar aviso.", "error")
    
    return redirect(url_for('avisos_list'))

@app.route('/avisos/delete/<aviso_id>', methods=['POST'])
@login_required
def avisos_delete(aviso_id):
    """ Remove aviso via API """
    try:
        print(f"[DEBUG] Removendo aviso {aviso_id}")
        headers = get_auth_headers()
        response = requests.delete(f"{API_BASE_URL}/aviso/delete/{aviso_id}", headers=headers, timeout=10)
        print(f"[DEBUG] Status Code: {response.status_code}")
        
        if response.status_code == 204:
            flash("Aviso removido com sucesso!", "success")
        elif response.status_code == 404:
            flash("Aviso não encontrado.", "error")
        else:
            response.raise_for_status()
        
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] HTTPError: {e}")
        flash(f"Erro ao remover aviso (HTTP {e.response.status_code}).", "error")
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] RequestException: {e}")
        flash("Erro de comunicação com o servidor.", "error")
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        flash("Erro inesperado ao remover aviso.", "error")
    
    return redirect(url_for('avisos_list'))


# ===== ROTAS DE CALENDÁRIO =====

def get_materias_list():
    """Busca a lista de disciplinas (matérias) da API"""
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{API_BASE_URL}/disciplinas/lista_disciplina/",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            disciplinas = response.json()
            # Transforma os dados da API para o formato esperado pelo template
            materias = []
            for disc in disciplinas:
                # Garante que o ID seja uma string válida
                id_disciplina = disc.get('id_disciplina')
                if id_disciplina:
                    # Se for UUID, converte para string
                    id_str = str(id_disciplina)
                else:
                    print(f"[WARN] Disciplina sem ID: {disc.get('nome_disciplina', 'N/A')}")
                    continue
                
                materia = {
                    'id': id_str,  # ID como string para uso nas URLs
                    'nome': disc.get('nome_disciplina', 'N/A'),
                    'codigo': disc.get('codigo', 'N/A'),  # Campo correto do schema
                    'carga_horaria': f"{disc.get('carga_horaria', 0)}h",
                    'modalidade': disc.get('semestre', 'N/A'),  # Usa semestre como modalidade temporariamente
                    'professor': 'N/A'  # Será preenchido se houver professores
                }
                
                # Se houver professores associados, pega o primeiro
                if disc.get('professores') and len(disc.get('professores', [])) > 0:
                    prof = disc['professores'][0]
                    nome_prof = f"{prof.get('nome_professor', '')} {prof.get('sobrenome_professor', '')}".strip()
                    if nome_prof:
                        materia['professor'] = nome_prof
                
                materias.append(materia)
            
            print(f"[DEBUG] {len(materias)} matérias carregadas da API")
            return materias
        else:
            print(f"[ERROR] Erro ao buscar disciplinas: {response.status_code}")
            print(f"[ERROR] Resposta: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erro de conexão ao buscar disciplinas: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Erro inesperado ao buscar disciplinas: {e}")
        import traceback
        traceback.print_exc()
        return []

def add_materia_session(item):
    items = get_materias_list()
    max_id = max([i.get('id', 0) for i in items], default=0)
    novo = { **item, 'id': max_id + 1 }
    items.append(novo)
    session.modified = True
    return novo

def get_wizard_state():
    return session.setdefault('materia_wizard', {})

def clear_wizard_state():
    session.pop('materia_wizard', None)
    session.modified = True

@app.route('/calendario')
@login_required
def calendario_list():
    materias = get_materias_list()
    return render_template('calendario/list.html', materias=materias, user=session.get('user', {}))

@app.route('/calendario/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor', 'coordenador'])
def calendario_add():
    step = int(request.args.get('step') or request.form.get('step') or 1)
    wizard = get_wizard_state()
    
    # Buscar professores da API para popular selects
    professores = []
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
        if response.status_code == 200:
            professores = response.json()
            # Formatar nome completo para exibição
            for prof in professores:
                nome = prof.get('nome_professor', '')
                sobrenome = prof.get('sobrenome_professor', '')
                prof['nome_completo'] = f"{nome} {sobrenome}".strip()
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar professores: {e}")
        professores = []

    if request.method == 'POST':
        if step == 1:
            wizard.update({
                'nome': request.form.get('nome', '').strip(),
                'professor': request.form.get('professor', '').strip(),
                'codigo': request.form.get('codigo', '').strip(),
                'carga_horaria': request.form.get('carga_horaria', '').strip(),
                'modalidade': request.form.get('modalidade', '').strip(),
            })
            session.modified = True
            return redirect(url_for('calendario_add', step=2))
        elif step == 2:
            wizard.update({
                'ementa_resumo': request.form.get('ementa_resumo', '').strip(),
                'ementa_arquivo_nome': (request.files.get('ementa_arquivo').filename if request.files.get('ementa_arquivo') and request.files.get('ementa_arquivo').filename else '')
            })
            session.modified = True
            return redirect(url_for('calendario_add', step=3))
        elif step == 3:
            wizard.update({
                'dia_semana': request.form.get('dia_semana', '').strip(),
                'hora_inicio': request.form.get('hora_inicio', '').strip(),
                'hora_fim': request.form.get('hora_fim', '').strip(),
                'sala': request.form.get('sala', '').strip(),
            })
            session.modified = True
            return redirect(url_for('calendario_add', step=4))
        elif step == 4:
            provas = {
                'np1': {
                    'data': request.form.get('np1_data', '').strip(),
                    'inicio': request.form.get('np1_inicio', '').strip(),
                    'fim': request.form.get('np1_fim', '').strip(),
                    'sala': request.form.get('np1_sala', '').strip(),
                    'aplicador': request.form.get('np1_aplicador', '').strip(),
                    'conteudo': request.form.get('np1_conteudo', '').strip(),
                },
                'np2': {
                    'data': request.form.get('np2_data', '').strip(),
                    'inicio': request.form.get('np2_inicio', '').strip(),
                    'fim': request.form.get('np2_fim', '').strip(),
                    'sala': request.form.get('np2_sala', '').strip(),
                    'aplicador': request.form.get('np2_aplicador', '').strip(),
                    'conteudo': request.form.get('np2_conteudo', '').strip(),
                },
                'exame': {
                    'data': request.form.get('exame_data', '').strip(),
                    'inicio': request.form.get('exame_inicio', '').strip(),
                    'fim': request.form.get('exame_fim', '').strip(),
                    'sala': request.form.get('exame_sala', '').strip(),
                    'aplicador': request.form.get('exame_aplicador', '').strip(),
                    'conteudo': request.form.get('exame_conteudo', '').strip(),
                },
                'sub': {
                    'data': request.form.get('sub_data', '').strip(),
                    'inicio': request.form.get('sub_inicio', '').strip(),
                    'fim': request.form.get('sub_fim', '').strip(),
                    'sala': request.form.get('sub_sala', '').strip(),
                    'aplicador': request.form.get('sub_aplicador', '').strip(),
                    'conteudo': request.form.get('sub_conteudo', '').strip(),
                }
            }
            wizard['provas'] = provas

            # Salvar na API
            try:
                headers = get_auth_headers()
                
                # 1. Criar disciplina na API
                # Mapear dia da semana de nome para número
                dias_semana_map = {
                    'segunda-feira': 1,
                    'terça-feira': 2,
                    'quarta-feira': 3,
                    'quinta-feira': 4,
                    'sexta-feira': 5,
                    'sábado': 6,
                    'domingo': 7
                }
                
                # Preparar dados da disciplina
                disciplina_data = {
                    'nome_disciplina': wizard.get('nome', ''),
                    'codigo': wizard.get('codigo', ''),
                    'semestre': wizard.get('modalidade', ''),  # Usando modalidade como semestre temporariamente
                    'ementa': wizard.get('ementa_resumo', ''),
                    'carga_horaria': int(wizard.get('carga_horaria', '0').replace('h', '').replace('H', '').strip()) if wizard.get('carga_horaria') else 0
                }
                
                print(f"[DEBUG] Criando disciplina: {disciplina_data}")
                disciplina_response = requests.post(
                    f"{API_BASE_URL}/disciplinas/",
                    json=disciplina_data,
                    headers=headers,
                    timeout=10
                )
                
                if disciplina_response.status_code not in [200, 201]:
                    error_detail = disciplina_response.json().get('detail', f'Erro {disciplina_response.status_code}') if disciplina_response.headers.get('content-type', '').startswith('application/json') else disciplina_response.text
                    raise Exception(f"Erro ao criar disciplina: {error_detail}")
                
                disciplina_criada = disciplina_response.json()
                disciplina_id = disciplina_criada.get('id_disciplina')
                print(f"[DEBUG] Disciplina criada com ID: {disciplina_id}")
                
                # 2. Associar professor à disciplina (se houver)
                if wizard.get('professor'):
                    # Buscar ID do professor pelo nome
                    professores_response = requests.get(
                        f"{API_BASE_URL}/professores/lista_professores/",
                        headers=headers,
                        timeout=10
                    )
                    if professores_response.status_code == 200:
                        professores_list = professores_response.json()
                        for prof in professores_list:
                            nome_completo = f"{prof.get('nome_professor', '')} {prof.get('sobrenome_professor', '')}".strip()
                            if nome_completo == wizard.get('professor'):
                                professor_id = prof.get('id_professor')
                                # Associar professor à disciplina via atualização do professor
                                # A API cria a associação automaticamente quando atualizamos disciplina_nomes
                                try:
                                    # Buscar disciplinas atuais do professor
                                    prof_response = requests.get(
                                        f"{API_BASE_URL}/professores/get_professor_id/{professor_id}",
                                        headers=headers,
                                        timeout=10
                                    )
                                    if prof_response.status_code == 200:
                                        prof_data = prof_response.json()
                                        disciplinas_atual = prof_data.get('disciplina_nomes', [])
                                        if wizard.get('nome') not in disciplinas_atual:
                                            disciplinas_atual.append(wizard.get('nome'))
                                        
                                        # Atualizar professor com nova disciplina (a API cria a associação)
                                        update_response = requests.put(
                                            f"{API_BASE_URL}/professores/update/{professor_id}",
                                            json={'disciplina_nomes': disciplinas_atual},
                                            headers=headers,
                                            timeout=10
                                        )
                                        if update_response.status_code == 200:
                                            print(f"[DEBUG] Professor associado à disciplina")
                                        else:
                                            print(f"[WARN] Erro ao atualizar professor: {update_response.text}")
                                except Exception as e:
                                    print(f"[WARN] Erro ao associar professor: {e}")
                                break
                
                # 3. Criar cronograma na API (se houver dados)
                if wizard.get('dia_semana') and wizard.get('hora_inicio') and wizard.get('hora_fim'):
                    try:
                        dia_num = dias_semana_map.get(wizard.get('dia_semana', '').lower())
                        # Formatar hora para HH:MM:SS se necessário
                        hora_inicio = wizard.get('hora_inicio', '')
                        if hora_inicio and len(hora_inicio) == 5:  # HH:MM
                            hora_inicio = f"{hora_inicio}:00"
                        hora_fim = wizard.get('hora_fim', '')
                        if hora_fim and len(hora_fim) == 5:  # HH:MM
                            hora_fim = f"{hora_fim}:00"
                        
                        cronograma_data = {
                            'nome_disciplina': wizard.get('nome', ''),
                            'hora_inicio': hora_inicio,
                            'hora_fim': hora_fim,
                            'periodicidade': 'semanal',
                            'id_disciplina': str(disciplina_id),
                            'dia_semana': dia_num,
                            'sala': int(wizard.get('sala', 0)) if wizard.get('sala') and wizard.get('sala').isdigit() else None
                        }
                        
                        print(f"[DEBUG] Criando cronograma: {cronograma_data}")
                        cronograma_response = requests.post(
                            f"{API_BASE_URL}/cronograma/",
                            json=cronograma_data,
                            headers=headers,
                            timeout=10
                        )
                        
                        if cronograma_response.status_code not in [200, 201]:
                            print(f"[WARN] Erro ao criar cronograma: {cronograma_response.text}")
                        else:
                            print(f"[DEBUG] Cronograma criado com sucesso")
                    except Exception as e:
                        print(f"[WARN] Erro ao criar cronograma: {e}")
                
                # 4. Criar avaliações na API
                for tipo_prova, dados_prova in wizard.get('provas', {}).items():
                    if dados_prova.get('data'):
                        try:
                            # Buscar ID do aplicador pelo nome
                            id_aplicador = None
                            if dados_prova.get('aplicador'):
                                professores_response = requests.get(
                                    f"{API_BASE_URL}/professores/lista_professores/",
                                    headers=headers,
                                    timeout=10
                                )
                                if professores_response.status_code == 200:
                                    professores_list = professores_response.json()
                                    for prof in professores_list:
                                        nome_completo = f"{prof.get('nome_professor', '')} {prof.get('sobrenome_professor', '')}".strip()
                                        if nome_completo == dados_prova.get('aplicador'):
                                            id_aplicador = prof.get('id_professor')
                                            break
                            
                            # Formatar hora para HH:MM:SS se necessário
                            hora_inicio_av = dados_prova.get('inicio', '')
                            if hora_inicio_av and len(hora_inicio_av) == 5:  # HH:MM
                                hora_inicio_av = f"{hora_inicio_av}:00"
                            hora_fim_av = dados_prova.get('fim', '')
                            if hora_fim_av and len(hora_fim_av) == 5:  # HH:MM
                                hora_fim_av = f"{hora_fim_av}:00"
                            
                            avaliacao_data = {
                                'tipo_avaliacao': tipo_prova.upper(),
                                'data_prova': dados_prova.get('data', ''),
                                'hora_inicio': hora_inicio_av if hora_inicio_av else None,
                                'hora_fim': hora_fim_av if hora_fim_av else None,
                                'sala': dados_prova.get('sala', '') if dados_prova.get('sala') else None,
                                'conteudo': dados_prova.get('conteudo', '') if dados_prova.get('conteudo') else None,
                                'id_disciplina': str(disciplina_id),
                                'id_aplicador': str(id_aplicador) if id_aplicador else None
                            }
                            
                            print(f"[DEBUG] Criando avaliação {tipo_prova}: {avaliacao_data}")
                            avaliacao_response = requests.post(
                                f"{API_BASE_URL}/avaliacao/",
                                json=avaliacao_data,
                                headers=headers,
                                timeout=10
                            )
                            
                            if avaliacao_response.status_code not in [200, 201]:
                                print(f"[WARN] Erro ao criar avaliação {tipo_prova}: {avaliacao_response.text}")
                            else:
                                print(f"[DEBUG] Avaliação {tipo_prova} criada com sucesso")
                        except Exception as e:
                            print(f"[WARN] Erro ao criar avaliação {tipo_prova}: {e}")
                
                # 5. Upload do arquivo de ementa se houver
                if request.files.get('ementa_arquivo'):
                    arquivo = request.files.get('ementa_arquivo')
                    if arquivo.filename:
                        try:
                            # Usar a função de upload por categoria
                            sucesso, mensagem = upload_documento_por_categoria(
                                arquivo,
                                'disciplina',
                                nome_disciplina=wizard.get('nome')
                            )
                            if sucesso:
                                print(f"[DEBUG] Arquivo de ementa enviado com sucesso")
                            else:
                                print(f"[WARN] Erro ao enviar arquivo de ementa: {mensagem}")
                        except Exception as e:
                            print(f"[WARN] Erro ao enviar arquivo de ementa: {e}")
                
                clear_wizard_state()
                flash('Matéria cadastrada com sucesso na API!', 'success')
                return redirect(url_for('calendario_view', materia_id=str(disciplina_id)))
                
            except Exception as e:
                print(f"[ERROR] Erro ao salvar na API: {e}")
                import traceback
                traceback.print_exc()
                flash(f'Erro ao salvar matéria na API: {str(e)}', 'error')
                # Mantém o wizard para o usuário poder tentar novamente
                return redirect(url_for('calendario_add', step=4))

    return render_template('calendario/add.html', step=step, wizard=wizard, user=session.get('user', {}), professores=professores)

@app.route('/calendario/view/<materia_id>')
@login_required
def calendario_view(materia_id):
    """Visualiza detalhes de uma disciplina específica"""
    materia = None
    try:
        headers = get_auth_headers()
        # A API tem um bug: a URL usa {disciplina} mas o parâmetro da função é disciplina_id
        # Por isso precisamos passar também como query parameter
        url = f"{API_BASE_URL}/disciplinas/get_diciplina_id/{materia_id}?disciplina_id={materia_id}"
        print(f"[DEBUG] Buscando disciplina: {url}")
        print(f"[DEBUG] Materia ID recebido: {materia_id} (tipo: {type(materia_id)})")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"[DEBUG] Status Code: {response.status_code}")
        print(f"[DEBUG] Response: {response.text[:200] if response.text else 'Sem resposta'}")
        
        if response.status_code == 200:
            disc = response.json()
            print(f"[DEBUG] Disciplina encontrada: {disc.get('nome_disciplina', 'N/A')}")
            
            # Busca o cronograma da disciplina
            cronograma_data = None
            try:
                cronograma_response = requests.get(
                    f"{API_BASE_URL}/cronograma/disciplina/{materia_id}",
                    headers=headers,
                    timeout=10
                )
                if cronograma_response.status_code == 200:
                    cronogramas = cronograma_response.json()
                    # Pega o primeiro cronograma se houver
                    if cronogramas and len(cronogramas) > 0:
                        cronograma_data = cronogramas[0]
                        print(f"[DEBUG] Cronograma encontrado: {cronograma_data.get('dia_semana', 'N/A')}")
            except Exception as e:
                print(f"[WARN] Erro ao buscar cronograma: {e}")
            
            # Busca as avaliações da disciplina
            avaliacoes_data = []
            provas_dict = {}
            try:
                avaliacoes_response = requests.get(
                    f"{API_BASE_URL}/avaliacao/disciplina/{materia_id}",
                    headers=headers,
                    timeout=10
                )
                if avaliacoes_response.status_code == 200:
                    avaliacoes_data = avaliacoes_response.json()
                    print(f"[DEBUG] {len(avaliacoes_data)} avaliações encontradas")
                    
                    # Transforma as avaliações da API para o formato esperado pelo template
                    for avaliacao in avaliacoes_data:
                        tipo = avaliacao.get('tipo_avaliacao', '').lower()
                        if tipo:
                            # Formata data de "YYYY-MM-DD" para "DD/MM/YYYY"
                            data_prova = avaliacao.get('data_prova', '')
                            if data_prova:
                                try:
                                    from datetime import datetime
                                    dt = datetime.strptime(data_prova, '%Y-%m-%d')
                                    data_formatada = dt.strftime('%d/%m/%Y')
                                except:
                                    data_formatada = data_prova
                            else:
                                data_formatada = ''
                            
                            # Formata hora de "HH:MM:SS" para "HH:MM"
                            hora_inicio = avaliacao.get('hora_inicio', '')
                            hora_inicio_formatada = hora_inicio[:5] if hora_inicio and ':' in hora_inicio else hora_inicio
                            
                            # Busca o nome do aplicador se houver id_aplicador
                            nome_aplicador = 'N/A'
                            if avaliacao.get('id_aplicador'):
                                try:
                                    # Tenta buscar o nome do professor/aplicador
                                    aplicador_id = avaliacao.get('id_aplicador')
                                    aplicador_response = requests.get(
                                        f"{API_BASE_URL}/professores/get_professor_id/{aplicador_id}",
                                        headers=headers,
                                        timeout=5
                                    )
                                    if aplicador_response.status_code == 200:
                                        aplicador_data = aplicador_response.json()
                                        nome_aplicador = f"{aplicador_data.get('nome_professor', '')} {aplicador_data.get('sobrenome_professor', '')}".strip()
                                        if not nome_aplicador:
                                            nome_aplicador = 'N/A'
                                except Exception as e:
                                    print(f"[WARN] Erro ao buscar nome do aplicador: {e}")
                            
                            provas_dict[tipo] = {
                                'data': data_formatada,
                                'inicio': hora_inicio_formatada,
                                'fim': avaliacao.get('hora_fim', '')[:5] if avaliacao.get('hora_fim') else '',
                                'sala': str(avaliacao.get('sala', '')) if avaliacao.get('sala') else '',
                                'aplicador': nome_aplicador,
                                'conteudo': avaliacao.get('conteudo', '')
                            }
            except Exception as e:
                print(f"[WARN] Erro ao buscar avaliações: {e}")
                import traceback
                traceback.print_exc()
            
            # Mapeia dia da semana de número para nome
            dias_semana = {
                1: 'Segunda-feira',
                2: 'Terça-feira',
                3: 'Quarta-feira',
                4: 'Quinta-feira',
                5: 'Sexta-feira',
                6: 'Sábado',
                7: 'Domingo'
            }
            
            # Formata hora de "HH:MM:SS" para "HH:MM"
            def formatar_hora(hora_str):
                if not hora_str:
                    return None
                if isinstance(hora_str, str) and ':' in hora_str:
                    return hora_str[:5]  # Pega apenas HH:MM
                return hora_str
            
            # Transforma os dados da API para o formato esperado pelo template
            ementa = disc.get('ementa', '') or ''
            materia = {
                'id': str(disc.get('id_disciplina', '')),
                'nome': disc.get('nome_disciplina', 'N/A'),
                'codigo': disc.get('codigo', 'N/A'),
                'semestre': disc.get('semestre', 'N/A'),
                'carga_horaria': disc.get('carga_horaria', 0),
                'ementa': ementa,
                'ementa_resumo': ementa,  # O resumo é a própria ementa da API
                'professor': 'N/A',
                'modalidade': disc.get('semestre', 'N/A'),  # Usa semestre como modalidade
                'ementa_arquivo_nome': None,  # Não há arquivo de ementa na API atual
                # Dados do cronograma
                'dia_semana': dias_semana.get(cronograma_data.get('dia_semana')) if cronograma_data and cronograma_data.get('dia_semana') else None,
                'hora_inicio': formatar_hora(cronograma_data.get('hora_inicio')) if cronograma_data else None,
                'hora_fim': formatar_hora(cronograma_data.get('hora_fim')) if cronograma_data else None,
                'sala': cronograma_data.get('sala') if cronograma_data else None,
                'bloco': cronograma_data.get('bloco') if cronograma_data else None,
                'tipo_aula': cronograma_data.get('tipo_aula') if cronograma_data else None,
                'provas': provas_dict  # Avaliações da API
            }
            
            # Se houver professores associados
            if disc.get('professores') and len(disc.get('professores', [])) > 0:
                prof = disc['professores'][0]
                nome_prof = f"{prof.get('nome_professor', '')} {prof.get('sobrenome_professor', '')}".strip()
                if nome_prof:
                    materia['professor'] = nome_prof
            
            print(f"[DEBUG] Dados do cronograma mapeados: dia={materia['dia_semana']}, hora_inicio={materia['hora_inicio']}, sala={materia['sala']}")
        elif response.status_code == 404:
            error_detail = response.json().get('detail', 'Disciplina não encontrada') if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"[ERROR] Disciplina não encontrada: {error_detail}")
            flash(f"Disciplina não encontrada: {error_detail}", "error")
            return redirect(url_for('calendario_list'))
        else:
            error_detail = response.json().get('detail', f'Erro {response.status_code}') if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"[ERROR] Erro ao buscar disciplina: {response.status_code} - {error_detail}")
            flash(f"Erro ao carregar disciplina: {error_detail}", "error")
            return redirect(url_for('calendario_list'))
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erro de conexão ao buscar disciplina: {e}")
        flash("Erro de conexão ao carregar dados da disciplina.", "error")
        return redirect(url_for('calendario_list'))
    except Exception as e:
        print(f"[ERROR] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        flash("Erro ao carregar dados da disciplina.", "error")
        return redirect(url_for('calendario_list'))
    
    if not materia:
        flash('Matéria não encontrada.', 'error')
        return redirect(url_for('calendario_list'))
    
    return render_template('calendario/view.html', materia=materia, user=session.get('user', {}))

@app.route('/calendario/edit/<materia_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor', 'coordenador'])
def calendario_edit(materia_id):
    # Buscar dados da API
    headers = get_auth_headers()
    materia = None
    
    try:
        # Buscar disciplina da API
        url = f"{API_BASE_URL}/disciplinas/get_diciplina_id/{materia_id}?disciplina_id={materia_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            disc = response.json()
            
            # Buscar cronograma
            cronograma_data = None
            try:
                cronograma_response = requests.get(
                    f"{API_BASE_URL}/cronograma/disciplina/{materia_id}",
                    headers=headers,
                    timeout=10
                )
                if cronograma_response.status_code == 200:
                    cronogramas = cronograma_response.json()
                    if cronogramas and len(cronogramas) > 0:
                        cronograma_data = cronogramas[0]
            except Exception as e:
                print(f"[WARN] Erro ao buscar cronograma: {e}")
            
            # Buscar avaliações
            provas_dict = {}
            try:
                avaliacoes_response = requests.get(
                    f"{API_BASE_URL}/avaliacao/disciplina/{materia_id}",
                    headers=headers,
                    timeout=10
                )
                if avaliacoes_response.status_code == 200:
                    avaliacoes_data = avaliacoes_response.json()
                    for avaliacao in avaliacoes_data:
                        tipo = avaliacao.get('tipo_avaliacao', '').lower()
                        if tipo:
                            # Formata data de "YYYY-MM-DD" para formato do input date
                            data_prova = avaliacao.get('data_prova', '')
                            
                            # Formata hora de "HH:MM:SS" para "HH:MM"
                            hora_inicio = avaliacao.get('hora_inicio', '')
                            hora_inicio_formatada = hora_inicio[:5] if hora_inicio and ':' in hora_inicio else hora_inicio
                            hora_fim = avaliacao.get('hora_fim', '')
                            hora_fim_formatada = hora_fim[:5] if hora_fim and ':' in hora_fim else hora_fim
                            
                            # Busca nome do aplicador
                            nome_aplicador = 'N/A'
                            if avaliacao.get('id_aplicador'):
                                try:
                                    aplicador_id = avaliacao.get('id_aplicador')
                                    aplicador_response = requests.get(
                                        f"{API_BASE_URL}/professores/get_professor_id/{aplicador_id}",
                                        headers=headers,
                                        timeout=5
                                    )
                                    if aplicador_response.status_code == 200:
                                        aplicador_data = aplicador_response.json()
                                        nome_aplicador = f"{aplicador_data.get('nome_professor', '')} {aplicador_data.get('sobrenome_professor', '')}".strip()
                                except Exception as e:
                                    print(f"[WARN] Erro ao buscar nome do aplicador: {e}")
                            
                            provas_dict[tipo] = {
                                'data': data_prova,
                                'inicio': hora_inicio_formatada,
                                'fim': hora_fim_formatada,
                                'sala': str(avaliacao.get('sala', '')) if avaliacao.get('sala') else '',
                                'aplicador': nome_aplicador,
                                'conteudo': avaliacao.get('conteudo', '')
                            }
            except Exception as e:
                print(f"[WARN] Erro ao buscar avaliações: {e}")
            
            # Mapear dia da semana de número para nome
            dias_semana_reverse = {
                1: 'segunda-feira',
                2: 'terça-feira',
                3: 'quarta-feira',
                4: 'quinta-feira',
                5: 'sexta-feira',
                6: 'sábado',
                7: 'domingo'
            }
            
            # Formatar hora de "HH:MM:SS" para "HH:MM"
            def formatar_hora_edit(hora_str):
                if not hora_str:
                    return None
                if isinstance(hora_str, str) and ':' in hora_str:
                    return hora_str[:5]  # Pega apenas HH:MM
                return hora_str
            
            # Buscar nome do professor
            nome_professor = 'N/A'
            if disc.get('professores') and len(disc.get('professores', [])) > 0:
                prof = disc['professores'][0]
                nome_professor = f"{prof.get('nome_professor', '')} {prof.get('sobrenome_professor', '')}".strip()
            
            # Montar objeto materia com dados da API
            materia = {
                'id': str(disc.get('id_disciplina', '')),
                'nome': disc.get('nome_disciplina', ''),
                'codigo': disc.get('codigo', ''),
                'carga_horaria': f"{disc.get('carga_horaria', 0)}h",
                'modalidade': disc.get('semestre', ''),
                'professor': nome_professor,
                'ementa_resumo': disc.get('ementa', ''),
                'ementa_arquivo_nome': None,
                'dia_semana': dias_semana_reverse.get(cronograma_data.get('dia_semana')) if cronograma_data and cronograma_data.get('dia_semana') else '',
                'hora_inicio': formatar_hora_edit(cronograma_data.get('hora_inicio')) if cronograma_data else '',
                'hora_fim': formatar_hora_edit(cronograma_data.get('hora_fim')) if cronograma_data else '',
                'sala': str(cronograma_data.get('sala', '')) if cronograma_data and cronograma_data.get('sala') else '',
                'provas': provas_dict
            }
        else:
            flash('Matéria não encontrada na API.', 'error')
            return redirect(url_for('calendario_list'))
    except Exception as e:
        print(f"[ERROR] Erro ao buscar dados da API: {e}")
        flash('Erro ao carregar dados da matéria.', 'error')
        return redirect(url_for('calendario_list'))

    if not materia:
        flash('Matéria não encontrada.', 'error')
        return redirect(url_for('calendario_list'))

    # Buscar professores da API para popular selects
    professores = []
    try:
        response = requests.get(f"{API_BASE_URL}/professores/lista_professores/", headers=headers, timeout=10)
        if response.status_code == 200:
            professores = response.json()
            # Formatar nome completo para exibição
            for prof in professores:
                nome = prof.get('nome_professor', '')
                sobrenome = prof.get('sobrenome_professor', '')
                prof['nome_completo'] = f"{nome} {sobrenome}".strip()
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar professores: {e}")
        professores = []

    step = int(request.args.get('step') or request.form.get('step') or 1)
    # Usa dados da API se não houver wizard na sessão, senão mantém o wizard
    if 'edit_wizard' not in session:
        wizard = materia.copy()
    else:
        wizard = session.get('edit_wizard', materia.copy())

    if request.method == 'POST':
        if step == 1:
            wizard.update({
                'nome': request.form.get('nome', '').strip(),
                'professor': request.form.get('professor', '').strip(),
                'codigo': request.form.get('codigo', '').strip(),
                'carga_horaria': request.form.get('carga_horaria', '').strip(),
                'modalidade': request.form.get('modalidade', '').strip(),
            })
            session.modified = True
            return redirect(url_for('calendario_edit', materia_id=materia_id, step=2))
        elif step == 2:
            wizard.update({
                'ementa_resumo': request.form.get('ementa_resumo', '').strip(),
                'ementa_arquivo_nome': (request.files.get('ementa_arquivo').filename if request.files.get('ementa_arquivo') and request.files.get('ementa_arquivo').filename else wizard.get('ementa_arquivo_nome', ''))
            })
            session.modified = True
            return redirect(url_for('calendario_edit', materia_id=materia_id, step=3))
        elif step == 3:
            wizard.update({
                'dia_semana': request.form.get('dia_semana', '').strip(),
                'hora_inicio': request.form.get('hora_inicio', '').strip(),
                'hora_fim': request.form.get('hora_fim', '').strip(),
                'sala': request.form.get('sala', '').strip(),
            })
            session.modified = True
            return redirect(url_for('calendario_edit', materia_id=materia_id, step=4))
        elif step == 4:
            provas = {
                'np1': {
                    'data': request.form.get('np1_data', '').strip(),
                    'inicio': request.form.get('np1_inicio', '').strip(),
                    'fim': request.form.get('np1_fim', '').strip(),
                    'sala': request.form.get('np1_sala', '').strip(),
                    'aplicador': request.form.get('np1_aplicador', '').strip(),
                    'conteudo': request.form.get('np1_conteudo', '').strip(),
                },
                'np2': {
                    'data': request.form.get('np2_data', '').strip(),
                    'inicio': request.form.get('np2_inicio', '').strip(),
                    'fim': request.form.get('np2_fim', '').strip(),
                    'sala': request.form.get('np2_sala', '').strip(),
                    'aplicador': request.form.get('np2_aplicador', '').strip(),
                    'conteudo': request.form.get('np2_conteudo', '').strip(),
                },
                'exame': {
                    'data': request.form.get('exame_data', '').strip(),
                    'inicio': request.form.get('exame_inicio', '').strip(),
                    'fim': request.form.get('exame_fim', '').strip(),
                    'sala': request.form.get('exame_sala', '').strip(),
                    'aplicador': request.form.get('exame_aplicador', '').strip(),
                    'conteudo': request.form.get('exame_conteudo', '').strip(),
                },
                'sub': {
                    'data': request.form.get('sub_data', '').strip(),
                    'inicio': request.form.get('sub_inicio', '').strip(),
                    'fim': request.form.get('sub_fim', '').strip(),
                    'sala': request.form.get('sub_sala', '').strip(),
                    'aplicador': request.form.get('sub_aplicador', '').strip(),
                    'conteudo': request.form.get('sub_conteudo', '').strip(),
                }
            }
            wizard['provas'] = provas

            # Atualizar na API
            try:
                headers = get_auth_headers()
                
                # 1. Atualizar disciplina na API
                # Mapear dia da semana de nome para número
                dias_semana_map = {
                    'segunda-feira': 1,
                    'terça-feira': 2,
                    'quarta-feira': 3,
                    'quinta-feira': 4,
                    'sexta-feira': 5,
                    'sábado': 6,
                    'domingo': 7
                }
                
                # Preparar dados da disciplina para atualização
                disciplina_update = {
                    'nome_disciplina': wizard.get('nome', ''),
                    'codigo': wizard.get('codigo', ''),
                    'semestre': wizard.get('modalidade', ''),  # Usando modalidade como semestre temporariamente
                    'ementa': wizard.get('ementa_resumo', ''),
                    'carga_horaria': int(wizard.get('carga_horaria', '0').replace('h', '').replace('H', '').strip()) if wizard.get('carga_horaria') else None
                }
                
                # Remove campos None para não enviar
                disciplina_update = {k: v for k, v in disciplina_update.items() if v is not None}
                
                print(f"[DEBUG] Atualizando disciplina {materia_id}: {disciplina_update}")
                disciplina_response = requests.put(
                    f"{API_BASE_URL}/disciplinas/update/{materia_id}",
                    json=disciplina_update,
                    headers=headers,
                    timeout=10
                )
                
                if disciplina_response.status_code not in [200, 201]:
                    error_detail = disciplina_response.json().get('detail', f'Erro {disciplina_response.status_code}') if disciplina_response.headers.get('content-type', '').startswith('application/json') else disciplina_response.text
                    raise Exception(f"Erro ao atualizar disciplina: {error_detail}")
                
                print(f"[DEBUG] Disciplina atualizada com sucesso")
                
                # 2. Atualizar associação do professor (se mudou)
                if wizard.get('professor'):
                    # Buscar ID do professor pelo nome
                    professores_response = requests.get(
                        f"{API_BASE_URL}/professores/lista_professores/",
                        headers=headers,
                        timeout=10
                    )
                    if professores_response.status_code == 200:
                        professores_list = professores_response.json()
                        for prof in professores_list:
                            nome_completo = f"{prof.get('nome_professor', '')} {prof.get('sobrenome_professor', '')}".strip()
                            if nome_completo == wizard.get('professor'):
                                professor_id = prof.get('id_professor')
                                # Buscar disciplinas atuais do professor
                                try:
                                    prof_response = requests.get(
                                        f"{API_BASE_URL}/professores/get_professor_id/{professor_id}",
                                        headers=headers,
                                        timeout=10
                                    )
                                    if prof_response.status_code == 200:
                                        prof_data = prof_response.json()
                                        disciplinas_atual = prof_data.get('disciplina_nomes', [])
                                        # Se a disciplina não está na lista, adiciona
                                        if wizard.get('nome') not in disciplinas_atual:
                                            disciplinas_atual.append(wizard.get('nome'))
                                        
                                        # Atualizar professor com disciplinas
                                        update_response = requests.put(
                                            f"{API_BASE_URL}/professores/update/{professor_id}",
                                            json={'disciplina_nomes': disciplinas_atual},
                                            headers=headers,
                                            timeout=10
                                        )
                                        if update_response.status_code == 200:
                                            print(f"[DEBUG] Professor atualizado com sucesso")
                                except Exception as e:
                                    print(f"[WARN] Erro ao atualizar professor: {e}")
                                break
                
                # 3. Buscar cronograma existente e atualizar ou criar
                try:
                    cronograma_response = requests.get(
                        f"{API_BASE_URL}/cronograma/disciplina/{materia_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if cronograma_response.status_code == 200:
                        cronogramas = cronograma_response.json()
                        
                        if wizard.get('dia_semana') and wizard.get('hora_inicio') and wizard.get('hora_fim'):
                            # Formatar hora para HH:MM:SS se necessário
                            hora_inicio = wizard.get('hora_inicio', '')
                            if hora_inicio and len(hora_inicio) == 5:  # HH:MM
                                hora_inicio = f"{hora_inicio}:00"
                            hora_fim = wizard.get('hora_fim', '')
                            if hora_fim and len(hora_fim) == 5:  # HH:MM
                                hora_fim = f"{hora_fim}:00"
                            
                            dia_num = dias_semana_map.get(wizard.get('dia_semana', '').lower())
                            
                            if cronogramas and len(cronogramas) > 0:
                                # Atualizar cronograma existente
                                cronograma_id = cronogramas[0].get('id_cronograma')
                                cronograma_update = {
                                    'nome_disciplina': wizard.get('nome', ''),
                                    'dia_semana': dia_num,
                                    'hora_inicio': hora_inicio,
                                    'hora_fim': hora_fim,
                                    'sala': int(wizard.get('sala', 0)) if wizard.get('sala') and wizard.get('sala').isdigit() else None
                                }
                                
                                print(f"[DEBUG] Atualizando cronograma {cronograma_id}: {cronograma_update}")
                                update_response = requests.put(
                                    f"{API_BASE_URL}/cronograma/updade/{cronograma_id}",
                                    json=cronograma_update,
                                    headers=headers,
                                    timeout=10
                                )
                                
                                if update_response.status_code not in [200, 201]:
                                    print(f"[WARN] Erro ao atualizar cronograma: {update_response.text}")
                                else:
                                    print(f"[DEBUG] Cronograma atualizado com sucesso")
                            else:
                                # Criar novo cronograma
                                cronograma_data = {
                                    'nome_disciplina': wizard.get('nome', ''),
                                    'hora_inicio': hora_inicio,
                                    'hora_fim': hora_fim,
                                    'periodicidade': 'semanal',
                                    'id_disciplina': str(materia_id),
                                    'dia_semana': dia_num,
                                    'sala': int(wizard.get('sala', 0)) if wizard.get('sala') and wizard.get('sala').isdigit() else None
                                }
                                
                                print(f"[DEBUG] Criando novo cronograma: {cronograma_data}")
                                create_response = requests.post(
                                    f"{API_BASE_URL}/cronograma/",
                                    json=cronograma_data,
                                    headers=headers,
                                    timeout=10
                                )
                                
                                if create_response.status_code not in [200, 201]:
                                    print(f"[WARN] Erro ao criar cronograma: {create_response.text}")
                                else:
                                    print(f"[DEBUG] Cronograma criado com sucesso")
                except Exception as e:
                    print(f"[WARN] Erro ao atualizar/criar cronograma: {e}")
                
                # 4. Atualizar avaliações na API
                for tipo_prova, dados_prova in wizard.get('provas', {}).items():
                    try:
                        # Formatar hora para HH:MM:SS se necessário
                        hora_inicio_av = dados_prova.get('inicio', '')
                        if hora_inicio_av and len(hora_inicio_av) == 5:  # HH:MM
                            hora_inicio_av = f"{hora_inicio_av}:00"
                        hora_fim_av = dados_prova.get('fim', '')
                        if hora_fim_av and len(hora_fim_av) == 5:  # HH:MM
                            hora_fim_av = f"{hora_fim_av}:00"
                        
                        # Buscar ID do aplicador pelo nome
                        id_aplicador = None
                        if dados_prova.get('aplicador'):
                            professores_response = requests.get(
                                f"{API_BASE_URL}/professores/lista_professores/",
                                headers=headers,
                                timeout=10
                            )
                            if professores_response.status_code == 200:
                                professores_list = professores_response.json()
                                for prof in professores_list:
                                    nome_completo = f"{prof.get('nome_professor', '')} {prof.get('sobrenome_professor', '')}".strip()
                                    if nome_completo == dados_prova.get('aplicador'):
                                        id_aplicador = prof.get('id_professor')
                                        break
                        
                        avaliacao_update = {
                            'data_prova': dados_prova.get('data', '') if dados_prova.get('data') else None,
                            'hora_inicio': hora_inicio_av if hora_inicio_av else None,
                            'hora_fim': hora_fim_av if hora_fim_av else None,
                            'sala': dados_prova.get('sala', '') if dados_prova.get('sala') else None,
                            'conteudo': dados_prova.get('conteudo', '') if dados_prova.get('conteudo') else None,
                            'id_aplicador': str(id_aplicador) if id_aplicador else None
                        }
                        
                        # Remove campos None
                        avaliacao_update = {k: v for k, v in avaliacao_update.items() if v is not None}
                        
                        if dados_prova.get('data'):
                            # Atualizar avaliação existente ou criar nova
                            print(f"[DEBUG] Atualizando avaliação {tipo_prova}: {avaliacao_update}")
                            update_response = requests.put(
                                f"{API_BASE_URL}/avaliacao/disciplina/{materia_id}/tipo/{tipo_prova}",
                                json=avaliacao_update,
                                headers=headers,
                                timeout=10
                            )
                            
                            if update_response.status_code == 404:
                                # Avaliação não existe, criar nova
                                avaliacao_create = avaliacao_update.copy()
                                avaliacao_create['tipo_avaliacao'] = tipo_prova.upper()
                                avaliacao_create['id_disciplina'] = str(materia_id)
                                
                                print(f"[DEBUG] Criando nova avaliação {tipo_prova}: {avaliacao_create}")
                                create_response = requests.post(
                                    f"{API_BASE_URL}/avaliacao/",
                                    json=avaliacao_create,
                                    headers=headers,
                                    timeout=10
                                )
                                
                                if create_response.status_code not in [200, 201]:
                                    print(f"[WARN] Erro ao criar avaliação {tipo_prova}: {create_response.text}")
                                else:
                                    print(f"[DEBUG] Avaliação {tipo_prova} criada com sucesso")
                            elif update_response.status_code not in [200, 201]:
                                print(f"[WARN] Erro ao atualizar avaliação {tipo_prova}: {update_response.text}")
                            else:
                                print(f"[DEBUG] Avaliação {tipo_prova} atualizada com sucesso")
                    except Exception as e:
                        print(f"[WARN] Erro ao atualizar avaliação {tipo_prova}: {e}")
                
                # 5. Upload do arquivo de ementa se houver novo arquivo
                if request.files.get('ementa_arquivo'):
                    arquivo = request.files.get('ementa_arquivo')
                    if arquivo.filename:
                        try:
                            sucesso, mensagem = upload_documento_por_categoria(
                                arquivo,
                                'disciplina',
                                nome_disciplina=wizard.get('nome')
                            )
                            if sucesso:
                                print(f"[DEBUG] Arquivo de ementa enviado com sucesso")
                            else:
                                print(f"[WARN] Erro ao enviar arquivo de ementa: {mensagem}")
                        except Exception as e:
                            print(f"[WARN] Erro ao enviar arquivo de ementa: {e}")
                
                session.pop('edit_wizard', None)
                flash('Matéria atualizada com sucesso na API!', 'success')
                return redirect(url_for('calendario_view', materia_id=materia_id))
                
            except Exception as e:
                print(f"[ERROR] Erro ao atualizar na API: {e}")
                import traceback
                traceback.print_exc()
                flash(f'Erro ao atualizar matéria na API: {str(e)}', 'error')
                # Mantém o wizard para o usuário poder tentar novamente
                return redirect(url_for('calendario_edit', materia_id=materia_id, step=4))

    return render_template('calendario/edit.html', step=step, wizard=wizard, materia_id=materia_id, user=session.get('user', {}), professores=professores)

@app.route('/calendario/delete/<materia_id>', methods=['POST'])
@login_required
@role_required(['admin', 'professor', 'coordenador'])
def calendario_delete(materia_id):
    """ Remove disciplina da API """
    try:
        headers = get_auth_headers()
        response = requests.delete(
            f"{API_BASE_URL}/disciplinas/delete/{materia_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 204:
            flash('Matéria removida com sucesso!', 'success')
        elif response.status_code == 404:
            flash('Matéria não encontrada.', 'error')
        else:
            error_detail = response.json().get('detail', f'Erro {response.status_code}') if response.headers.get('content-type', '').startswith('application/json') else response.text
            flash(f'Erro ao remover matéria: {error_detail}', 'error')
            print(f"[ERROR] Erro ao deletar disciplina: {response.status_code} - {error_detail}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erro de conexão ao deletar disciplina: {e}")
        flash('Erro de conexão ao remover matéria.', 'error')
    except Exception as e:
        print(f"[ERROR] Erro inesperado ao remover matéria: {e}")
        flash('Erro ao remover matéria.', 'error')
    
    return redirect(url_for('calendario_list'))

# ===== ROTAS DE INFORMAÇÕES DO CURSO =====

@app.route('/infos-curso')
@login_required
def infos_curso_list():
    """ Lista informações do curso """
    return render_template('infos_curso/list.html', user=session.get('user', {}))

@app.route('/infos-curso/add', methods=['GET', 'POST'])
@login_required
def infos_curso_add():
    """ Adicionar nova informação do curso """
    if request.method == 'POST':
        tipo = request.form.get('tipo')

        if tipo == 'APS':
            session['add_info_type'] = 'APS'
            return redirect(url_for('infos_curso_add_aps'))
        elif tipo == 'TCC':
            session['add_info_type'] = 'TCC'
            session['tcc_step'] = 1
            return redirect(url_for('infos_curso_add_tcc'))
        elif tipo == 'Estagio':
            session['add_info_type'] = 'Estagio'
            session['estagio_step'] = 1
            return redirect(url_for('infos_curso_add_estagio'))
        elif tipo == 'Horas Complementares':
            session['add_info_type'] = 'Horas Complementares'
            return redirect(url_for('infos_curso_add_horas'))

    return render_template('infos_curso/add_select.html', user=session.get('user', {}))

@app.route('/infos-curso/add/aps', methods=['GET', 'POST'])
@login_required
def infos_curso_add_aps():
    """ Formulário para adicionar APS """
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            semestre = request.form.get('semestre')
            data_limite = request.form.get('data_limite')
            tema = request.form.get('tema')
            max_integrantes = request.form.get('max_integrantes')
            file_storage = request.files.get('documento')
            
            # Fazer upload do documento se houver
            if file_storage and file_storage.filename:
                # Buscar nome do curso (pode vir da sessão ou ser fixo)
                nome_curso = request.form.get('nome_curso', 'Curso Padrão')  # Ajustar conforme necessário
                
                success, result = upload_documento_por_categoria(
                    file_storage, 
                    'aps',
                    tipo='aps',
                    nome_curso=nome_curso,
                    data=data_limite or '2025-12-31'  # Data padrão se não fornecida
                )
                
                if not success:
                    flash(f'Erro ao fazer upload do documento: {result}', 'error')
                    return redirect(url_for('infos_curso_add_aps'))
            
            # Aqui você pode salvar os outros dados (semestre, tema, etc.) na API se necessário
            flash('APS adicionada com sucesso!', 'success')
            session.pop('add_info_type', None)
            return redirect(url_for('infos_curso_list'))
        except Exception as e:
            flash(f'Erro ao processar formulário: {str(e)}', 'error')
            return redirect(url_for('infos_curso_add_aps'))

    return render_template('infos_curso/add_aps.html', user=session.get('user', {}))

@app.route('/infos-curso/add/tcc', methods=['GET', 'POST'])
@login_required
def infos_curso_add_tcc():
    """ Formulário multi-etapas para adicionar TCC """
    step = session.get('tcc_step', 1)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'next' and step < 3:
            session['tcc_step'] = step + 1
        elif action == 'back' and step > 1:
            session['tcc_step'] = step - 1
        elif action == 'save':
            # Salvar dados do TCC
            try:
                # Obter dados do formulário
                file_storage = request.files.get('manual_tcc')
                
                # Fazer upload do documento se houver
                if file_storage and file_storage.filename:
                    # Buscar nome do curso (pode vir da sessão ou ser fixo)
                    nome_curso = request.form.get('nome_curso', 'Curso Padrão')  # Ajustar conforme necessário
                    data_entrega = request.form.get('entrega_final', '2025-12-31')
                    
                    success, result = upload_documento_por_categoria(
                        file_storage,
                        'tcc',
                        tipo='tcc',
                        nome_curso=nome_curso,
                        data=data_entrega
                    )
                    
                    if not success:
                        flash(f'Erro ao fazer upload do documento: {result}', 'error')
                        return redirect(url_for('infos_curso_add_tcc'))
                
                # Aqui você pode salvar os outros dados do TCC na API se necessário
                flash('TCC adicionado com sucesso!', 'success')
                session.pop('tcc_step', None)
                session.pop('add_info_type', None)
                return redirect(url_for('infos_curso_list'))
            except Exception as e:
                flash(f'Erro ao processar formulário: {str(e)}', 'error')
                return redirect(url_for('infos_curso_add_tcc'))

        return redirect(url_for('infos_curso_add_tcc'))

    return render_template('infos_curso/add_tcc.html', step=session.get('tcc_step', 1), user=session.get('user', {}))

@app.route('/infos-curso/add/estagio', methods=['GET', 'POST'])
@login_required
def infos_curso_add_estagio():
    """ Formulário multi-etapas para adicionar Estágio """
    step = session.get('estagio_step', 1)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'next' and step < 2:
            session['estagio_step'] = step + 1
        elif action == 'back' and step > 1:
            session['estagio_step'] = step - 1
        elif action == 'save':
            # Salvar dados do Estágio
            try:
                # Obter dados do formulário (arquivo está na etapa 1)
                # Se o arquivo foi enviado na etapa 1, ele deve estar na sessão
                # Por enquanto, vamos processar se houver arquivo na etapa atual
                file_storage = request.files.get('kit_estudante')
                
                # Fazer upload do documento se houver
                if file_storage and file_storage.filename:
                    nome_curso = request.form.get('nome_curso', 'Curso Padrão')  # Ajustar conforme necessário
                    # Pegar a primeira data de entrega se houver
                    datas = request.form.getlist('data[]')
                    data_entrega = datas[0] if datas else '2025-12-31'
                    
                    success, result = upload_documento_por_categoria(
                        file_storage,
                        'estagio',
                        tipo='estagio',
                        nome_curso=nome_curso,
                        data=data_entrega
                    )
                    
                    if not success:
                        flash(f'Erro ao fazer upload do documento: {result}', 'error')
                        return redirect(url_for('infos_curso_add_estagio'))
                
                # Aqui você pode salvar os outros dados do Estágio na API se necessário
                flash('Estágio adicionado com sucesso!', 'success')
                session.pop('estagio_step', None)
                session.pop('add_info_type', None)
                return redirect(url_for('infos_curso_list'))
            except Exception as e:
                flash(f'Erro ao processar formulário: {str(e)}', 'error')
                return redirect(url_for('infos_curso_add_estagio'))

        return redirect(url_for('infos_curso_add_estagio'))

    return render_template('infos_curso/add_estagio.html', step=session.get('estagio_step', 1), user=session.get('user', {}))

@app.route('/infos-curso/add/horas', methods=['GET', 'POST'])
@login_required
def infos_curso_add_horas():
    """ Formulário para adicionar Horas Complementares """
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            carga_horaria = request.form.get('carga_horaria')
            data_limite = request.form.get('data_limite')
            file_storage = request.files.get('kit_estudante')
            
            # Fazer upload do documento se houver
            if file_storage and file_storage.filename:
                nome_curso = request.form.get('nome_curso', 'Curso Padrão')  # Ajustar conforme necessário
                
                success, result = upload_documento_por_categoria(
                    file_storage,
                    'hora_complementares',
                    tipo='hora_complementares',
                    nome_curso=nome_curso,
                    data=data_limite or '2025-12-31'
                )
                
                if not success:
                    flash(f'Erro ao fazer upload do documento: {result}', 'error')
                    return redirect(url_for('infos_curso_add_horas'))
            
            # Aqui você pode salvar os outros dados (carga_horaria, categorias, etc.) na API se necessário
            flash('Horas Complementares adicionadas com sucesso!', 'success')
            session.pop('add_info_type', None)
            return redirect(url_for('infos_curso_list'))
        except Exception as e:
            flash(f'Erro ao processar formulário: {str(e)}', 'error')
            return redirect(url_for('infos_curso_add_horas'))

    return render_template('infos_curso/add_horas.html', user=session.get('user', {}))

# ===== ROTAS DE ALUNOS =====
@app.route('/alunos')
@login_required
def alunos_list():
    """ Lista alunos - busca da API """
    try:
        print(f"[DEBUG] Buscando alunos em: {API_BASE_URL}/alunos/get_list_alunos/")
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/alunos/get_list_alunos/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            alunos = response.json()
            print(f"[DEBUG] {len(alunos)} alunos encontrados")
            return jsonify(alunos), 200
        else:
            flash(f"Erro ao carregar alunos (Status {response.status_code})", "error")
            return jsonify([]), response.status_code
            
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar alunos: {e}")
        flash("Erro ao carregar alunos.", "error")
        return jsonify([]), 500

@app.route('/alunos/get_email/<email>')
@login_required
def alunos_get_by_email(email):
    """ Busca aluno por email """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/alunos/get_email/{email}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": "Aluno não encontrado"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE DISCIPLINAS =====
@app.route('/disciplinas')
@login_required
def disciplinas_list():
    """ Lista disciplinas - busca da API """
    try:
        print(f"[DEBUG] Buscando disciplinas em: {API_BASE_URL}/disciplinas/lista_disciplina/")
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/disciplinas/lista_disciplina/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            disciplinas = response.json()
            print(f"[DEBUG] {len(disciplinas)} disciplinas encontradas")
            return jsonify(disciplinas), 200
        else:
            return jsonify([]), response.status_code
            
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar disciplinas: {e}")
        return jsonify([]), 500

@app.route('/disciplinas/get/<disciplina_id>')
@login_required
def disciplinas_get(disciplina_id):
    """ Busca disciplina por ID """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/disciplinas/get_diciplina_id/{disciplina_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": "Disciplina não encontrada"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE CURSOS =====
@app.route('/cursos')
@login_required
def cursos_list():
    """ Lista cursos - busca da API """
    try:
        headers = get_auth_headers()
        # Nota: API pode não ter endpoint de lista, verificar
        response = requests.get(f"{API_BASE_URL}/curso/get_curso/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            cursos = response.json() if isinstance(response.json(), list) else [response.json()]
            return jsonify(cursos), 200
        return jsonify([]), response.status_code
            
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar cursos: {e}")
        return jsonify([]), 500

@app.route('/cursos/get/<curso_id>')
@login_required
def cursos_get(curso_id):
    """ Busca curso por ID """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/curso/get_curso/{curso_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": "Curso não encontrado"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE CRONOGRAMA =====
@app.route('/cronograma')
@login_required
def cronograma_list():
    """ Lista cronogramas - busca da API """
    try:
        headers = get_auth_headers()
        # Nota: API pode precisar de disciplina_id, verificar
        response = requests.get(f"{API_BASE_URL}/cronograma/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            cronogramas = response.json() if isinstance(response.json(), list) else [response.json()]
            return jsonify(cronogramas), 200
        return jsonify([]), response.status_code
            
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar cronograma: {e}")
        return jsonify([]), 500

@app.route('/cronograma/disciplina/<disciplina_id>')
@login_required
def cronograma_by_disciplina(disciplina_id):
    """ Busca cronograma por disciplina """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/cronograma/disciplina/{disciplina_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": "Cronograma não encontrado"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE COORDENADORES =====
@app.route('/coordenadores')
@login_required
def coordenadores_list():
    """ Lista coordenadores - busca da API """
    try:
        print(f"[DEBUG] Buscando coordenadores em: {API_BASE_URL}/coordenador/get_list_coordenador/")
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/coordenador/get_list_coordenador/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            coordenadores = response.json()
            print(f"[DEBUG] {len(coordenadores)} coordenadores encontrados")
            return jsonify(coordenadores), 200
        else:
            return jsonify([]), response.status_code
            
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Erro ao buscar coordenadores: {e}")
        return jsonify([]), 500

# ===== ROTAS DE AVALIAÇÃO =====
@app.route('/avaliacoes/disciplina/<disciplina_id>')
@login_required
def avaliacoes_by_disciplina(disciplina_id):
    """ Busca avaliações por disciplina """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/avaliacao/disciplina/{disciplina_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": "Avaliações não encontradas"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE TRABALHO ACADÊMICO =====
@app.route('/trabalho_academico', methods=['GET', 'POST'])
@login_required
def trabalho_academico_list_create():
    """ Lista trabalhos acadêmicos ou cria novo """
    if request.method == 'GET':
        try:
            headers = get_auth_headers()
            # Nota: API não tem endpoint de listagem geral, retorna vazio
            return jsonify([]), 200
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Erro ao buscar trabalhos acadêmicos: {e}")
            return jsonify([]), 500
    elif request.method == 'POST':
        try:
            headers = get_auth_headers()
            data = request.get_json() if request.is_json else request.form.to_dict()
            response = requests.post(f"{API_BASE_URL}/trabalho_academico/", json=data, headers=headers, timeout=10)
            if response.status_code == 201:
                return jsonify(response.json()), 201
            return jsonify({"error": response.json().get("detail", "Erro ao criar trabalho acadêmico")}), response.status_code
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e)}), 500

@app.route('/trabalho_academico/<trabalho_id>')
@login_required
def trabalho_academico_get(trabalho_id):
    """ Busca trabalho acadêmico por ID """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/trabalho_academico/{trabalho_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": "Trabalho acadêmico não encontrado"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trabalho_academico/curso/<curso_id>')
@login_required
def trabalho_academico_by_curso(curso_id):
    """ Lista trabalhos acadêmicos por curso """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/trabalho_academico/curso/{curso_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify([]), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trabalho_academico/disciplina/<disciplina_id>')
@login_required
def trabalho_academico_by_disciplina(disciplina_id):
    """ Lista trabalhos acadêmicos por disciplina """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/trabalho_academico/disciplina/{disciplina_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify([]), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trabalho_academico/update/<trabalho_id>', methods=['PUT'])
@login_required
def trabalho_academico_update(trabalho_id):
    """ Atualiza trabalho acadêmico """
    try:
        headers = get_auth_headers()
        data = request.get_json() if request.is_json else request.form.to_dict()
        response = requests.put(f"{API_BASE_URL}/trabalho_academico/update/{trabalho_id}", json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": response.json().get("detail", "Erro ao atualizar trabalho acadêmico")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trabalho_academico/delete/<trabalho_id>', methods=['DELETE'])
@login_required
def trabalho_academico_delete(trabalho_id):
    """ Deleta trabalho acadêmico """
    try:
        headers = get_auth_headers()
        response = requests.delete(f"{API_BASE_URL}/trabalho_academico/delete/{trabalho_id}", headers=headers, timeout=10)
        if response.status_code == 204:
            return jsonify({"message": "Trabalho acadêmico deletado com sucesso"}), 200
        return jsonify({"error": response.json().get("detail", "Erro ao deletar trabalho acadêmico")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE BASE DE CONHECIMENTO =====
@app.route('/baseconhecimento', methods=['GET', 'POST'])
@login_required
def base_conhecimento_list_create():
    """ Lista base de conhecimento ou cria novo """
    if request.method == 'GET':
        try:
            headers = get_auth_headers()
            query = request.args.get('q', '')
            if query:
                response = requests.get(f"{API_BASE_URL}/baseconhecimento/get_buscar?q={query}", headers=headers, timeout=10)
            else:
                # Se não houver query, retorna lista vazia
                return jsonify([]), 200
            if response.status_code == 200:
                resultados = response.json()
                return jsonify(resultados), 200
            return jsonify([]), response.status_code
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Erro ao buscar base de conhecimento: {e}")
            return jsonify([]), 500
    elif request.method == 'POST':
        try:
            headers = get_auth_headers()
            data = request.get_json() if request.is_json else request.form.to_dict()
            response = requests.post(f"{API_BASE_URL}/baseconhecimento/", json=data, headers=headers, timeout=10)
            if response.status_code == 201:
                return jsonify(response.json()), 201
            return jsonify({"error": response.json().get("detail", "Erro ao criar base de conhecimento")}), response.status_code
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e)}), 500

@app.route('/baseconhecimento/buscar')
@login_required
def base_conhecimento_buscar():
    """ Busca na base de conhecimento """
    try:
        headers = get_auth_headers()
        query = request.args.get('q', '')
        if not query or len(query) < 3:
            return jsonify({"error": "Query deve ter pelo menos 3 caracteres"}), 400
        response = requests.get(f"{API_BASE_URL}/baseconhecimento/get_buscar?q={query}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify([]), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/baseconhecimento/<item_id>')
@login_required
def base_conhecimento_get(item_id):
    """ Busca base de conhecimento por ID """
    try:
        headers = get_auth_headers()
        response = requests.get(f"{API_BASE_URL}/baseconhecimento/get_baseconhecimento_id/{item_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": "Item não encontrado"}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/baseconhecimento/update/<item_id>', methods=['PUT'])
@login_required
def base_conhecimento_update(item_id):
    """ Atualiza base de conhecimento """
    try:
        headers = get_auth_headers()
        data = request.get_json() if request.is_json else request.form.to_dict()
        response = requests.put(f"{API_BASE_URL}/baseconhecimento/update/{item_id}", json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": response.json().get("detail", "Erro ao atualizar base de conhecimento")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/baseconhecimento/delete/<item_id>', methods=['DELETE'])
@login_required
def base_conhecimento_delete(item_id):
    """ Deleta base de conhecimento """
    try:
        headers = get_auth_headers()
        response = requests.delete(f"{API_BASE_URL}/baseconhecimento/delete/{item_id}", headers=headers, timeout=10)
        if response.status_code == 204:
            return jsonify({"message": "Item deletado com sucesso"}), 200
        return jsonify({"error": response.json().get("detail", "Erro ao deletar item")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE DÚVIDAS FREQUENTES =====
@app.route('/duvidas-frequentes')
@login_required
def duvidas_frequentes_list():
    """ Lista dúvidas frequentes dos alunos (mensagens do chatbot) """
    try:
        headers = get_auth_headers()
        user = session.get('user', {})
        
        # Buscar mensagens dos alunos da API
        response = requests.get(
            f"{API_BASE_URL}/mensagens_aluno/get_lista_msg/",
            headers=headers,
            timeout=10
        )
        
        todas_mensagens = []
        if response.status_code == 200:
            mensagens_data = response.json()
            todas_mensagens = mensagens_data if isinstance(mensagens_data, list) else [mensagens_data]
        elif response.status_code == 404:
            todas_mensagens = []
        else:
            flash(f"Erro ao carregar dúvidas frequentes: {response.status_code}", "error")
            todas_mensagens = []
        
        # Separar por tópico/categoria
        duvidas_materia = []  # Disciplina, Conteúdo, etc.
        duvidas_institucionais = []  # Geral, TCC, etc.
        
        for mensagem in todas_mensagens:
            if isinstance(mensagem, dict):
                topico = mensagem.get('topico', [])
                
                # Se topico é uma lista, pega o primeiro item
                if isinstance(topico, list) and len(topico) > 0:
                    topico_str = topico[0] if isinstance(topico[0], str) else str(topico[0])
                elif isinstance(topico, str):
                    topico_str = topico
                else:
                    topico_str = 'Geral'
                
                topico_lower = topico_str.lower()
                
                # Classificar baseado no tópico
                if any(palavra in topico_lower for palavra in ['disciplina', 'conteúdo', 'materia', 'aula', 'prova', 'avaliacao']):
                    duvidas_materia.append(mensagem)
                else:
                    duvidas_institucionais.append(mensagem)
        
        # Obter informações do curso do usuário (se disponíveis)
        curso_codigo = user.get('curso_codigo', '') if user else ''
        curso_nome = user.get('curso_nome', '') if user else ''
        
        # Se não encontrou nada, mostra mensagem informativa
        if not todas_mensagens:
            flash("Nenhuma dúvida frequente encontrada.", "info")
        
        return render_template(
            'duvidas_frequentes/list.html',
            user=user,
            curso_codigo=curso_codigo,
            curso_nome=curso_nome,
            duvidas_materia=duvidas_materia,
            duvidas_institucionais=duvidas_institucionais,
            todas_duvidas=todas_mensagens
        )
    except requests.exceptions.RequestException as e:
        flash(f"Erro ao carregar dúvidas frequentes: {str(e)}", "error")
        return render_template(
            'duvidas_frequentes/list.html',
            user=session.get('user', {}),
            curso_codigo=session.get('user', {}).get('curso_codigo', '') if session.get('user') else '',
            curso_nome=session.get('user', {}).get('curso_nome', '') if session.get('user') else '',
            duvidas_materia=[],
            duvidas_institucionais=[],
            todas_duvidas=[]
        )

@app.route('/duvidas-frequentes/delete/<item_id>', methods=['POST'])
@login_required
def duvidas_frequentes_delete(item_id):
    """ Remove mensagem de aluno (dúvida frequente) via API """
    try:
        print(f"[DEBUG] Removendo mensagem de aluno {item_id}")
        headers = get_auth_headers()
        
        response = requests.delete(
            f"{API_BASE_URL}/mensagens_aluno/delete/{item_id}",
            headers=headers,
            timeout=10
        )
        
        print(f"[DEBUG] Status Code: {response.status_code}")
        
        if response.status_code in (200, 204):
            flash('Dúvida frequente removida com sucesso!', 'success')
        elif response.status_code == 404:
            flash('Dúvida frequente não encontrada.', 'error')
        else:
            response.raise_for_status()
            
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] HTTPError: {e}")
        flash(f'Erro ao remover dúvida frequente (HTTP {e.response.status_code}).', 'error')
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] RequestException: {e}")
        flash('Erro de comunicação com o servidor.', 'error')
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        flash('Erro inesperado ao remover dúvida frequente.', 'error')
    
    return redirect(url_for('duvidas_frequentes_list'))

# ===== ROTAS DE MENSAGENS DE ALUNO =====
@app.route('/mensagens_aluno', methods=['GET', 'POST'])
@login_required
def mensagens_aluno_list_create():
    """ Lista mensagens de aluno ou cria nova """
    if request.method == 'GET':
        try:
            headers = get_auth_headers()
            response = requests.get(f"{API_BASE_URL}/mensagens_aluno/get_lista_msg/", headers=headers, timeout=10)
            if response.status_code == 200:
                mensagens = response.json() if isinstance(response.json(), list) else [response.json()]
                return jsonify(mensagens), 200
            return jsonify([]), response.status_code
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Erro ao buscar mensagens de aluno: {e}")
            return jsonify([]), 500
    elif request.method == 'POST':
        try:
            headers = get_auth_headers()
            data = request.get_json() if request.is_json else request.form.to_dict()
            response = requests.post(f"{API_BASE_URL}/mensagens_aluno/", json=data, headers=headers, timeout=10)
            if response.status_code == 201:
                return jsonify(response.json()), 201
            return jsonify({"error": response.json().get("detail", "Erro ao criar mensagem")}), response.status_code
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e)}), 500

@app.route('/mensagens_aluno/update/<item_id>', methods=['PUT'])
@login_required
def mensagens_aluno_update(item_id):
    """ Atualiza mensagem de aluno """
    try:
        headers = get_auth_headers()
        data = request.get_json() if request.is_json else request.form.to_dict()
        response = requests.put(f"{API_BASE_URL}/mensagens_aluno/update/{item_id}", json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": response.json().get("detail", "Erro ao atualizar mensagem")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mensagens_aluno/delete/<item_id>', methods=['DELETE'])
@login_required
def mensagens_aluno_delete(item_id):
    """ Deleta mensagem de aluno """
    try:
        headers = get_auth_headers()
        response = requests.delete(f"{API_BASE_URL}/mensagens_aluno/delete/{item_id}", headers=headers, timeout=10)
        if response.status_code == 204:
            return jsonify({"message": "Mensagem deletada com sucesso"}), 200
        return jsonify({"error": response.json().get("detail", "Erro ao deletar mensagem")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== FUNÇÕES AUXILIARES PARA UPLOAD DE DOCUMENTOS =====
def upload_documento_por_categoria(file_storage, categoria, **kwargs):
    """
    Faz upload de documento usando o endpoint correto baseado na categoria.
    
    Args:
        file_storage: Arquivo do Flask request.files
        categoria: 'disciplina', 'tcc', 'aps', 'estagio', 'hora_complementares'
        **kwargs: Parâmetros adicionais conforme a categoria:
            - disciplina: nome_disciplina (str)
            - tcc/aps/estagio/hora_complementares: tipo (str), nome_curso (str), data (str)
    
    Returns:
        tuple: (success: bool, data: dict ou error: str)
    """
    try:
        headers = get_auth_headers()
        upload_headers = {k: v for k, v in headers.items() if k.lower() != 'content-type'}
        
        if not file_storage or file_storage.filename == '':
            return False, "Nenhum arquivo enviado"
        
        # Reset stream position
        file_storage.stream.seek(0)
        files = {'file': (file_storage.filename, file_storage.stream, file_storage.mimetype or 'application/octet-stream')}
        
        # Prepara dados conforme a categoria
        data = {}
        endpoint = ""
        
        if categoria == 'disciplina':
            endpoint = f"{API_BASE_URL}/documentos/upload_disciplina"
            if 'nome_disciplina' not in kwargs:
                return False, "nome_disciplina é obrigatório para upload de disciplina"
            data['nome_disciplina'] = kwargs['nome_disciplina']
        
        elif categoria == 'tcc':
            endpoint = f"{API_BASE_URL}/documentos/upload_tcc"
            for key in ['tipo', 'nome_curso', 'data']:
                if key not in kwargs:
                    return False, f"{key} é obrigatório para upload de TCC"
                data[key] = kwargs[key]
        
        elif categoria == 'aps':
            endpoint = f"{API_BASE_URL}/documentos/upload_aps"
            for key in ['tipo', 'nome_curso', 'data']:
                if key not in kwargs:
                    return False, f"{key} é obrigatório para upload de APS"
                data[key] = kwargs[key]
        
        elif categoria == 'estagio':
            endpoint = f"{API_BASE_URL}/documentos/upload_estagio"
            for key in ['tipo', 'nome_curso', 'data']:
                if key not in kwargs:
                    return False, f"{key} é obrigatório para upload de Estágio"
                data[key] = kwargs[key]
        
        elif categoria == 'hora_complementares':
            endpoint = f"{API_BASE_URL}/documentos/upload_hora_complementares"
            for key in ['tipo', 'nome_curso', 'data']:
                if key not in kwargs:
                    return False, f"{key} é obrigatório para upload de Horas Complementares"
                data[key] = kwargs[key]
        
        else:
            return False, f"Categoria '{categoria}' não suportada"
        
        # Faz a requisição
        response = requests.post(endpoint, files=files, data=data, headers=upload_headers, timeout=30)
        
        if response.status_code == 201:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", f"Erro {response.status_code}") if response.headers.get('content-type', '').startswith('application/json') else response.text
            return False, error_detail
            
    except requests.exceptions.RequestException as e:
        return False, str(e)
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

# ===== ROTAS DE DOCUMENTOS =====
@app.route('/documentos/upload', methods=['POST'])
@login_required
def documentos_upload():
    """ Upload de documento genérico (mantido para compatibilidade) """
    try:
        headers = get_auth_headers()
        upload_headers = {k: v for k, v in headers.items() if k.lower() != 'content-type'}
        
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nome de arquivo vazio"}), 400
        
        # Tenta usar upload_disciplina se nome_disciplina for fornecido
        nome_disciplina = request.form.get('nome_disciplina')
        if nome_disciplina:
            success, result = upload_documento_por_categoria(file, 'disciplina', nome_disciplina=nome_disciplina)
            if success:
                return jsonify(result), 201
            return jsonify({"error": result}), 400
        
        # Fallback para endpoint antigo (se ainda existir)
        files = {'file': (file.filename, file.stream, file.content_type)}
        response = requests.post(f"{API_BASE_URL}/documentos/upload", files=files, headers=upload_headers, timeout=30)
        
        if response.status_code == 201:
            return jsonify(response.json()), 201
        return jsonify({"error": response.json().get("detail", "Erro ao fazer upload do documento")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE IA SERVICES =====
@app.route('/ia/gerar-resposta', methods=['POST'])
@login_required
def ia_gerar_resposta():
    """ Gera resposta usando IA """
    try:
        headers = get_auth_headers()
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validação básica
        if 'pergunta' not in data:
            return jsonify({"error": "Campo 'pergunta' é obrigatório"}), 400
        
        response = requests.post(f"{API_BASE_URL}/ia/gerar-resposta", json=data, headers=headers, timeout=60)
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        return jsonify({"error": response.json().get("detail", "Erro ao gerar resposta com IA")}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# ===== ERROS =====
@app.errorhandler(404)
def handle_404(e):
    """ Handler para erros 404 - Página não encontrada """
    if request.path.startswith('/debug/'):
        # Para rotas de debug, retorna JSON
        return jsonify({
            'error': 'Not Found',
            'message': 'A rota solicitada não foi encontrada.',
            'path': request.path
        }), 404
    else:
        # Para outras rotas, redireciona para a página inicial
        # Não exibe mensagem de erro para evitar duplicação, pois o flash já foi usado antes
        return redirect(url_for('index'))

# Execução da aplicação
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
