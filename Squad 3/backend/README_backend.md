# README — Backend MINERA Goiás (Squad 3 — Kayo)

Este arquivo explica tudo que existe dentro de `Squad 3/backend/` e `Squad 3/database/`: o que cada arquivo faz, como rodar, e como fazer as alterações mais comuns (adicionar coluna, mudar dado, adicionar rota nova) sem precisar reaprender do zero toda vez.

---

## 1. Visão geral — o que essa parte do projeto faz

Esse componente tem duas peças que trabalham juntas:

1. **Banco de dados MySQL** (`database/`) — guarda os dados de minérios, projetos, empresas, projeções e fontes, organizados em tabelas conectadas.
2. **API em FastAPI** (`backend/`) — um programa Python que fica escutando pedidos via internet (URLs) e responde consultando o banco, devolvendo os dados em formato JSON.

O frontend do Eduardo e o simulador do Henrique não acessam o MySQL diretamente — eles conversam só com a API. Isso é proposital: se um dia trocarmos o banco de lugar (por exemplo, para o Aiven), só a API precisa saber onde o banco está; o resto do time nem percebe a mudança.

---

## 2. Estrutura de arquivos — o que é cada coisa

```
Squad 3/
├── database/
│   ├── schema.sql       → cria as tabelas (rodar 1x, ou toda vez que resetar o banco)
│   ├── seed.sql         → popula com dados fictícios de teste
│   └── import_data.py   → vai importar os dados REAIS quando chegarem (Fase 4)
├── backend/
│   ├── main.py          → o código da API (as rotas)
│   ├── requirements.txt → lista de pacotes Python que o projeto precisa
│   ├── .env             → suas senhas locais (NUNCA vai pro GitHub)
│   ├── .env.example     → modelo do .env, sem senha real (esse SIM vai pro GitHub)
│   └── README.md        → este arquivo
└── documentacao/
    ├── modelo_er.md         → diagrama de como as tabelas se conectam
    └── dicionario_dados.md  → o que cada coluna de cada tabela significa
```

**Regra simples pra saber onde mexer:**
- Quer mudar a estrutura das tabelas (nova coluna, nova tabela)? → `database/schema.sql`
- Quer mudar dados de teste? → `database/seed.sql`
- Quer mudar o que a API responde, ou adicionar uma rota nova? → `backend/main.py`

---

## 3. Como rodar do zero (num Codespace novo, ou depois de muito tempo parado)

```bash
# 1. Ligar o MySQL (sempre precisa rodar isso de novo quando o Codespace reabre)
sudo service mysql start

# 2. Ir para a pasta do projeto
cd "Squad 3"

# 3. Copiar o modelo de variáveis de ambiente e editar a senha
cp backend/.env.example backend/.env
# abra backend/.env no editor e coloque a senha real do seu MySQL local

# 4. Instalar as dependências Python
pip install -r backend/requirements.txt

# 5. Se o banco ainda não existir, criar as tabelas
sudo mysql -u root -p"$(grep DB_PASSWORD backend/.env | cut -d '=' -f2)" < database/schema.sql

# 6. Popular com dados de teste (só se o banco estiver vazio)
sudo mysql -u root -p"$(grep DB_PASSWORD backend/.env | cut -d '=' -f2)" db_minera_goias < database/seed.sql

# 7. Rodar a API
cd backend
uvicorn main:app --reload --port 8000
```

Depois disso, abra a porta 8000 no navegador e acrescente `/docs` no final da URL para ver o Swagger (a tela interativa de testes).

---

## 4. Como o banco de dados funciona (`schema.sql`)

Cada `CREATE TABLE` no `schema.sql` define uma tabela. Os dois conceitos que aparecem em toda tabela:

- **PK (Primary Key)** — a coluna que identifica uma linha de forma única. Ex: `mineral_id` em `tb_minerais`. Nunca se repete.
- **FK (Foreign Key)** — uma coluna que "aponta" para a PK de outra tabela. Ex: `tb_projetos.mineral_id` aponta para `tb_minerais.mineral_id`, dizendo "esse projeto extrai esse mineral específico".

### As 7 tabelas e pra que servem

| Tabela | Serve para |
|---|---|
| `tb_fontes` | Guarda uma vez só o nome/URL/tipo de cada fonte de dado (ANM, EPE, etc.), evitando repetir isso em cada linha |
| `tb_municipios` | Municípios de Goiás com coordenadas |
| `tb_minerais` | Minerais e seus sinônimos |
| `tb_empresas` | Empresas mineradoras |
| `tb_projetos` | Cada projeto/mina — conecta empresa + mineral + município + fonte |
| `tb_intensidade_energetica` | Quanto de energia (MWh) cada mineral gasta por tonelada produzida |
| `tb_projecoes` | Produção e energia projetadas ano a ano (2027–2040), por cenário |

