CREATE DATABASE IF NOT EXISTS db_minera_goias;
USE db_minera_goias;

CREATE TABLE tb_fontes (
    source_id VARCHAR(30) PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    instituicao VARCHAR(150),
    url_arquivo VARCHAR(500),
    cobertura VARCHAR(100),
    notas_metodologicas VARCHAR(500)
);

CREATE TABLE tb_municipios (
    codigo_ibge VARCHAR(10) PRIMARY KEY,
    nome_municipio VARCHAR(120) NOT NULL
);

CREATE TABLE tb_minerais (
    mineral_id INT AUTO_INCREMENT PRIMARY KEY,
    -- Identificador do dicionário oficial da ANM (Squad 1/dados/Substancia.txt).
    id_substancia_anm INT NULL UNIQUE,
    mineral_name VARCHAR(100) NOT NULL,
    sinonimos VARCHAR(300),
    observacao VARCHAR(300)
);

-- As fontes cadastrais identificam o titular pelo nome; o documento aparece
-- ausente (shapefile) ou mascarado (rodadas de disponibilidade). Por isso a
-- chave é o nome normalizado e o documento é opcional.
CREATE TABLE tb_empresas (
    empresa_id INT AUTO_INCREMENT PRIMARY KEY,
    nome_empresa VARCHAR(200) NOT NULL,
    nome_empresa_normalizado VARCHAR(200) NOT NULL UNIQUE,
    documento_cnpj_cpf VARCHAR(20) NULL UNIQUE,
    tipo_pessoa VARCHAR(50)
);

CREATE TABLE tb_projetos (
    processo_anm VARCHAR(30) PRIMARY KEY,
    empresa_id INT NULL,
    titular_nome VARCHAR(200),
    ultimo_evento VARCHAR(120),
    uf VARCHAR(2),
    poligonos INT NOT NULL DEFAULT 0,
    substancia_anm VARCHAR(150),
    mineral_id INT,
    fase VARCHAR(100),
    uso VARCHAR(100),
    -- Preenchida apenas quando o processo tem um único polígono; com vários, a
    -- área fica em tb_projeto_poligono e não é somada (os polígonos podem se sobrepor).
    area_ha DECIMAL(12,2),
    categoria VARCHAR(50),
    source_id VARCHAR(30),
    data_acesso DATE,
    periodo_referencia VARCHAR(20),
    valor_observado_estimado ENUM('Real','Projetado') DEFAULT 'Real',
    status_validacao VARCHAR(50),
    responsavel_validacao VARCHAR(100),
    FOREIGN KEY (empresa_id) REFERENCES tb_empresas(empresa_id),
    FOREIGN KEY (mineral_id) REFERENCES tb_minerais(mineral_id),
    FOREIGN KEY (source_id) REFERENCES tb_fontes(source_id)
);

-- Um processo pode ter vários polígonos (há casos com mais de cem). Guardar a
-- geometria em tabela própria evita perder linhas ao usar o processo como chave.
CREATE TABLE tb_projeto_poligono (
    poligono_id INT AUTO_INCREMENT PRIMARY KEY,
    processo_anm VARCHAR(30) NOT NULL,
    -- O identificador do shapefile se repete entre processos e até dentro do
    -- mesmo processo, então é atributo de origem, nunca chave.
    id_poligono_origem VARCHAR(40),
    area_ha DECIMAL(12,2),
    KEY ix_poligono_processo (processo_anm),
    FOREIGN KEY (processo_anm) REFERENCES tb_projetos(processo_anm)
);

CREATE TABLE tb_projeto_municipio (
    processo_anm VARCHAR(30) NOT NULL,
    codigo_ibge VARCHAR(10) NOT NULL,
    PRIMARY KEY (processo_anm, codigo_ibge),
    FOREIGN KEY (processo_anm) REFERENCES tb_projetos(processo_anm),
    FOREIGN KEY (codigo_ibge) REFERENCES tb_municipios(codigo_ibge)
);

CREATE TABLE tb_intensidade_energetica (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mineral_id INT NOT NULL,
    intensidade_mwh_t DECIMAL(10,4) NOT NULL,
    production_basis ENUM('ROM','Beneficiado') NOT NULL,
    source_id VARCHAR(30),
    data_acesso DATE,
    periodo_referencia VARCHAR(20),
    valor_observado_estimado ENUM('Real','Projetado') DEFAULT 'Real',
    status_validacao VARCHAR(50),
    responsavel_validacao VARCHAR(100),
    FOREIGN KEY (mineral_id) REFERENCES tb_minerais(mineral_id),
    FOREIGN KEY (source_id) REFERENCES tb_fontes(source_id)
);

CREATE TABLE tb_projecoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mineral_id INT NOT NULL,
    processo_anm VARCHAR(30) NOT NULL,
    year INT NOT NULL,
    scenario ENUM('conservador','referencia','expansao') NOT NULL,
    projected_production DECIMAL(14,2),
    unidade_producao VARCHAR(10) NOT NULL DEFAULT 't',
    energy_demand_mwh DECIMAL(14,2),
    source_id VARCHAR(30),
    data_acesso DATE,
    periodo_referencia VARCHAR(20),
    valor_observado_estimado ENUM('Real','Projetado') DEFAULT 'Projetado',
    status_validacao VARCHAR(50),
    responsavel_validacao VARCHAR(100),
    FOREIGN KEY (mineral_id) REFERENCES tb_minerais(mineral_id),
    FOREIGN KEY (processo_anm) REFERENCES tb_projetos(processo_anm),
    FOREIGN KEY (source_id) REFERENCES tb_fontes(source_id)
);
