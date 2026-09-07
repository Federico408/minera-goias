# Registro de Desenvolvimento — 07/09/2026
## Kayo Silva, Estudante 1 (Squad 3 — Product & AI) | Projeto MINERA Goiás

---

## 1. Checklist — o que foi feito hoje e o que ainda falta

### Modelagem
- [x] Schema corrigido desenhado (com `tb_fontes` normalizada e `tb_empresas` separada de `tb_projetos`)
- [x] `documentacao/dicionario_dados.md` criado e confirmado correto (bate com o schema final)
- [ ] `documentacao/modelo_er.md` — **estava vazio/quebrado no GitHub (retornou 404 ao abrir), precisa ser recriado com o diagrama Mermaid** (conteúdo já entregue nesta sessão, falta só colar e commitar)

### Banco de dados (Fase 1)
- [x] MySQL instalado e configurado no Codespace
- [x] `database/schema.sql` criado com as 7 tabelas, rodado com sucesso
- [x] Confirmado via terminal: banco `db_minera_goias` existe com as 7 tabelas certas

### Dados de teste (Fase 2)
- [x] `database/seed.sql` criado com 3 municípios, 2 minerais, 2 empresas, 2 projetos, 3 fontes, e projeções 2027–2040 para os 3 cenários
- [x] Rodado com sucesso após correção de bugs (ver seção 3) — confirmado 84 linhas em `tb_projecoes` (2 projetos × 3 cenários × 14 anos), número correto

### API (Fase 3)
- [x] `backend/main.py` criado com 3 rotas: `/api/projetos`, `/api/projecoes`, `/api/fontes`
- [x] CORS configurado
- [x] Conexão com banco via variáveis de ambiente (`.env`), não mais senha hardcoded
- [x] Testado via Swagger UI (`/docs`) — todas as rotas retornando dados corretos
- [ ] Confirmar se `backend/.env.example` foi de fato criado e commitado (combinado, mas não confirmado nesta sessão)
- [ ] Confirmar se `backend/requirements.txt` já inclui `python-dotenv` (combinado, mas não confirmado nesta sessão)

### Organização e Git
- [x] Identificado que o repositório usa convenção de pastas por squad (`Squad 1/`, `Squad 3/`) — plano inicial ajustado para seguir esse padrão
- [x] Corrigido typo de pasta: `Squad 3/dcumentacao` → `Squad 3/documentacao`
- [x] Movidos `database/` e `backend/` para dentro de `Squad 3/`
- [x] `.gitignore` criado (protegendo `.env` e `__pycache__/`) e commitado (foi esquecido no primeiro commit, corrigido depois)
- [x] Dois commits feitos e enviados ao GitHub (`feat(squad3-kayo): banco mysql, api fastapi e documentacao organizados em Squad 3/` e o commit de correção do `.gitignore`)
- [ ] `backend/README.md` detalhado — criado nesta sessão, falta colar no repositório e commitar
- [ ] `documentacao/modelo_er.md` — falta colar o conteúdo e commitar (ver acima)

### Fase 4 (depende de outras pessoas)
- [ ] Aguardando CSVs reais do Squad 1 (Eliel/Gabriel) e Squad 2 (Federico/Henrique)
- [x] Esqueleto de `database/import_data.py` já preparado, pronto para adaptar quando os arquivos chegarem

---

## 2. Pontos de desenvolvimento — observações e decisões em aberto

Essas são questões que não têm resposta fechada ainda e precisam de atenção nos próximos dias:

