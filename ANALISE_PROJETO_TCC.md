# Análise do Projeto TCC - Chatbot Assistente Acadêmico

## 📋 Estrutura do Projeto Analisada

### 1. **ChatBot_API** (Backend FastAPI)
- **Tecnologia:** FastAPI + Supabase
- **Endpoints principais:**
  - `/professores/` - CRUD de professores
  - `/aviso/` - CRUD de avisos
  - `/alunos/` - CRUD de alunos
  - `/coordenador/` - CRUD de coordenadores
  - `/disciplina/` - CRUD de disciplinas
  - `/cronograma/` - CRUD de cronogramas
  - `/avaliacao/` - CRUD de avaliações
  - `/base_conhecimento/` - Base de conhecimento do chatbot

### 2. **chatbot_rasa** (IA/NLP)
- **Tecnologia:** Rasa Framework
- **Funcionalidades:**
  - Processamento de linguagem natural
  - Ações customizadas que consomem a API
  - Integração com Microsoft Teams
  - Busca de avisos e cronogramas

### 3. **chatbot-front** (Painel Administrativo)
- **Tecnologia:** Flask + HTML/CSS/JS
- **Status atual:** Parcialmente implementado
- **Funcionalidades existentes:**
  - Sistema de login
  - Dashboard básico
  - CRUD de professores (docentes)

## 🎯 Plano de Desenvolvimento - Painel Administrativo Completo

### **FASE 1: Estrutura Base (CONCLUÍDA)**
- ✅ Sistema de autenticação
- ✅ Dashboard principal
- ✅ CRUD de professores
- ✅ Design responsivo com identidade visual UNIP

### **FASE 2: Gestão de Avisos (PRIORIDADE ALTA)**
```python
# Novos endpoints a implementar no frontend:
- GET /avisos - Listar avisos
- POST /avisos - Criar aviso
- PUT /avisos/{id} - Editar aviso
- DELETE /avisos/{id} - Remover aviso
```

**Funcionalidades:**
- Lista de avisos com paginação
- Formulário de criação/edição
- Filtros por data, autor, tipo
- Preview de avisos
- Sistema de notificações

### **FASE 3: Gestão de Disciplinas e Cronogramas**
```python
# Endpoints para disciplinas:
- GET /disciplinas - Listar disciplinas
- POST /disciplinas - Criar disciplina
- PUT /disciplinas/{id} - Editar disciplina
- DELETE /disciplinas/{id} - Remover disciplina

# Endpoints para cronogramas:
- GET /cronogramas - Listar cronogramas
- POST /cronogramas - Criar cronograma
- PUT /cronogramas/{id} - Editar cronograma
- DELETE /cronogramas/{id} - Remover cronograma
```

**Funcionalidades:**
- Gestão de disciplinas por curso
- Cronogramas visuais (calendário)
- Associação professor-disciplina
- Horários de aula

### **FASE 4: Gestão de Alunos e Cursos**
```python
# Endpoints para alunos:
- GET /alunos - Listar alunos
- POST /alunos - Criar aluno
- PUT /alunos/{ra} - Editar aluno
- DELETE /alunos/{ra} - Remover aluno

# Endpoints para cursos:
- GET /cursos - Listar cursos
- POST /cursos - Criar curso
- PUT /cursos/{id} - Editar curso
- DELETE /cursos/{id} - Remover curso
```

**Funcionalidades:**
- Matrícula de alunos em disciplinas
- Gestão de cursos
- Relatórios de alunos por disciplina
- Histórico acadêmico

### **FASE 5: Base de Conhecimento e Avaliações**
```python
# Endpoints para base de conhecimento:
- GET /base-conhecimento - Listar itens
- POST /base-conhecimento - Criar item
- PUT /base-conhecimento/{id} - Editar item
- DELETE /base-conhecimento/{id} - Remover item

# Endpoints para avaliações:
- GET /avaliacoes - Listar avaliações
- POST /avaliacoes - Criar avaliação
- PUT /avaliacoes/{id} - Editar avaliação
- DELETE /avaliacoes/{id} - Remover avaliação
```