Se tiver dúvida do que uma coluna específica significa, olhe `documentacao/dicionario_dados.md` — e **sempre que adicionar/mudar uma coluna, atualize esse dicionário também**, senão ele fica desatualizado e vira documentação mentirosa.

---

## 5. Como fazer as alterações mais comuns

### 5.1 — Adicionar uma coluna nova em uma tabela existente

Exemplo: adicionar uma coluna `capacidade_instalada_mw` em `tb_projetos`.

```bash
sudo mysql -u root -padmin123 db_minera_goias -e "ALTER TABLE tb_projetos ADD COLUMN capacidade_instalada_mw DECIMAL(10,2);"
```

Depois disso, **três coisas precisam ser atualizadas** (é fácil esquecer uma):
1. `database/schema.sql` — adicione a mesma linha `ADD COLUMN` (ou reescreva o `CREATE TABLE` já com a coluna nova), pra quem recriar o banco do zero já vir com ela.
2. `documentacao/dicionario_dados.md` — adicione uma linha explicando a coluna nova.
3. `backend/main.py` — se a API precisa devolver esse dado, adicione a coluna no `SELECT` da rota correspondente.

### 5.2 — Alterar um dado específico (ex: corrigir o nome de um projeto)

```bash
sudo mysql -u root -padmin123 db_minera_goias -e "UPDATE tb_projetos SET nome_projeto = 'Nome Corrigido' WHERE project_id = 1;"
```

O `WHERE project_id = 1` é essencial — sem ele, o `UPDATE` muda **todas** as linhas da tabela. Sempre teste primeiro com um `SELECT` usando o mesmo `WHERE`, pra confirmar que está pegando só a linha certa:

```bash
sudo mysql -u root -padmin123 db_minera_goias -e "SELECT * FROM tb_projetos WHERE project_id = 1;"
```

### 5.3 — Resetar o banco inteiro e repopular do zero

Útil quando os dados de teste ficaram bagunçados (isso aconteceu com a gente por rodar o seed duas vezes seguidas).

```bash
sudo mysql -u root -padmin123 db_minera_goias -e "
SET FOREIGN_KEY_CHECKS=0;
TRUNCATE TABLE tb_projecoes;
TRUNCATE TABLE tb_intensidade_energetica;
TRUNCATE TABLE tb_projetos;
TRUNCATE TABLE tb_empresas;
TRUNCATE TABLE tb_minerais;
TRUNCATE TABLE tb_municipios;
TRUNCATE TABLE tb_fontes;
SET FOREIGN_KEY_CHECKS=1;
"
sudo mysql -u root -padmin123 db_minera_goias < ../database/seed.sql
```

**Por que `TRUNCATE` e não `DELETE`:** `DELETE FROM tabela` apaga as linhas mas não zera o contador de auto-incremento (o próximo ID continua de onde parou). Isso já nos causou um erro real: os IDs não bateram mais com os números fixos no `seed.sql`, e o banco recusou inserir por violar a Foreign Key. `TRUNCATE` apaga tudo e zera o contador, evitando esse problema.

### 5.4 — Remover uma coluna (cuidado)

```bash
sudo mysql -u root -padmin123 db_minera_goias -e "ALTER TABLE tb_projetos DROP COLUMN nome_da_coluna;"
```

Antes de remover, confirme que nenhuma rota em `main.py` usa essa coluna no `SELECT` — se usar, a API vai quebrar na próxima chamada.

---

## 6. Como a API funciona (`main.py`)

- **FastAPI**: framework Python que transforma funções comuns em rotas de internet, e gera documentação automática (o Swagger em `/docs`).
- **CORS** (`CORSMiddleware`): sem isso, o navegador bloqueia o frontend do Eduardo de acessar sua API quando os dois rodam em domínios/portas diferentes — é uma trava de segurança padrão dos navegadores, o CORS avisa "pode confiar nesse frontend".
- **pymysql**: biblioteca que faz o Python conversar com o MySQL. A função `get_connection()` abre uma conexão nova toda vez que uma rota precisa consultar dados, e fecha logo depois (`conn.close()`), pra não deixar conexões penduradas.

### Cada rota, em detalhe