1. **Qual plataforma usar para hospedar o banco de dados compartilhado?**
   Hoje o MySQL roda só dentro do Codespace pessoal do Kayo — cada pessoa do time que rodar o projeto localmente terá seu próprio banco isolado, sem dados em comum. Isso é aceitável para a entrega técnica de 21/09 (que avalia código e commits), mas não permite colaboração real nem serve para a entrega final de dezembro. Decisão tomada: migrar para o **Aiven** (MySQL gratuito permanente, sem cartão de crédito). Avaliado e descartado por ora: **AWS RDS** — tecnicamente também tem opção gratuita, mas exige cartão de crédito na maioria dos casos, o tier grátis expira em 12 meses e cobra automaticamente depois, e a configuração é mais complexa (VPC, security groups). Migração para o Aiven ainda **não foi implementada** — ficou combinado fazer depois.

2. **A API também precisa de um lugar fixo para rodar.**
   Mesmo com o banco no Aiven, a API (`main.py`) continua rodando só dentro do Codespace do Kayo, que desliga por inatividade. Para o Eduardo e o Henrique consumirem a API de verdade (não só testar localmente), ela precisa ficar hospedada em algum serviço que fique sempre no ar (ex: Render). Isso ainda não foi decidido nem implementado — é o próximo problema depois de resolver o banco.

3. **Simplificação `project_id` = `operation_id`.**
   A rubrica original do projeto pede chaves separadas para projeto e operação (`project_id` e `operation_id`). Nesta primeira versão, tratamos as duas como a mesma coisa, documentado no `modelo_er.md`, porque o Squad 1 ainda não definiu se um projeto minerário terá múltiplas operações distintas. Isso pode precisar ser revisto quando os dados reais chegarem.

4. **Extensão "Database Client" (interface visual do banco) nunca funcionou.**
   Foi instalada, mas a interface não abriu ou não mostrou o formulário de conexão corretamente, mesmo depois de tentar reload da janela. Abandonamos essa abordagem e passamos a usar o terminal MySQL diretamente, que funcionou sem problema. Se quiser retomar a visualização gráfica no futuro (é conveniente para navegar nas tabelas visualmente), pode valer desinstalar e reinstalar a extensão do zero, mas não é bloqueador para nada do trabalho atual.

5. **Nomes exatos das colunas dos CSVs do Squad 1 e Squad 2 ainda são desconhecidos.**
   O `import_data.py` tem só um esqueleto — os nomes reais de coluna precisam ser confirmados com Eliel/Gabriel (Squad 1) e Federico/Henrique (Squad 2) antes de completar o script.

6. **Confirmar com Rodrigo (líder do projeto) se `Squad 3/` é de fato a convenção oficial de pastas para todos os squads.**
   Parece ser, já que `Squad 1/` já existia no repositório, mas vale uma confirmação explícita para evitar reestruturações futuras.

---

## 3. Relato detalhado da sessão

### Contexto inicial
A sessão começou com uma revisão crítica de um guia passo a passo gerado por outra IA (NotebookLM) para a entrega técnica de Kayo (Estudante 1, Squad 3). A análise identificou que o guia, apesar de bem escrito para um iniciante seguir, tinha lacunas em relação à rubrica oficial do projeto: faltava a modelagem (diagrama ER e dicionário de dados) como entregável separado, faltava uma tabela de fontes normalizada (o que quebraria a rota `/api/fontes` proposta), não separava empresa de projeto, mandava commitar a senha do banco direto no código, e não avisava que o MySQL do Codespace precisa ser reiniciado toda vez que o ambiente hiberna.

Com base nisso, foi produzido um plano revisado completo, incluindo: uma Fase 0 de modelagem (ER em Mermaid + dicionário de dados), o `schema.sql` corrigido com a tabela `tb_fontes`, separação de `tb_empresas` e `tb_projetos`, uso de variáveis de ambiente (`.env`) em vez de senha hardcoded, um `requirements.txt` para reprodutibilidade, e um `README` documentando o procedimento de atualização de dados — tudo com explicações do "porquê" de cada decisão, para fins de aprendizado.

### Execução — Fase 1 (banco de dados)