**Funcionalidades:**
- Editor de conteúdo para o chatbot
- Gestão de perguntas e respostas
- Avaliações e provas
- Relatórios de desempenho

### **FASE 6: Relatórios e Analytics**
- Dashboard com métricas
- Relatórios de uso do chatbot
- Estatísticas de disciplinas
- Relatórios de alunos

## 🔧 Melhorias Técnicas Sugeridas

### **1. Estrutura de Arquivos**
```
templates/
├── dashboard.html
├── login.html
├── avisos/
│   ├── list.html
│   ├── add.html
│   ├── edit.html
│   └── view.html
├── disciplinas/
│   ├── list.html
│   ├── add.html
│   ├── edit.html
│   └── view.html
├── alunos/
│   ├── list.html
│   ├── add.html
│   ├── edit.html
│   └── view.html
└── relatorios/
    ├── dashboard.html
    └── relatorios.html
```

### **2. Rotas Flask Organizadas**
```python
# app.py - Estrutura modular
from flask import Blueprint

# Blueprints para cada módulo
avisos_bp = Blueprint('avisos', __name__, url_prefix='/avisos')
disciplinas_bp = Blueprint('disciplinas', __name__, url_prefix='/disciplinas')
alunos_bp = Blueprint('alunos', __name__, url_prefix='/alunos')
relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

# Registrar blueprints
app.register_blueprint(avisos_bp)
app.register_blueprint(disciplinas_bp)
app.register_blueprint(alunos_bp)
app.register_blueprint(relatorios_bp)
```

### **3. Sistema de Permissões**
```python
# Decorators para diferentes níveis de acesso
def admin_required(f):
    """Apenas administradores"""
    pass

def professor_required(f):
    """Professores e administradores"""
    pass

def coordenador_required(f):
    """Coordenadores e administradores"""
    pass
```

### **4. Validação e Tratamento de Erros**
```python
# Validação de dados
def validate_form_data(form_data, required_fields):
    """Valida dados do formulário"""
    pass

# Tratamento de erros da API
def handle_api_error(response):
    """Trata erros da API de forma consistente"""
    pass
```

## 🚀 Próximos Passos Recomendados

### **Imediato (Esta Semana)**
1. **Implementar CRUD de Avisos**
   - Lista de avisos
   - Formulário de criação/edição
   - Integração com API

2. **Melhorar Dashboard**
   - Estatísticas em tempo real
   - Gráficos de uso
   - Notificações

### **Curto Prazo (2-3 Semanas)**
1. **CRUD de Disciplinas e Cronogramas**
2. **Sistema de permissões por usuário**
3. **Melhorias na interface**

### **Médio Prazo (1-2 Meses)**
1. **CRUD de Alunos e Cursos**
2. **Base de conhecimento**
3. **Sistema de relatórios**

### **Longo Prazo (2-3 Meses)**
1. **Analytics avançados**
2. **Integração com Teams**
3. **Testes automatizados**

## 📊 Métricas de Sucesso

- **Funcionalidade:** 100% dos endpoints da API integrados
- **Usabilidade:** Interface intuitiva e responsiva
- **Performance:** Tempo de resposta < 2s
- **Segurança:** Autenticação e autorização robustas
- **Manutenibilidade:** Código bem documentado e modular

## 🎨 Design System

### **Cores UNIP**
- Primário: #023D71
- Secundário: #075EBD
- Accent: #1583FF
- Sucesso: #329959
- Erro: #DC3545

### **Componentes**
- Cards com sombra sutil
- Botões com estados (hover, active, disabled)
- Formulários com validação visual
- Tabelas responsivas
- Modais para confirmações

---

**Status:** Análise completa realizada
**Próxima ação:** Implementar CRUD de Avisos
**Responsável:** Equipe de desenvolvimento
**Prazo:** Conforme cronograma definido
