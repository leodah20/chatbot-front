# 📋 Guia de Comandos - Chatbot Frontend

Este documento contém todos os comandos frequentemente usados para desenvolvimento, execução e manutenção do projeto.

---

## 🚀 Configuração Inicial do Projeto

### 1. Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd chatbot-front
```
**Explicação:** Clona o repositório do projeto para sua máquina local e acessa o diretório.

### 2. Criar Ambiente Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```
**Explicação:** Cria um ambiente virtual isolado para instalar as dependências do projeto sem afetar outros projetos Python no seu sistema. Isso é uma boa prática!

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```
**Explicação:** Instala todas as bibliotecas Python necessárias listadas no arquivo `requirements.txt` (Flask, requests, etc.).

---

## ▶️ Executar a Aplicação

### Modo Desenvolvimento (Debug)
```bash
python app.py
```
**Explicação:** Inicia o servidor Flask em modo debug na porta 5000. O servidor recarrega automaticamente quando você faz alterações no código.

**Acesso:** Abra o navegador em `http://localhost:5000` ou `http://127.0.0.1:5000`

### Modo Produção (Usando Gunicorn - Linux/Mac)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
**Explicação:** 
- `-w 4` cria 4 workers (processos) para lidar com múltiplas requisições
- `-b 0.0.0.0:5000` define o bind do servidor
- `app:app` refere-se ao arquivo `app.py` e à variável `app` dentro dele

---

## 📦 Gerenciamento de Dependências

### Listar Pacotes Instalados
```bash
pip list
```
**Explicação:** Mostra todos os pacotes Python instalados no ambiente atual com suas versões.

### Atualizar requirements.txt
```bash
pip freeze > requirements.txt
```
**Explicação:** Gera/atualiza o arquivo requirements.txt com todas as dependências instaladas e suas versões exatas.

### Instalar Nova Dependência
```bash
pip install nome-do-pacote
pip freeze > requirements.txt
```
**Explicação:** Instala um novo pacote e atualiza o requirements.txt para incluir a nova dependência.

### Desinstalar Dependência
```bash
pip uninstall nome-do-pacote
```
**Explicação:** Remove um pacote específico do ambiente.

---

## 🔧 Git - Controle de Versão

### Verificar Status
```bash
git status
```
**Explicação:** Mostra o estado atual do repositório (arquivos modificados, adicionados, etc.).

### Adicionar Arquivos ao Stage
```bash
# Adicionar arquivo específico
git add nome-do-arquivo.py

# Adicionar todos os arquivos modificados
git add .
```
**Explicação:** Prepara os arquivos para serem commitados.

### Fazer Commit
```bash
git commit -m "Descrição clara das mudanças realizadas"
```
**Explicação:** Salva as mudanças no histórico do Git com uma mensagem descritiva.

### Enviar para Repositório Remoto
```bash
git push origin main
```
**Explicação:** Envia os commits locais para o repositório remoto (GitHub, GitLab, etc.).

### Atualizar Repositório Local
```bash
git pull origin main
```
**Explicação:** Baixa e mescla as últimas mudanças do repositório remoto para sua máquina.

### Ver Histórico de Commits
```bash
git log --oneline
```
**Explicação:** Exibe o histórico de commits de forma resumida.

### Criar Nova Branch
```bash
git checkout -b nome-da-branch
```
**Explicação:** Cria e muda para uma nova branch (útil para desenvolver features isoladas).

### Mudar de Branch
```bash
git checkout nome-da-branch
```
**Explicação:** Troca para uma branch existente.

---

## 🧪 Testes e Depuração

### Testar Endpoint da API Manualmente (usando curl)
```bash
# Testar login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@email.com","password":"senha123"}'
```
**Explicação:** Faz uma requisição HTTP POST para testar o endpoint de login sem usar o navegador.

### Verificar Porta em Uso
```bash
# Windows
netstat -ano | findstr :5000

# Linux/Mac
lsof -i :5000
```
**Explicação:** Verifica se a porta 5000 já está sendo usada por outro processo.

### Matar Processo em Porta Específica
```bash
# Windows
taskkill /PID <numero-do-pid> /F

# Linux/Mac
kill -9 <numero-do-pid>
```
**Explicação:** Encerra um processo que está ocupando uma porta necessária.

---

## 🐍 Python - Comandos Úteis

### Verificar Versão do Python
```bash
python --version
# ou
python3 --version
```
**Explicação:** Mostra a versão do Python instalada no sistema.

### Verificar Versão do Pip
```bash
pip --version
```
**Explicação:** Mostra a versão do gerenciador de pacotes pip.

### Atualizar Pip
```bash
python -m pip install --upgrade pip
```
**Explicação:** Atualiza o pip para a versão mais recente.

### Limpar Cache do Pip
```bash
pip cache purge
```
**Explicação:** Remove arquivos em cache do pip para liberar espaço.

---

## 🗂️ Estrutura do Projeto

```
chatbot-front/
│
├── app.py              # Aplicação principal Flask
├── requirements.txt    # Dependências do projeto
├── COMANDOS.md        # Este arquivo!
│
├── static/            # Arquivos estáticos (CSS, JS, imagens)
│   └── style.css
│
└── templates/         # Templates HTML
    ├── base.html
    ├── dashboard.html
    └── login.html
```

---

## 🔑 Variáveis de Ambiente (Futuro)

Para projetos maiores, considere usar variáveis de ambiente:

```bash
# Criar arquivo .env
echo "API_BASE_URL=http://100.75.160.12:5005" > .env
echo "SECRET_KEY=sua-chave-secreta-aqui" >> .env
```

E instalar python-dotenv:
```bash
pip install python-dotenv
```

**Explicação:** Permite armazenar configurações sensíveis fora do código-fonte.

---

## 📝 Notas Importantes

1. **Sempre ative o ambiente virtual** antes de trabalhar no projeto
2. **Nunca commite o arquivo .env** com dados sensíveis
3. **Atualize o requirements.txt** sempre que instalar novos pacotes
4. **Teste localmente** antes de fazer push para o repositório
5. **Use branches** para desenvolver novas features

---

## 🆘 Solução de Problemas Comuns

### "pip não é reconhecido"
```bash
python -m pip install nome-do-pacote
```

### "Porta 5000 já em uso"
Mude a porta no arquivo `app.py` ou mate o processo que está usando a porta.

### "ModuleNotFoundError"
Certifique-se de que o ambiente virtual está ativado e as dependências foram instaladas:
```bash
pip install -r requirements.txt
```

### Erro de conexão com a API
Verifique se a URL da API em `app.py` está correta e se a API está online.

---

## 📚 Recursos Adicionais

- [Documentação Flask](https://flask.palletsprojects.com/)
- [Documentação Requests](https://requests.readthedocs.io/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)

---

**Última atualização:** 19/10/2025