- **`GET /api/projetos`** — junta 4 tabelas (`tb_projetos`, `tb_empresas`, `tb_minerais`, `tb_municipios`) num `JOIN` e devolve a lista completa com nome da empresa, mineral, município e coordenadas. Usada pelo mapa do Eduardo.
- **`GET /api/projecoes?scenario=referencia`** — filtra `tb_projecoes` pelo cenário pedido na URL (o `?scenario=...` é um parâmetro de consulta). Usada pelo simulador do Henrique.
- **`GET /api/fontes`** — devolve a tabela `tb_fontes` inteira, pra qualquer tela do frontend poder mostrar "de onde vem esse dado".

### Como adicionar uma rota nova

Copie o padrão de uma rota existente. Exemplo, se precisar de uma rota que lista só os minerais:

```python
@app.get("/api/minerais")
def listar_minerais():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tb_minerais")
            return cursor.fetchall()
    finally:
        conn.close()
```

Cole isso no final do `main.py`, salve, e o `--reload` do uvicorn recarrega sozinho (não precisa parar e ligar de novo).

---

## 7. Variáveis de ambiente — `.env` vs `.env.example`

- **`.env`** — tem a senha real do seu MySQL local. Está no `.gitignore`, então **nunca** vai pro GitHub. Cada pessoa do time cria o próprio, com a própria senha.
- **`.env.example`** — mesmo formato, mas com um valor de exemplo no lugar da senha (`coloque_sua_senha_aqui`). Esse vai pro GitHub, serve de instrução pra quem clonar o projeto saber quais variáveis precisa configurar.

Se alguém clonar o repositório do zero e a API der erro de conexão com o banco, o primeiro passo é sempre: `cp .env.example .env` e editar a senha.

---

## 8. Erros comuns e como resolver (baseado no que já enfrentamos)

| Sintoma | Causa | Solução |
|---|---|---|
| `Connection refused` ao rodar a API | MySQL não está ligado (o Codespace hibernou e desligou o serviço) | `sudo service mysql start` |
| Comandos normais (`ls`, `cat`) dão erro de sintaxe SQL | Você ainda está dentro do prompt `mysql>` sem perceber | Digite `exit;` para sair, confirme que o prompt voltou a mostrar o caminho da pasta antes de continuar |
| `ERROR 1452 ... foreign key constraint fails` ao rodar o seed de novo | Rodou `DELETE` antes, que não reseta o contador de ID, e os IDs não batem mais com o que o `seed.sql` espera | Use `TRUNCATE` (com `FOREIGN_KEY_CHECKS=0/1`) em vez de `DELETE` — veja seção 5.3 |
| Erro de sintaxe perto de `INSERT INTO ... WITH RECURSIVE` | Ordem errada: o `WITH RECURSIVE` precisa vir depois da lista de colunas do `INSERT INTO tabela (colunas)` e antes do `SELECT`, não antes do `INSERT` | Reordene a query nesse formato: `INSERT INTO tabela (col1, col2) WITH RECURSIVE cte AS (...) SELECT ...` |
| Terminal "não retorna nada" depois de um comando | Quase sempre é problema de exibição, não do comando em si | Redirecione a saída pra um arquivo e depois leia ele: `comando > /tmp/saida.txt 2>&1` seguido de `cat /tmp/saida.txt` |
| Contagem de linhas maior que o esperado depois do seed | O script foi rodado mais de uma vez sem limpar antes | Sempre resete com `TRUNCATE` (seção 5.3) antes de rodar o seed de novo |

---

## 9. Como atualizar os dados quando chegarem os CSVs reais (Fase 4)

1. Peça pro Squad 1 e Squad 2 as colunas exatas dos arquivos que vão te mandar.
2. Coloque os CSVs em `data/` (crie a pasta se não existir).
3. Complete `database/import_data.py` com os nomes de coluna reais (o arquivo já tem o esqueleto pronto — leitura com pandas, limpeza, `TRUNCATE` das tabelas antigas, inserção via pymysql).
4. Rode: `python database/import_data.py`
5. Confirme com `SHOW TABLES` e um `SELECT COUNT(*)` em cada tabela que os dados entraram.
6. A API não precisa de nenhuma mudança — ela lê direto do banco, então já vai responder com os dados novos automaticamente.

---

## 10. Antes de dar commit — checklist rápido

- [ ] `.env` **não** aparece em `git status` (se aparecer, pare e revise o `.gitignore`)
- [ ] Se mudou o schema, atualizou `documentacao/dicionario_dados.md` e `documentacao/modelo_er.md` junto
- [ ] Se adicionou uma rota nova, testou ela no Swagger (`/docs`) antes de commitar
- [ ] `requirements.txt` está atualizado se instalou algum pacote novo (`pip freeze > requirements.txt`)