A primeira dificuldade real foi de interface: a extensão "Database Client" do VS Code, sugerida no guia original para visualizar o banco graficamente, nunca funcionou — o ícone não aparecia na barra lateral, e o que parecia ser o formulário de conexão era, na verdade, apenas uma imagem estática da página de descrição da extensão. Depois de tentar reload de janela sem sucesso, a decisão foi abandonar a interface gráfica e seguir 100% por terminal.

A segunda dificuldade foi a criação do arquivo `schema.sql` em si. A primeira tentativa foi colar o conteúdo inteiro do SQL diretamente no terminal via `cat > arquivo << EOF`, mas o texto saiu embaralhado — o terminal do navegador não lida bem com blocos de texto muito longos colados de uma vez. Isso gerou uma sequência de comandos de verificação (`ls`, `cat`, `wc -l`) que pareciam não retornar nada, criando a impressão de que nada estava funcionando. Depois de investigar, ficou claro que dois problemas distintos estavam se sobrepondo:

1. A colagem de texto longo no terminal do navegador de fato corrompe o conteúdo às vezes — o arquivo `schema.sql` acabou sendo criado corretamente pelo **editor de texto do VS Code** (não pelo terminal), que não tem esse problema.
2. Em um momento posterior, comandos que pareciam "não retornar nada" na verdade estavam sendo digitados **dentro do prompt interativo do `mysql>`**, sem que isso fosse percebido — o MySQL tentava interpretar comandos de terminal como `ls` e `cat` como SQL, gerando erros de sintaxe que pareciam desconectados do que estava sendo pedido.

A solução que resolveu a incerteza de forma definitiva foi parar de confiar em texto colado diretamente no chat e passar a redirecionar toda saída de comando para um arquivo (`comando > /tmp/saida.txt 2>&1` seguido de `cat /tmp/saida.txt`), o que finalmente confirmou: o banco `db_minera_goias` e as 7 tabelas foram criados com sucesso desde a primeira tentativa — o problema nunca foi o schema em si, foi a visibilidade do resultado.

### Execução — Fase 2 (dados de teste)

O `seed.sql` incluía uma consulta com `WITH RECURSIVE` para gerar automaticamente os 14 anos de projeção (2027–2040) sem precisar digitar cada ano manualmente. A primeira tentativa de execução falhou com erro de sintaxe. A causa raiz foi diagnosticada incorretamente no início (suspeita de que o MySQL instalado seria uma versão antiga ou MariaDB, que teria suporte diferente a CTEs recursivos) — a versão foi confirmada como MySQL 8.0.46, que suporta a sintaxe normalmente. O erro real era de posicionamento: o `WITH RECURSIVE` precisa vir depois da lista de colunas do `INSERT INTO tabela (colunas)` e antes do `SELECT`, não antes do `INSERT` inteiro. Corrigido o posicionamento, o script rodou.

Isso gerou um novo problema: como a primeira tentativa (que falhou) já havia inserido as tabelas anteriores (fontes, municípios, minerais, empresas, projetos, intensidade energética) antes de travar na parte de projeções, e a segunda tentativa (corrigida) rodou o arquivo inteiro de novo do zero, os dados dessas tabelas ficaram duplicados. A contagem de `tb_projecoes` chegou a 168 linhas em vez das 84 esperadas.

A tentativa de corrigir isso com `DELETE FROM tabela` revelou outro problema de banco de dados: `DELETE` apaga as linhas, mas não reseta o contador de auto-incremento. Como o `seed.sql` usa números de ID fixos (ex: `company_id = 1`) para conectar projetos a empresas, e o MySQL continuou contando a partir de onde tinha parado (gerando `company_id = 3` e `4` nas empresas novas), o `INSERT` dos projetos falhou com erro de violação de chave estrangeira (`FOREIGN KEY constraint fails`), porque tentava referenciar um `company_id` que não existia mais com aquele número.

