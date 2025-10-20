# 🔐 Guia de Depuração de Autenticação - Chatbot Frontend

## ✅ Melhorias Implementadas

### 1. **Sistema de Logs Detalhados**
O código agora inclui logs extensivos para debug da autenticação:
- Status HTTP das requisições
- Respostas completas da API
- Dados do usuário recebidos
- Estrutura dos dados JSON
- Erros detalhados em cada etapa

### 2. **Extração Flexível de Dados do Usuário**
O sistema agora tenta múltiplos formatos de resposta da API:

**Para o ID do usuário:**
- `id`
- `id_professor`
- `id_coordenador`
- `id_aluno`
- `user_id`
- `userId`

**Para o nome do usuário:**
- `nome`
- `name`
- `username`
- Parte do email (fallback)

**Para o tipo de usuário:**
- `tipo`
- `type`
- `role`
- `usuario` (padrão)

### 3. **Tratamento de Erros HTTP Aprimorado**
- **401**: Credenciais inválidas
- **404**: Endpoint não encontrado
- **422**: Validação de dados (com detalhes do erro)
- **Outros**: Mensagem genérica com código de status
- **ConnectionError**: API offline
- **Timeout**: Servidor não responde
- **RequestException**: Erros de comunicação
- **Exception**: Erros inesperados com traceback completo

### 4. **Dashboard com Debug**
- Logs de acesso ao dashboard
- Informações do usuário logado
- Status das requisições aos endpoints
- Tipo e tamanho dos dados recebidos
- Tratamento flexível de respostas (lista ou dicionário)

### 5. **Formulário de Login Corrigido**
- Campo `name="email"` (antes era `username`)
- Campo `name="password"` 
- Ambos sincronizados com o backend

## 🧪 Como Testar a Autenticação

### Passo 1: Verificar os Logs
Ao tentar fazer login, verifique no terminal os logs de debug:

```
[DEBUG] Tentando login com: usuario@exemplo.com
[DEBUG] Status Code: 200
[DEBUG] Response: {"id": 123, "nome": "Usuário Teste", ...}
[DEBUG] User Data JSON: {...}
[DEBUG] Session User: {'id': 123, 'nome': 'Usuário Teste', ...}
```

### Passo 2: Verificar a Resposta da API
Se o login falhar, observe:
1. O status code HTTP retornado
2. O conteúdo da resposta (`Response:`)
3. A estrutura dos dados JSON recebidos

### Passo 3: Verificar a Sessão
Após login bem-sucedido, o sistema cria uma sessão com:
```python
{
    'id': <id_do_usuario>,
    'nome': '<nome_do_usuario>',
    'email': '<email>',
    'tipo': '<tipo_usuario>',
    'raw_data': { ... }  # Dados completos da API
}
```

## 🔍 Diagnóstico de Problemas Comuns

### Problema: "Nenhum ID de usuário encontrado"
**Causa**: A API retorna dados em um formato não esperado.  
**Solução**: 
1. Verifique os logs `[DEBUG] User Data JSON:`
2. Verifique `[DEBUG] Estrutura recebida:`
3. Adicione o campo correto no código (linhas 62-69 do `app.py`)

### Problema: "Credenciais inválidas" (401)
**Causa**: Email ou senha incorretos, ou API não reconhece as credenciais.  
**Solução**:
1. Verifique se o email e senha estão corretos
2. Teste diretamente na API usando curl/Postman
3. Verifique se a API espera o formato `{"email": "...", "password": "..."}`

### Problema: "Endpoint não encontrado" (404)
**Causa**: A URL do endpoint de login está incorreta.  
**Solução**:
1. Verifique `API_BASE_URL` no `app.py` (linha 12)
2. Confirme que a API está rodando em `http://100.75.160.12:5005`
3. Teste o endpoint: `curl -X POST http://100.75.160.12:5005/login`

### Problema: "Erro de conexão"
**Causa**: API está offline ou não acessível.  
**Solução**:
1. Verifique se a API está rodando
2. Teste: `curl http://100.75.160.12:5005`
3. Verifique firewall/rede

### Problema: Dashboard não carrega dados
**Causa**: Endpoints da API retornam 404 ou dados em formato inesperado.  
**Solução**:
1. Verifique logs `[DEBUG] Buscando {key} em:`
2. Verifique `[DEBUG] {key} - Status:` para cada endpoint
3. Os endpoints que retornam 404 são ignorados (dados vazios)

## 📝 Estrutura Esperada da Resposta da API

### Login (POST /login)
```json
{
  "id": 123,
  "nome": "João Silva",
  "email": "joao@exemplo.com",
  "tipo": "professor"
}
```

**OU** qualquer variação com os campos mencionados na seção "Extração Flexível".

### Endpoints de Dados (GET /aviso/, etc)
```json
[
  {"id": 1, "titulo": "Aviso 1", ...},
  {"id": 2, "titulo": "Aviso 2", ...}
]
```

**OU**

```json
{
  "data": [...],
  "items": [...],
  "avisos": [...]
}
```

## 🚀 Testando Manualmente com cURL

### Testar Login
```bash
curl -X POST http://100.75.160.12:5005/login \
  -H "Content-Type: application/json" \
  -d '{"email":"seu@email.com","password":"suasenha"}'
```

### Testar Avisos
```bash
curl -X GET http://100.75.160.12:5005/aviso/
```

## 🔧 Configuração Atual

- **API Base URL**: `http://100.75.160.12:5005`
- **Porta Frontend**: `5001`
- **Endpoints monitorados**:
  - `/aviso/`
  - `/disciplina/`
  - `/professor/`
  - `/aluno/`

## 📊 Informações Adicionais

- A sessão persiste entre requisições (`session.permanent = True`)
- Dados brutos da API são armazenados em `session['user']['raw_data']` para debug
- O sistema é tolerante a falhas - endpoints que falham retornam listas vazias
- Mensagens flash informam o usuário sobre erros e sucessos

---

**Última atualização**: 19/10/2025
**Versão**: 1.0

