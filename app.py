# Imports necessários
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from functools import wraps
import os
import re

# Configuração da aplicação Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave secreta para sessões

# URL da API (ajustar conforme necessário)
API_BASE_URL = "http://127.0.0.1:8000"
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
            
            response.raise_for_status()
            user_data = response.json()
            print(f"[DEBUG] User Data JSON: {user_data}")

            # Extrai o ID do usuário de forma flexível
            user_id = (
                user_data.get('id') or 
                user_data.get('id_aluno') or
                user_data.get('id_professor') or 
                user_data.get('id_coordenador') or 
                user_data.get('user_id') or
                user_data.get('userId')
            )
            
            # Extrai o nome do usuário de forma flexível (com nome e sobrenome)
            # Prioriza os campos específicos da API de alunos
            nome = (
                user_data.get('nome_aluno') or 
                user_data.get('nome') or 
                user_data.get('name') or 
                ''
            )
            sobrenome = (
                user_data.get('sobrenome_aluno') or 
                user_data.get('sobrenome') or 
                user_data.get('lastname') or 
                user_data.get('last_name') or 
                ''
            )
            
            # Monta o nome completo
            if nome and sobrenome:
                # Caso 1: Nome e sobrenome separados na API
                user_nome = f"{nome} {sobrenome}"
            elif nome:
                # Caso 2: Nome completo em um único campo - usa apenas o nome
                user_nome = nome
            else:
                # Fallback: usa parte do email
                user_nome = email.split('@')[0]
            
            print(f"[DEBUG] Nome original: '{nome}', Sobrenome: '{sobrenome}', Nome final: '{user_nome}'")
            
            # Extrai o tipo de usuário
            user_tipo = (
                user_data.get('tipo') or 
                user_data.get('type') or 
                user_data.get('role') or
                'usuario'
            )

            # Extrai o email (prioriza email_institucional para alunos)
            user_email = (
                user_data.get('email_institucional') or
                user_data.get('email') or
                email
            )

            # Guarda informações na sessão
            session['user'] = {
                'id': user_id,
                'nome': user_nome,
                'email': user_email,
                'tipo': user_tipo,
                'matricula': user_data.get('matricula_ra', ''),
                'raw_data': user_data  # Guarda dados brutos para debug
            }
            
            print(f"[DEBUG] Session User: {session['user']}")
            
            # Verifica se pelo menos um ID foi obtido
            if not session['user']['id']:
                print("[DEBUG] ERRO: Nenhum ID de usuário encontrado na resposta da API")
                print(f"[DEBUG] Estrutura recebida: {user_data.keys()}")
                flash("Erro ao processar dados do utilizador recebidos da API.", "error")
                session.pop('user', None)
                return redirect(url_for('index'))

            # Login bem-sucedido - configurar sessão
            session.permanent = True
            flash(f"Bem-vindo(a), {session['user'].get('nome', 'Usuário')}!", "success")
            return redirect(url_for('dashboard'))

        except requests.exceptions.HTTPError as e:
            print(f"[DEBUG] HTTPError: {e}")
            print(f"[DEBUG] Response Text: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            
            if e.response.status_code == 401:
                flash("Credenciais inválidas. Verifique seu email e senha.", "error")
            elif e.response.status_code == 404:
                flash("Endpoint de login não encontrado na API. Verifique a configuração.", "error")
            elif e.response.status_code == 422:
                try:
                    error_detail = e.response.json()
                    flash(f"Dados inválidos: {error_detail}", "error")
                except:
                    flash("Dados de login inválidos. Verifique o formato.", "error")
            else:
                flash(f"Erro no servidor de autenticação (HTTP {e.response.status_code}). Tente novamente.", "error")
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
        print(f"[DEBUG] Buscando avisos em: {API_BASE_URL}/aviso/")
        response = requests.get(f"{API_BASE_URL}/aviso/", timeout=5)
        print(f"[DEBUG] Avisos - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[DEBUG] Avisos - Tipo de dados: {type(data)}")
            
            if isinstance(data, list):
                dashboard_data['avisos'] = data
                print(f"[DEBUG] {len(data)} avisos encontrados")
            else:
                print(f"[DEBUG] Formato inesperado de avisos: {data}")
        else:
            print(f"[DEBUG] Avisos retornou status {response.status_code}")
            
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
        response_avisos = requests.get(f"{API_BASE_URL}/aviso/", timeout=5)
        print(f"[DEBUG] Avisos - Status: {response_avisos.status_code}")
        
        # Teste do endpoint de professores (GET não existe)
        try:
            response_professores = requests.get(f"{API_BASE_URL}/professores/", timeout=5)
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
    """ Lista docentes - usa dados mock (API não tem GET) """
    print(f"[DEBUG] API não suporta GET /professores/ - usando dados mock")
    
    docentes = get_docentes_list()
    return render_template('docentes/list.html', docentes=docentes)

@app.route('/docentes/add', methods=['GET', 'POST'])
@login_required
def docentes_add():
    """ Adiciona novo docente via API """
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
                return render_template('docentes/add.html')
            
            # Validação do ID funcional (máximo 7 caracteres)
            if len(docente_data['id_funcional']) > 7:
                flash("ID Funcional deve ter no máximo 7 caracteres.", "error")
                return render_template('docentes/add.html')
            
            # Validação de formato de email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, docente_data['email_institucional']):
                flash("Formato de email inválido.", "error")
                return render_template('docentes/add.html')
            
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
            
            response = requests.post(f"{API_BASE_URL}/professores/", json=docente_data, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response Headers: {dict(response.headers)}")
            print(f"[DEBUG] Response Text: {response.text}")
            
            if response.status_code == 201:
                # Adiciona o novo docente à lista da sessão
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
    
    return render_template('docentes/add.html')

@app.route('/docentes/view/<int:id>')
@login_required
def docentes_view(id):
    """ Visualiza docente - busca na lista da sessão """
    print(f"[DEBUG] Buscando docente {id} na lista da sessão")
    
    # Busca o docente na lista da sessão
    docentes_list = get_docentes_list()
    docente = next((d for d in docentes_list if d.get('id') == id), None)
    
    if not docente:
        flash("Docente não encontrado.", "error")
        return redirect(url_for('docentes_list'))
    
    # Adiciona dados extras para exibição (não salvos na API)
    docente_completo = {
        **docente,
        'nivel_acesso': 'professor',
        'disciplinas': ['Ciência da Computação', 'Análise e Desenvolvimento de Sistemas'],
        'dia_semana': 'terça',
        'horario_inicio': '14:00',
        'horario_fim': '18:00'
    }
    
    print(f"[DEBUG] Docente encontrado: {docente_completo}")
    return render_template('docentes/view.html', docente=docente_completo)

@app.route('/docentes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def docentes_edit(id):
    """ Edita docente - GET usa mock, POST envia para API """
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
            response = requests.put(f"{API_BASE_URL}/professores/{id}", json=docente_data, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            response.raise_for_status()
            flash("Docente atualizado com sucesso!", "success")
            return redirect(url_for('docentes_view', id=id))
            
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
            flash("Erro inesperado ao atualizar docente.", "error")
    
    # GET - Buscar dados do docente para edição (usando dados mock)
    print(f"[DEBUG] API não suporta GET /professores/{id} - usando dados mock para edição")
    
    # Dados mock baseados no ID (mesmo da função view)
    mock_docentes = {
        1: {
            'id': 1,
            'nome_professor': 'João',
            'sobrenome_professor': 'Silva',
            'email_institucional': 'joao.silva@docente.unip.br',
            'id_funcional': 'F123456',
            'nivel_acesso': 'professor',
            'disciplinas': ['ciencia_computacao', 'ads'],
            'dia_semana': 'terca',
            'horario_inicio': '14:00',
            'horario_fim': '18:00'
        },
        2: {
            'id': 2,
            'nome_professor': 'Maria',
            'sobrenome_professor': 'Santos',
            'email_institucional': 'maria.santos@docente.unip.br',
            'id_funcional': 'F789012',
            'nivel_acesso': 'coordenador',
            'disciplinas': ['eng_software'],
            'dia_semana': 'quinta',
            'horario_inicio': '19:00',
            'horario_fim': '23:00'
        },
        3: {
            'id': 3,
            'nome_professor': 'Carlos',
            'sobrenome_professor': 'Oliveira',
            'email_institucional': 'carlos.oliveira@docente.unip.br',
            'id_funcional': 'F345678',
            'nivel_acesso': 'professor',
            'disciplinas': ['sistemas_info'],
            'dia_semana': 'segunda',
            'horario_inicio': '08:00',
            'horario_fim': '12:00'
        }
    }
    
    docente = mock_docentes.get(id)
    if not docente:
        flash("Docente não encontrado.", "error")
        return redirect(url_for('docentes_list'))
    
    print(f"[DEBUG] Docente encontrado para edição: {docente}")
    
    return render_template('docentes/edit.html', docente=docente)

@app.route('/docentes/delete/<int:id>', methods=['POST'])
@login_required
def docentes_delete(id):
    """ Remove docente via API """
    try:
        print(f"[DEBUG] Removendo docente {id}")
        # DELETE /professores/{id} - conforme documentação da API
        response = requests.delete(f"{API_BASE_URL}/professores/{id}", timeout=10)
        print(f"[DEBUG] Status Code: {response.status_code}")
        
        response.raise_for_status()
        
        # Remove o docente da lista da sessão
        remove_docente_from_list(id)
        
        flash("Docente removido com sucesso!", "success")
        
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] HTTPError: {e}")
        flash(f"Erro ao remover docente (HTTP {e.response.status_code}).", "error")
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] RequestException: {e}")
        flash("Erro de comunicação com o servidor.", "error")
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        flash("Erro inesperado ao remover docente.", "error")
    
    return redirect(url_for('docentes_list'))

# ===== FUNÇÕES AUXILIARES PARA DOCENTES =====

def get_docentes_list():
    """ Retorna a lista de docentes da sessão, inicializando se necessário """
    if 'docentes_list' not in session:
        session['docentes_list'] = [
            {
                'id': 1,
                'nome_professor': 'João',
                'sobrenome_professor': 'Silva',
                'email_institucional': 'joao.silva@docente.unip.br',
                'id_funcional': 'F123456'
            },
            {
                'id': 2,
                'nome_professor': 'Maria',
                'sobrenome_professor': 'Santos',
                'email_institucional': 'maria.santos@docente.unip.br',
                'id_funcional': 'F789012'
            },
            {
                'id': 3,
                'nome_professor': 'Carlos',
                'sobrenome_professor': 'Oliveira',
                'email_institucional': 'carlos.oliveira@docente.unip.br',
                'id_funcional': 'F345678'
            }
        ]
    return session['docentes_list']

def add_docente_to_list(docente_data):
    """ Adiciona um novo docente à lista da sessão """
    if 'docentes_list' not in session:
        session['docentes_list'] = []
    
    # Gera um novo ID único para o docente
    max_id = max([d.get('id', 0) for d in session['docentes_list']], default=0)
    novo_docente = {
        'id': max_id + 1,
        'nome_professor': docente_data['nome_professor'],
        'sobrenome_professor': docente_data['sobrenome_professor'],
        'email_institucional': docente_data['email_institucional'],
        'id_funcional': docente_data['id_funcional']
    }
    
    session['docentes_list'].append(novo_docente)
    session.modified = True
    return novo_docente

def remove_docente_from_list(docente_id):
    """ Remove um docente da lista da sessão """
    if 'docentes_list' in session:
        session['docentes_list'] = [d for d in session['docentes_list'] if d.get('id') != docente_id]
        session.modified = True

# ===== ROTAS DE CONTEÚDO =====

CONTENT_ENDPOINT_CANDIDATES = [
    "/conteudo",
    "/materiais",
    "/material",
]

def _join_url(base, path):
    return f"{base}{path if path.startswith('/') else '/' + path}"

def resolve_content_endpoint():
    for cand in CONTENT_ENDPOINT_CANDIDATES:
        try:
            url = _join_url(API_BASE_URL, f"{cand}/")
            resp = requests.get(url, timeout=5)
            if resp.status_code in (200, 204, 400, 405):
                return cand
        except requests.exceptions.RequestException:
            continue
    return "/conteudo"

def get_conteudos_api():
    endpoint = resolve_content_endpoint()
    try:
        resp = requests.get(_join_url(API_BASE_URL, f"{endpoint}/"), timeout=8)
        if resp.status_code == 200 and isinstance(resp.json(), list):
            return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Conteúdo GET falhou: {e}")
    return []

def create_conteudo_api(data, file_storage=None):
    endpoint = resolve_content_endpoint()
    url = _join_url(API_BASE_URL, f"{endpoint}/")
    try:
        if file_storage and file_storage.filename:
            files = {"arquivo": (file_storage.filename, file_storage.stream, file_storage.mimetype or 'application/octet-stream')}
            resp = requests.post(url, data=data, files=files, timeout=15)
        else:
            resp = requests.post(url, json=data, timeout=10)
        if resp.status_code in (200, 201):
            try:
                return True, resp.json()
            except Exception:
                return True, None
        return False, resp.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

def update_conteudo_api(conteudo_id, data, file_storage=None):
    endpoint = resolve_content_endpoint()
    url = _join_url(API_BASE_URL, f"{endpoint}/{conteudo_id}")
    try:
        if file_storage and file_storage.filename:
            files = {"arquivo": (file_storage.filename, file_storage.stream, file_storage.mimetype or 'application/octet-stream')}
            resp = requests.put(url, data=data, files=files, timeout=15)
        else:
            resp = requests.put(url, json=data, timeout=10)
        return resp.status_code in (200, 204)
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Conteúdo PUT falhou: {e}")
        return False

def delete_conteudo_api(conteudo_id):
    endpoint = resolve_content_endpoint()
    url = _join_url(API_BASE_URL, f"{endpoint}/{conteudo_id}")
    try:
        resp = requests.delete(url, timeout=8)
        return resp.status_code in (200, 204)
    except requests.exceptions.RequestException:
        return False

# ===== Sessão (fallback local) =====

def get_conteudo_list_session():
    if 'conteudos_list' not in session:
        session['conteudos_list'] = [
            { 'id': 1, 'titulo': 'Slide - Aula 01', 'disciplina': 'Ciência da Computação', 'tipo': 'aula', 'url_arquivo': '', 'link': 'https://exemplo.com/aula-01' },
            { 'id': 2, 'titulo': 'Artigo Complementar', 'disciplina': 'Ciência da Computação', 'tipo': 'complementar', 'url_arquivo': '', 'link': 'https://exemplo.com/artigo' },
            { 'id': 3, 'titulo': 'Lista de Exercícios', 'disciplina': 'Análise e Desenvolvimento de Sistemas', 'tipo': 'aula', 'url_arquivo': '', 'link': '' },
        ]
    return session['conteudos_list']

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
    api_items = get_conteudos_api()
    if api_items:
        set_conteudo_list_session(api_items)
        items = api_items
    else:
        items = get_conteudo_list_session()

    grouped = group_by_disciplina(items)
    disciplina = request.args.get('disciplina') or (next(iter(grouped.keys()), 'Sem Disciplina'))

    return render_template('conteudo/list.html', grouped=grouped, disciplina_selecionada=disciplina)

@app.route('/conteudo/add', methods=['GET', 'POST'])
@login_required
def conteudo_add():
    if request.method == 'POST':
        tipo = request.form.get('tipo', 'aula')
        titulo = request.form.get('titulo', '').strip()
        disciplina = request.form.get('disciplina', '').strip() or 'Sem Disciplina'
        link = request.form.get('link', '').strip()
        arquivo = request.files.get('arquivo')

        if not titulo:
            flash('Título é obrigatório.', 'error')
            return render_template('conteudo/add.html')

        if not link and (not arquivo or not arquivo.filename):
            flash('Envie um arquivo ou informe um link.', 'error')
            return render_template('conteudo/add.html')

        payload = { 'tipo': tipo, 'titulo': titulo, 'disciplina': disciplina, 'link': link }
        ok, resp = create_conteudo_api(payload, arquivo)
        if ok:
            # Atualiza cache local
            added = { **payload, 'url_arquivo': '', 'id': (resp.get('id') if isinstance(resp, dict) else None) }
            add_conteudo_session(added)
            flash('Conteúdo cadastrado com sucesso!', 'success')
            return redirect(url_for('conteudo_list', disciplina=disciplina))
        else:
            flash(f'Erro ao cadastrar conteúdo: {resp}', 'error')

    return render_template('conteudo/add.html')

@app.route('/conteudo/edit/<conteudo_id>', methods=['GET', 'POST'])
@login_required
def conteudo_edit(conteudo_id):
    item = find_conteudo_session(conteudo_id)
    if not item:
        flash('Conteúdo não encontrado.', 'error')
        return redirect(url_for('conteudo_list'))

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

    return render_template('conteudo/edit.html', conteudo=item)

# ===== ROTAS DE AVISOS =====

@app.route('/avisos')
@login_required
def avisos_list():
    """ Lista avisos - busca da API """
    try:
        print(f"[DEBUG] Buscando avisos em: {API_BASE_URL}/aviso/")
        response = requests.get(f"{API_BASE_URL}/aviso/", timeout=10)
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
                return render_template('avisos/add.html')
            
            # Validação de data
            try:
                from datetime import datetime
                datetime.strptime(aviso_data['data'], '%Y-%m-%d')
            except ValueError:
                flash("Formato de data inválido. Use YYYY-MM-DD.", "error")
                return render_template('avisos/add.html')
            
            print(f"[DEBUG] Criando aviso: {aviso_data}")
            response = requests.post(f"{API_BASE_URL}/aviso/", json=aviso_data, timeout=10)
            print(f"[DEBUG] Status Code: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            if response.status_code == 201:
                flash("Aviso criado com sucesso!", "success")
                return redirect(url_for('avisos_list'))
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
            flash("Erro inesperado ao criar aviso.", "error")
    
    return render_template('avisos/add.html')

@app.route('/avisos/view/<aviso_id>')
@login_required
def avisos_view(aviso_id):
    """ Visualiza aviso espec��fico """
    try:
        print(f"[DEBUG] Buscando aviso {aviso_id}")
        response = requests.get(f"{API_BASE_URL}/aviso/{aviso_id}", timeout=10)
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
                return render_template('avisos/edit.html', aviso={'id_aviso': aviso_id, **aviso_data})
            
            # Validação de data
            try:
                from datetime import datetime
                datetime.strptime(aviso_data['data'], '%Y-%m-%d')
            except ValueError:
                flash("Formato de data inválido. Use YYYY-MM-DD.", "error")
                return render_template('avisos/edit.html', aviso={'id_aviso': aviso_id, **aviso_data})
            
            print(f"[DEBUG] Atualizando aviso {aviso_id}: {aviso_data}")
            response = requests.put(f"{API_BASE_URL}/aviso/{aviso_id}", json=aviso_data, timeout=10)
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
    try:
        print(f"[DEBUG] Buscando aviso {aviso_id} para edição")
        response = requests.get(f"{API_BASE_URL}/aviso/{aviso_id}", timeout=10)
        print(f"[DEBUG] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            aviso = response.json()
            print(f"[DEBUG] Aviso encontrado para edição: {aviso}")
            return render_template('avisos/edit.html', aviso=aviso)
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
        response = requests.delete(f"{API_BASE_URL}/aviso/{aviso_id}", timeout=10)
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
    if 'materias_list' not in session:
        session['materias_list'] = []
    return session['materias_list']

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
def calendario_add():
    step = int(request.args.get('step') or request.form.get('step') or 1)
    wizard = get_wizard_state()

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

            novo = add_materia_session(wizard.copy())
            clear_wizard_state()
            flash('Matéria cadastrada com sucesso!', 'success')
            return redirect(url_for('calendario_view', materia_id=novo.get('id')))

    return render_template('calendario/add.html', step=step, wizard=wizard, user=session.get('user', {}))

@app.route('/calendario/view/<int:materia_id>')
@login_required
def calendario_view(materia_id):
    materia = next((m for m in get_materias_list() if m.get('id') == materia_id), None)
    if not materia:
        flash('Matéria não encontrada.', 'error')
        return redirect(url_for('calendario_list'))
    return render_template('calendario/view.html', materia=materia, user=session.get('user', {}))

@app.route('/calendario/edit/<int:materia_id>', methods=['GET', 'POST'])
@login_required
def calendario_edit(materia_id):
    materias = get_materias_list()
    materia = next((m for m in materias if m.get('id') == materia_id), None)

    if not materia:
        flash('Matéria não encontrada.', 'error')
        return redirect(url_for('calendario_list'))

    step = int(request.args.get('step') or request.form.get('step') or 1)
    wizard = session.setdefault('edit_wizard', materia.copy())

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

            for idx, m in enumerate(materias):
                if m.get('id') == materia_id:
                    materias[idx] = wizard.copy()
                    break

            session.modified = True
            session.pop('edit_wizard', None)
            flash('Matéria atualizada com sucesso!', 'success')
            return redirect(url_for('calendario_view', materia_id=materia_id))

    return render_template('calendario/edit.html', step=step, wizard=wizard, materia_id=materia_id, user=session.get('user', {}))

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
        # Processar dados do formulário APS
        flash('APS adicionada com sucesso!', 'success')
        session.pop('add_info_type', None)
        return redirect(url_for('infos_curso_list'))

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
            flash('TCC adicionado com sucesso!', 'success')
            session.pop('tcc_step', None)
            session.pop('add_info_type', None)
            return redirect(url_for('infos_curso_list'))

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
            flash('Estágio adicionado com sucesso!', 'success')
            session.pop('estagio_step', None)
            session.pop('add_info_type', None)
            return redirect(url_for('infos_curso_list'))

        return redirect(url_for('infos_curso_add_estagio'))

    return render_template('infos_curso/add_estagio.html', step=session.get('estagio_step', 1), user=session.get('user', {}))

@app.route('/infos-curso/add/horas', methods=['GET', 'POST'])
@login_required
def infos_curso_add_horas():
    """ Formulário para adicionar Horas Complementares """
    if request.method == 'POST':
        # Processar dados do formulário Horas Complementares
        flash('Horas Complementares adicionadas com sucesso!', 'success')
        session.pop('add_info_type', None)
        return redirect(url_for('infos_curso_list'))

    return render_template('infos_curso/add_horas.html', user=session.get('user', {}))

# ===== ERROS =====
@app.errorhandler(404)
def handle_404(e):
    return render_template('404.html'), 404

# Execução da aplicação
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
