# 🎓 ChatBot Frontend - Painel Administrativo

<div align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

**Interface web moderna e responsiva para gerenciamento acadêmico universitário**

[Features](#-features) • [Instalação](#-instalação) • [Uso](#-como-usar) • [Documentação](#-documentação) • [Contribuindo](#-contribuindo)

</div>

---

## 📋 Sobre o Projeto

O **ChatBot Frontend** é uma aplicação web desenvolvida em Flask que oferece uma interface administrativa completa para gerenciamento acadêmico universitário. O sistema integra-se com uma API REST para fornecer funcionalidades como gestão de avisos, conteúdo acadêmico, calendário, docentes, alunos e informações de cursos.

### 🎯 Objetivo

Fornecer uma interface intuitiva e eficiente para administradores, coordenadores, professores e alunos gerenciarem informações acadêmicas de forma centralizada e segura.

---

## ✨ Features

### 🔐 Autenticação e Segurança
- ✅ Sistema de login com autenticação via Bearer Token
- ✅ Controle de acesso baseado em roles (Admin, Coordenador, Professor, Aluno)
- ✅ Sessões seguras com Flask
- ✅ Proteção de rotas com decorators customizados

### 📢 Gestão de Avisos
- ✅ Listagem completa de avisos
- ✅ Criação, edição e remoção de avisos
- ✅ Visualização detalhada de avisos
- ✅ Filtros por data e busca textual
- ✅ Associação com professores ou coordenadores

### 📚 Gestão de Conteúdo Acadêmico
- ✅ CRUD completo de conteúdo acadêmico
- ✅ Organização por disciplinas e cursos
- ✅ Interface intuitiva para gerenciamento

### 👨‍🏫 Gestão de Docentes
- ✅ Cadastro e edição de professores
- ✅ Listagem e visualização de perfis
- ✅ Integração com sistema de avisos

### 📅 Calendário Acadêmico
- ✅ Visualização de eventos acadêmicos
- ✅ Gestão de cronogramas
- ✅ Organização por período letivo

### 🎓 Informações de Curso
- ✅ Gestão de informações de cursos
- ✅ Atividades Práticas Supervisionadas (APS)
- ✅ Estágio supervisionado
- ✅ Trabalho de Conclusão de Curso (TCC)
- ✅ Gestão de horas complementares

### 📊 Dashboard
- ✅ Painel centralizado com resumo de informações
- ✅ Estatísticas rápidas
- ✅ Acesso rápido às principais funcionalidades

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **[Flask](https://flask.palletsprojects.com/)** 3.0.0 - Framework web Python
- **[Requests](https://requests.readthedocs.io/)** 2.31.0 - Cliente HTTP para comunicação com API

### Frontend
- **HTML5** - Estrutura semântica
- **CSS3** - Estilização moderna e responsiva
- **JavaScript (Vanilla)** - Interatividade e validações
- **Jinja2** - Sistema de templates

### Ferramentas
- **Python 3.10+** - Linguagem de programação
- **Git** - Controle de versão
- **Virtual Environment** - Isolamento de dependências

---

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python** 3.10 ou superior
- **pip** (gerenciador de pacotes Python)
- **Git** (para clonar o repositório)
- **API Backend** rodando e acessível (veja [Configuração](#-configuração))
- **Arquivo `.env` configurado** ⚠️ **OBRIGATÓRIO** (veja [Instalação - Passo 4](#4-configure-a-aplicação--obrigatório))

### Verificação de Versão

```bash
python --version  # Deve retornar Python 3.10+
pip --version     # Verifica se pip está instalado
```

---

## 🚀 Instalação

Siga estes passos para configurar o projeto localmente:

### 1. Clone o Repositório

```bash
git clone https://github.com/leodah20/chatbot-front.git
cd chatbot-front
```

### 2. Crie um Ambiente Virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configure a Aplicação ⚠️ OBRIGATÓRIO

**O arquivo `.env` é OBRIGATÓRIO para executar a aplicação.** Sem ele, a aplicação não iniciará.

#### Opção 1: Usar o template `.env.example` (Recomendado)

**Windows (PowerShell):**
```powershell
# Copie o arquivo de exemplo
Copy-Item .env.example .env
```

**Linux/Mac:**
```bash
# Copie o arquivo de exemplo
cp .env.example .env
```

#### Opção 2: Criar manualmente

**Windows (PowerShell):**
```powershell
# Crie o arquivo .env
New-Item -Path .env -ItemType File
```

**Linux/Mac:**
```bash
# Crie o arquivo .env
touch .env
```

#### Conteúdo mínimo obrigatório do arquivo `.env`:

```env
# ============================================
# ⚠️ VARIÁVEIS OBRIGATÓRIAS
# ============================================

# Chave secreta para criptografia de sessões Flask
# OBRIGATÓRIO: Gere uma chave segura usando o comando abaixo:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=sua-chave-secreta-aqui

# URL base da API Backend (ChatBot_API)
# OBRIGATÓRIO: URL onde a API backend está rodando
API_BASE_URL=http://127.0.0.1:8000

# ============================================
# Configurações Recomendadas
# ============================================

FLASK_APP=app.py
FLASK_ENV=development
DEBUG=True
```

**📝 Explicação das variáveis OBRIGATÓRIAS:**

- **`SECRET_KEY`** ⚠️ **OBRIGATÓRIA**: Chave secreta usada para criptografar dados de sessão Flask. **Essencial para segurança e autenticação!**
  - Para gerar uma chave segura, execute: `python -c "import secrets; print(secrets.token_hex(32))"`
  - Copie a chave gerada e cole no lugar de `sua-chave-secreta-aqui`
  - **NUNCA** compartilhe esta chave publicamente
- **`API_BASE_URL`** ⚠️ **OBRIGATÓRIA**: URL onde a API backend está rodando (padrão: `http://127.0.0.1:8000`)
  - Ajuste se a API estiver em outro servidor ou porta

**📝 Variáveis opcionais (com valores padrão):**

- **`FLASK_APP`**: Nome do arquivo principal da aplicação (padrão: `app.py`)
- **`FLASK_ENV`**: Ambiente de execução (`development` para desenvolvimento, `production` para produção)
- **`DEBUG`**: Modo debug (`True` para desenvolvimento, `False` para produção)

**⚠️ IMPORTANTE:**
- O arquivo `.env` é **OBRIGATÓRIO** - a aplicação não funcionará sem ele
- O arquivo `.env` está no `.gitignore` e **NUNCA** será commitado no repositório
- Use o arquivo `.env.example` como template se necessário
- Em produção, use uma `SECRET_KEY` diferente da usada em desenvolvimento

### 5. Execute a Aplicação

```bash
# Opção 1: Usando Flask CLI
flask run

# Opção 2: Usando Python diretamente
python app.py
```

A aplicação estará disponível em: **http://127.0.0.1:5000**

---

## ⚙️ Configuração

### 📋 Arquivo `.env` - Guia Completo

O arquivo `.env` é usado para configurar variáveis de ambiente da aplicação. Ele deve ser criado na **raiz do projeto** (mesmo nível do `app.py`).

#### 📝 Exemplo Completo de `.env`

```env
# ============================================
# Configurações da Aplicação Flask
# ============================================

# Nome do arquivo principal da aplicação
FLASK_APP=app.py

# Ambiente: 'development' (desenvolvimento) ou 'production' (produção)
FLASK_ENV=development

# Chave secreta para criptografia de sessões Flask
# ⚠️ MUITO IMPORTANTE: Use uma chave forte e única!
# 
# Como gerar uma chave segura:
# Windows PowerShell:
#   python -c "import secrets; print(secrets.token_hex(32))"
# 
# Linux/Mac:
#   python3 -c "import secrets; print(secrets.token_hex(32))"
#
# Exemplo de chave gerada:
#   a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
SECRET_KEY=cole-aqui-a-chave-gerada-pelo-comando-acima

# ============================================
# Configurações da API Backend
# ============================================

# URL base da API Backend (ChatBot_API)
# Se a API estiver rodando localmente na porta 8000:
API_BASE_URL=http://127.0.0.1:8000

# Se a API estiver em outro servidor, ajuste:
# API_BASE_URL=http://seu-servidor.com:8000

# ============================================
# Configurações Opcionais
# ============================================

# Porta onde o Flask irá rodar (padrão: 5000)
# FLASK_RUN_PORT=5000

# Host onde o Flask irá rodar (padrão: 127.0.0.1)
# Para permitir acesso externo, use: 0.0.0.0
# FLASK_RUN_HOST=127.0.0.1
```

#### 🔑 O que é o `SECRET_KEY`?

O `SECRET_KEY` é uma string aleatória usada pelo Flask para:
- **Criptografar dados de sessão** (cookies, informações de login)
- **Assinar tokens** e garantir que não foram alterados
- **Proteger contra ataques CSRF** (Cross-Site Request Forgery)

**⚠️ Segurança:**
- **NUNCA** compartilhe sua `SECRET_KEY` publicamente
- **NUNCA** commite o arquivo `.env` no Git (já está no `.gitignore`)
- Use uma chave **diferente** para desenvolvimento e produção
- Gere uma chave **única** para cada ambiente

#### 🚀 Configuração Rápida (Passo a Passo)

1. **Gere a chave secreta:**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Crie o arquivo `.env`** na raiz do projeto com o conteúdo acima

3. **Cole a chave gerada** no lugar de `cole-aqui-a-chave-gerada-pelo-comando-acima`

4. **Verifique se a API está rodando** na URL configurada em `API_BASE_URL`

5. **Inicie a aplicação:**
   ```bash
   flask run
   ```

#### 🔧 Configuração da API

Por padrão, a aplicação se conecta à API em `http://127.0.0.1:8000`. 

**Para alterar a URL da API:**
- Edite o arquivo `.env` e altere o valor de `API_BASE_URL`
- Certifique-se de que a API backend está rodando e acessível nesta URL

**Exemplo para API em servidor remoto:**
```env
API_BASE_URL=http://192.168.1.100:8000
```

#### ✅ Verificação

Após configurar o `.env`, verifique se tudo está correto:

1. ✅ Arquivo `.env` existe na raiz do projeto
2. ✅ `SECRET_KEY` foi gerada e configurada
3. ✅ `API_BASE_URL` aponta para a URL correta da API
4. ✅ API backend está rodando e acessível
5. ✅ Ambiente virtual está ativado
6. ✅ Dependências estão instaladas (`pip install -r requirements.txt`)

---

## 🎮 Como Usar

### 1. Acesse a Aplicação

Abra seu navegador e acesse: `http://127.0.0.1:5000`

### 2. Faça Login

Use suas credenciais para fazer login no sistema:
- **Email:** Seu email institucional
- **Senha:** Sua senha cadastrada

### 3. Navegue pelo Dashboard

Após o login, você será redirecionado para o dashboard principal, onde poderá acessar todas as funcionalidades.

### 4. Funcionalidades Disponíveis

- **Dashboard:** Visão geral do sistema
- **Avisos:** Gerenciar avisos acadêmicos
- **Conteúdo:** Gerenciar conteúdo acadêmico
- **Docentes:** Gerenciar professores
- **Calendário:** Visualizar eventos acadêmicos
- **Informações de Curso:** Gerenciar informações de cursos

### 5. Controle de Acesso

O sistema possui diferentes níveis de acesso:

- **Admin:** Acesso completo a todas as funcionalidades
- **Coordenador:** Pode criar e gerenciar avisos, visualizar conteúdo
- **Professor:** Visualização de conteúdo e criação de avisos (quando permitido)
- **Aluno:** Visualização de avisos e conteúdo

---

## 📁 Estrutura do Projeto

```
chatbot-front/
│
├── app.py                          # Aplicação principal Flask
├── requirements.txt                # Dependências do projeto
├── .gitignore                      # Arquivos ignorados pelo Git
├── README.md                       # Este arquivo
│
├── static/                         # Arquivos estáticos
│   └── css/                        # Folhas de estilo
│       ├── avisos_styles.css       # Estilos para seção de avisos
│       ├── calendario_styles.css   # Estilos para calendário
│       ├── conteudo_styles.css     # Estilos para conteúdo
│       ├── dashboard_styles.css    # Estilos do dashboard
│       ├── docentes_styles.css     # Estilos para docentes
│       ├── infos_curso_styles.css  # Estilos para informações de curso
│       └── login_styles.css        # Estilos da página de login
│
└── templates/                      # Templates Jinja2
    ├── login.html                  # Página de login
    ├── dashboard.html              # Dashboard principal
    │
    ├── avisos/                     # Templates de avisos
    │   ├── list.html               # Lista de avisos
    │   ├── add.html                # Criar aviso
    │   ├── edit.html               # Editar aviso
    │   └── view.html               # Visualizar aviso
    │
    ├── conteudo/                   # Templates de conteúdo
    │   ├── list.html               # Lista de conteúdo
    │   ├── add.html                # Criar conteúdo
    │   └── edit.html               # Editar conteúdo
    │
    ├── docentes/                   # Templates de docentes
    │   ├── list.html               # Lista de docentes
    │   ├── add.html                # Cadastrar docente
    │   ├── edit.html               # Editar docente
    │   └── view.html               # Visualizar docente
    │
    ├── calendario/                 # Templates de calendário
    │   ├── list.html               # Lista de eventos
    │   ├── add.html                # Criar evento
    │   ├── edit.html               # Editar evento
    │   └── view.html               # Visualizar evento
    │
    └── infos_curso/                # Templates de informações de curso
        ├── list.html               # Lista de informações
        ├── add_aps.html            # Adicionar APS
        ├── add_estagio.html        # Adicionar estágio
        ├── add_horas.html          # Adicionar horas complementares
        ├── add_select.html         # Adicionar seletiva
        └── add_tcc.html            # Adicionar TCC
```

---

## 🔌 Integração com API

A aplicação se comunica com uma API REST backend. Todas as requisições são feitas através da biblioteca `requests` e incluem autenticação via Bearer Token.

### Endpoints Principais

A aplicação integra-se com os seguintes endpoints:

- `/auth/login` - Autenticação de usuários
- `/aviso/` - CRUD de avisos
- `/conteudo/` - CRUD de conteúdo acadêmico
- `/professores/` - CRUD de professores
- `/calendario/` - Gestão de calendário
- `/cursos/` - Informações de cursos

### Autenticação

A autenticação é feita através de Bearer Tokens. Após o login, o token é armazenado na sessão e incluído automaticamente em todas as requisições:

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
```

---

## 🧪 Testes

Para testar o sistema localmente:

1. Certifique-se de que a API backend está rodando
2. Inicie a aplicação Flask
3. Acesse `http://127.0.0.1:5000`
4. Faça login com credenciais válidas
5. Teste as funcionalidades disponíveis

### Credenciais de Teste

Use as credenciais fornecidas pela API backend para teste. Exemplo:

- **Admin:** `admin@admin.com` / `1234567`
- Outros usuários conforme configurados na API

---

## 🐛 Troubleshooting

### Problema: Erro ao conectar com a API

**Solução:**
- Verifique se a API está rodando na URL configurada
- Verifique a configuração de `API_BASE_URL` em `app.py`
- Verifique os logs do console para mensagens de erro

### Problema: Erro 401 - Não autorizado

**Solução:**
- Verifique se o token de acesso está sendo enviado corretamente
- Faça logout e login novamente
- Verifique se as credenciais estão corretas

### Problema: Erro 403 - Acesso negado

**Solução:**
- Verifique se seu usuário tem as permissões necessárias para a ação
- Verifique o role do usuário no sistema
- Entre em contato com o administrador do sistema

### Problema: Dependências não instalam

**Solução:**
```bash
# Atualize o pip
python -m pip install --upgrade pip

# Instale as dependências novamente
pip install -r requirements.txt --force-reinstall
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga estes passos:

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. Abra um **Pull Request**

### Padrões de Código

- Siga o estilo PEP 8 para Python
- Use nomes descritivos para variáveis e funções
- Adicione comentários quando necessário
- Mantenha o código limpo e legível

### Estrutura de Commits

Use mensagens de commit descritivas seguindo o padrão:

```
feat: adiciona nova funcionalidade
fix: corrige bug específico
docs: atualiza documentação
style: formatação de código
refactor: refatoração de código
test: adiciona ou corrige testes
chore: tarefas de manutenção
```

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

## 👥 Autores

- **Leonardo** - *Desenvolvimento inicial* - [@leodah20](https://github.com/leodah20)

---

## 📞 Contato

Para dúvidas, sugestões ou problemas:

- **GitHub Issues:** [Abrir uma issue](https://github.com/leodah20/chatbot-front/issues)
- **Email:** (adicione seu email aqui)

---

## 🎯 Roadmap

Funcionalidades planejadas para versões futuras:

- [ ] Sistema de notificações em tempo real
- [ ] Dashboard com gráficos e estatísticas avançadas
- [ ] Exportação de dados (PDF, Excel)
- [ ] Sistema de relatórios personalizados
- [ ] Integração com sistema de mensagens
- [ ] Suporte para múltiplos idiomas
- [ ] Modo escuro/claro
- [ ] PWA (Progressive Web App)

---

## 🙏 Agradecimentos

- Equipe de desenvolvimento do backend
- Comunidade Flask
- Todos os contribuidores do projeto

---

<div align="center">

**⭐ Se este projeto foi útil para você, considere dar uma estrela! ⭐**

Feito com ❤️ pela equipe do ChatBot Frontend

</div>

