# Endpoints da API - Chatbot Acadêmico

## 📋 **Endpoints Disponíveis**

### **1. Professores** (`/professores`)
- ❌ `GET /professores/` - **NÃO EXISTE** (usar dados mock)
- ✅ `POST /professores/` - Criar professor
- ✅ `PUT /professores/{id}` - Atualizar professor  
- ✅ `DELETE /professores/{id}` - Deletar professor

### **2. Avisos** (`/aviso`)
- ✅ `GET /aviso/` - Listar todos os avisos
- ✅ `GET /aviso/{aviso_id}` - Buscar aviso específico
- ✅ `POST /aviso/` - Criar aviso
- ✅ `PUT /aviso/{aviso_id}` - Atualizar aviso
- ✅ `DELETE /aviso/{aviso_id}` - Deletar aviso

### **3. Alunos** (`/alunos`)
- ❌ `GET /alunos/` - **NÃO EXISTE** (usar dados mock)
- ✅ `POST /alunos/` - Criar aluno
- ✅ `PUT /alunos/{ra}` - Atualizar aluno
- ✅ `DELETE /alunos/{ra}` - Deletar aluno
- ✅ `GET /alunos/email/{email}` - Buscar aluno por email

### **4. Disciplinas** (`/disciplinas`)
- ❌ `GET /disciplinas/` - **NÃO EXISTE** (usar dados mock)
- ✅ `POST /disciplinas/` - Criar disciplina
- ✅ `PUT /disciplinas/{id}` - Atualizar disciplina
- ✅ `DELETE /disciplinas/{id}` - Deletar disciplina
- ✅ `GET /disciplinas/{disciplina}` - Buscar disciplina específica
- ✅ `GET /disciplinas/{nome_disciplina}/cronograma` - Cronograma da disciplina

### **5. Cursos** (`/cursos`)
- ❌ `GET /cursos/` - **NÃO EXISTE** (usar dados mock)
- ✅ `POST /cursos/` - Criar curso
- ✅ `PUT /cursos/{id}` - Atualizar curso
- ✅ `DELETE /cursos/{id}` - Deletar curso
- ✅ `GET /cursos/{curso_id}` - Buscar curso específico

### **6. Cronogramas** (`/cronogramas`)
- ❌ `GET /cronogramas/` - **NÃO EXISTE** (usar dados mock)
- ✅ `POST /cronogramas/` - Criar cronograma
- ✅ `PUT /cronogramas/{id}` - Atualizar cronograma
- ✅ `DELETE /cronogramas/{id}` - Deletar cronograma
- ✅ `GET /cronogramas/{cronograma_id}` - Buscar cronograma específico

### **7. Avaliações** (`/avaliacoes`)
- ❌ `GET /avaliacoes/` - **NÃO EXISTE** (usar dados mock)
- ✅ `POST /avaliacoes/` - Criar avaliação
- ✅ `PUT /avaliacoes/{id}` - Atualizar avaliação
- ✅ `DELETE /avaliacoes/{id}` - Deletar avaliação
- ✅ `GET /avaliacoes/{avaliacao_id}` - Buscar avaliação específica

### **8. Base de Conhecimento** (`/base-conhecimento`)
- ✅ `GET /base-conhecimento/` - Listar todos os itens
- ✅ `GET /base-conhecimento/{item_id}` - Buscar item específico
- ✅ `POST /base-conhecimento/` - Criar item
- ✅ `PUT /base-conhecimento/{id}` - Atualizar item
- ✅ `DELETE /base-conhecimento/{id}` - Deletar item

### **9. Mensagens de Alunos** (`/msg-aluno`)
- ✅ `GET /msg-aluno/` - Listar todas as mensagens
- ✅ `POST /msg-aluno/` - Criar mensagem
- ✅ `PUT /msg-aluno/{id}` - Atualizar mensagem
- ✅ `DELETE /msg-aluno/{id}` - Deletar mensagem

### **10. Documentos** (`/documentos`)
- ✅ `POST /documentos/upload` - Upload de documento
- ✅ `GET /documentos/{filename}` - Download de documento
- ✅ `DELETE /documentos/{filename}` - Deletar documento

## 🔧 **Ajustes Necessários no Frontend**

### **1. Professores (Docentes)**
- ✅ **Manter dados mock** para listagem (GET não existe)
- ✅ **Usar API real** para POST, PUT, DELETE

### **2. Avisos**
- ✅ **Usar API real** para todas as operações
- ✅ **Já implementado** corretamente

### **3. Alunos** (próxima implementação)
- ❌ **Criar CRUD completo** usando dados mock para listagem
- ✅ **Usar API real** para POST, PUT, DELETE

### **4. Disciplinas** (próxima implementação)
- ❌ **Criar CRUD completo** usando dados mock para listagem
- ✅ **Usar API real** para POST, PUT, DELETE

### **5. Cursos** (próxima implementação)
- ❌ **Criar CRUD completo** usando dados mock para listagem
- ✅ **Usar API real** para POST, PUT, DELETE

### **6. Cronogramas** (próxima implementação)
- ❌ **Criar CRUD completo** usando dados mock para listagem
- ✅ **Usar API real** para POST, PUT, DELETE

### **7. Avaliações** (próxima implementação)
- ❌ **Criar CRUD completo** usando dados mock para listagem
- ✅ **Usar API real** para POST, PUT, DELETE

### **8. Base de Conhecimento** (próxima implementação)
- ✅ **Usar API real** para todas as operações
- ❌ **Criar interface** para gerenciar conhecimento do chatbot

### **9. Mensagens de Alunos** (próxima implementação)
- ✅ **Usar API real** para todas as operações
- ❌ **Criar interface** para visualizar mensagens

### **10. Documentos** (próxima implementação)
- ✅ **Usar API real** para todas as operações
- ❌ **Criar interface** para upload/download de documentos

## 📊 **Status Atual**
- ✅ **Avisos**: 100% integrado com API
- ✅ **Professores**: 50% integrado (CRUD sem listagem)
- ❌ **Outros módulos**: 0% integrado (usar dados mock)

## 🎯 **Próximos Passos**
1. Implementar CRUD de Alunos
2. Implementar CRUD de Disciplinas
3. Implementar CRUD de Cursos
4. Implementar CRUD de Cronogramas
5. Implementar CRUD de Avaliações
6. Implementar Base de Conhecimento
7. Implementar Mensagens de Alunos
8. Implementar Upload de Documentos
