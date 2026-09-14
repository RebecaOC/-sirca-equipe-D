# Instalação do ambiente

Siga na ordem. Se algum passo falhar, **não pule**: leve a mensagem de erro para a aula prática.

## 1. Python

Instale o Python 3.11 ou superior. No terminal:

```bash
python --version
```

Deve responder `Python 3.11.x` ou superior. No Windows, se responder algo diferente, tente `py --version`.

## 2. Ambiente virtual do projeto

Dentro da pasta do repositório:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux ou macOS
source .venv/bin/activate

pip install -r requirements.txt
```

O prompt do terminal passa a mostrar `(.venv)`. Sempre ative o ambiente antes de trabalhar.

## 3. Banco de dados PostgreSQL

Há dois caminhos. Escolha **um**.

**Caminho A — instalação direta (recomendado para quem tem máquina própria).**
Instale o PostgreSQL 16 e o pgAdmin. Anote a senha do usuário `postgres`. Crie o banco:

```sql
CREATE DATABASE semear;
```

**Caminho B — contêiner (recomendado para o laboratório).**
Com o Docker instalado:

```bash
cd ambiente
docker compose up -d
```

Isso sobe um PostgreSQL em `localhost:5432`, banco `semear`, usuário `semear`, senha `semear`.

## 4. Verificação

```bash
python ambiente/verificar_ambiente.py
```

O script confere a versão do Python, as bibliotecas, a presença dos arquivos brutos e a conexão com o banco.
**Só considere o ambiente pronto quando todas as linhas mostrarem OK.**

## 5. Editor

Recomendamos o Visual Studio Code com as extensões Python e PostgreSQL. Qualquer editor serve, desde que
você consiga executar o terminal integrado.