A correção definitiva foi usar `TRUNCATE TABLE` em vez de `DELETE` (que reseta o contador de auto-incremento), desativando temporariamente a checagem de chaves estrangeiras (`SET FOREIGN_KEY_CHECKS=0`) para poder truncar tabelas na ordem certa, e rodando o `seed.sql` uma única vez depois disso. O resultado final confirmado foi 84 linhas em `tb_projecoes` — exatamente o esperado (2 projetos × 3 cenários × 14 anos).

### Execução — Fase 3 (API)

A instalação das dependências (`fastapi`, `uvicorn`, `pymysql`, `pandas`) e a criação do `main.py` correram sem incidentes técnicos. Foi adicionada, além do que estava no plano original, a biblioteca `python-dotenv` para carregar variáveis de ambiente de um arquivo `.env`, evitando a senha do banco hardcoded no código-fonte — prática que o guia original não tinha (ele sugeria colar a senha direto no `main.py` e commitar esse arquivo).

O servidor subiu com `uvicorn main:app --reload --port 8000` sem erros, e o teste via Swagger UI (`/docs`) confirmou as três rotas funcionando corretamente, retornando dados reais do banco em formato JSON.

### Organização do repositório

Ao preparar o primeiro commit, foi identificado que o repositório do time já seguia uma convenção de pastas por squad (`Squad 1/`, `Squad 3/`) que não tinha sido informada previamente — o plano inicial sugeria uma estrutura na raiz do projeto (`database/`, `backend/`, `documentation/`). Também foi descoberto que os arquivos `dicionario_dados.md` e `modelo_er.md` já haviam sido criados por Kayo diretamente pela interface web do GitHub, dentro de uma pasta com erro de digitação (`Squad 3/dcumentacao`, faltando o "o").

A correção envolveu: `git pull` para sincronizar o Codespace com o que já existia no GitHub, `git mv` para corrigir o nome da pasta (`dcumentacao` → `documentacao`), e `mv` para mover `database/` e `backend/` para dentro de `Squad 3/`. Antes do commit final, foi feita uma verificação deliberada do `git status` para confirmar que o arquivo `.env` (com a senha real) não estava na lista de arquivos a serem enviados — confirmado que não estava, o commit e push foram concluídos com sucesso.

Um detalhe escapou nesse primeiro commit: o próprio arquivo `.gitignore` nunca tinha sido adicionado ao Git (aparecia como "untracked" no `git status"), então a proteção existia localmente mas não estava registrada no repositório compartilhado. Foi corrigido com um commit adicional.

### Verificação de documentação e hospedagem

Ao revisar os arquivos de documentação já existentes no repositório, `dicionario_dados.md` foi confirmado como correto e alinhado com o schema final. Já `modelo_er.md` retornou erro "404: Not Found" ao ser aberto — o arquivo existe no nome, mas está vazio ou corrompido no GitHub, e precisa ser recriado com o diagrama Mermaid (conteúdo já preparado nesta sessão).

Também foi discutida a questão de colaboração real entre o time: como o banco de dados hoje roda apenas dentro do Codespace pessoal de Kayo, cada membro do time que rodasse o projeto localmente teria seu próprio banco isolado, sem dados compartilhados — o que não é colaboração de fato, apenas cada pessoa testando sozinha. Duas alternativas foram avaliadas: manter como está (suficiente para a entrega de 21/09, que avalia código e commits, não uma aplicação ao vivo) ou migrar para um banco de dados hospedado na nuvem, acessível por todos. A segunda opção foi escolhida. Foram avaliadas duas plataformas: **Aiven** (MySQL gratuito permanente, sem necessidade de cartão de crédito) e **AWS RDS** (também tem tier gratuito, mas exige cartão de crédito na maioria dos casos, expira em 12 meses e depois cobra automaticamente, além de exigir configuração mais complexa de rede). O Aiven foi escolhido como a opção mais simples e segura para o prazo e o nível de experiência da equipe. A migração em si ainda não foi realizada — ficou planejada para depois da entrega de 21/09.
