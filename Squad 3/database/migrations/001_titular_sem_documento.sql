-- Migração 001 — permitir carregar as fontes reais da ANM
--
-- Por que: as fontes que temos identificam o titular apenas pelo NOME.
-- O shapefile cadastral (Squad 1/dados/GO.zip) traz PROCESSO, FASE, NOME, SUBS,
-- USO e AREA_HA, sem CNPJ. O CSV de rodadas traz CPF/CNPJ mascarado
-- ("354.**.***/****54"). O schema anterior exigia documento_cnpj_cpf NOT NULL
-- como chave de tb_empresas, o que obrigaria a inventar documento para carregar
-- qualquer linha real. Esta migração passa a chavear a empresa pelo nome
-- normalizado e deixa o documento como campo opcional e único quando existir.
--
-- Aplicar somente com backup e com as tabelas de negócio vazias. Estas tabelas
-- nunca foram populadas em produção (seed.sql não é aplicado; ver deploy/README.md),
-- portanto não há transformação de dados a fazer — é redefinição de estrutura.
-- O deploy NÃO executa este arquivo: a aplicação é administrativa e manual.

USE db_minera_goias;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Dicionário oficial de substâncias da ANM (Squad 1/dados/Substancia.txt).
--    Preserva o identificador da origem em vez de inventar um substituto.
ALTER TABLE tb_minerais
    ADD COLUMN id_substancia_anm INT NULL AFTER mineral_id,
    ADD UNIQUE KEY uq_minerais_substancia_anm (id_substancia_anm);

-- 2. Empresa passa a ser identificada pelo nome normalizado; documento é opcional.
DROP TABLE IF EXISTS tb_empresas_nova;
CREATE TABLE tb_empresas_nova (
    empresa_id INT AUTO_INCREMENT PRIMARY KEY,
    nome_empresa VARCHAR(200) NOT NULL,
    nome_empresa_normalizado VARCHAR(200) NOT NULL,
    documento_cnpj_cpf VARCHAR(20) NULL,
    tipo_pessoa VARCHAR(50),
    UNIQUE KEY uq_empresas_nome_norm (nome_empresa_normalizado),
    UNIQUE KEY uq_empresas_documento (documento_cnpj_cpf)
);
INSERT INTO tb_empresas_nova (nome_empresa, nome_empresa_normalizado, documento_cnpj_cpf, tipo_pessoa)
    SELECT nome_empresa,
           COALESCE(NULLIF(nome_empresa_normalizado, ''), UPPER(nome_empresa)),
           documento_cnpj_cpf, tipo_pessoa
    FROM tb_empresas;

-- 3. Projeto aponta para a empresa por chave interna, e guarda o que a fonte dá.
ALTER TABLE tb_projetos
    ADD COLUMN empresa_id INT NULL AFTER processo_anm,
    ADD COLUMN titular_nome VARCHAR(200) NULL AFTER empresa_id,
    ADD COLUMN ultimo_evento VARCHAR(120) NULL,
    ADD COLUMN uf VARCHAR(2) NULL,
    ADD COLUMN poligonos INT NOT NULL DEFAULT 0;

-- 4. Um processo pode ter mais de um polígono: sem tabela própria, usar o
--    processo como chave descartaria 772 das 17.428 linhas do shapefile de Goiás.
CREATE TABLE IF NOT EXISTS tb_projeto_poligono (
    poligono_id INT AUTO_INCREMENT PRIMARY KEY,
    processo_anm VARCHAR(30) NOT NULL,
    id_poligono_origem VARCHAR(40),
    area_ha DECIMAL(12,2),
    KEY ix_poligono_processo (processo_anm),
    FOREIGN KEY (processo_anm) REFERENCES tb_projetos(processo_anm)
);

UPDATE tb_projetos p
    JOIN tb_empresas e ON e.documento_cnpj_cpf = p.documento_cnpj_cpf
    JOIN tb_empresas_nova n ON n.nome_empresa_normalizado =
         COALESCE(NULLIF(e.nome_empresa_normalizado, ''), UPPER(e.nome_empresa))
    SET p.empresa_id = n.empresa_id, p.titular_nome = e.nome_empresa;

ALTER TABLE tb_projetos DROP FOREIGN KEY tb_projetos_ibfk_1;
ALTER TABLE tb_projetos DROP COLUMN documento_cnpj_cpf;

DROP TABLE tb_empresas;
RENAME TABLE tb_empresas_nova TO tb_empresas;

ALTER TABLE tb_projetos
    ADD CONSTRAINT fk_projetos_empresa FOREIGN KEY (empresa_id) REFERENCES tb_empresas(empresa_id);

SET FOREIGN_KEY_CHECKS = 1;
