CREATE DATABASE IF NOT EXISTS db_minera_goias;
USE db_minera_goias;

CREATE TABLE tb_fontes (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    nome_fonte VARCHAR(150) NOT NULL,
    source_url VARCHAR(500),
    tipo_fonte ENUM('Oficial','Companhia','Setorial','Imprensa') NOT NULL,
    descricao VARCHAR(300)
);

CREATE TABLE tb_municipios (
    municipality_id INT AUTO_INCREMENT PRIMARY KEY,
    nome_municipio VARCHAR(120) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);

CREATE TABLE tb_minerais (
    mineral_id INT AUTO_INCREMENT PRIMARY KEY,
    mineral_name VARCHAR(100) NOT NULL,
    sinonimos VARCHAR(300),
    observacao VARCHAR(300)
);

CREATE TABLE tb_empresas (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    nome_empresa VARCHAR(150) NOT NULL
);

CREATE TABLE tb_projetos (
    project_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    mineral_id INT NOT NULL,
    municipality_id INT NOT NULL,
    nome_projeto VARCHAR(150) NOT NULL,
    source_id INT,
    data_acesso DATE,
    periodo_referencia VARCHAR(20),
    valor_observado_estimado ENUM('Real','Projetado') DEFAULT 'Real',
    status_validacao VARCHAR(50),
    responsavel_validacao VARCHAR(100),
    FOREIGN KEY (company_id) REFERENCES tb_empresas(company_id),
    FOREIGN KEY (mineral_id) REFERENCES tb_minerais(mineral_id),
    FOREIGN KEY (municipality_id) REFERENCES tb_municipios(municipality_id),
    FOREIGN KEY (source_id) REFERENCES tb_fontes(source_id)
);

CREATE TABLE tb_intensidade_energetica (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mineral_id INT NOT NULL,
    intensidade_mwh_t DECIMAL(10,4) NOT NULL,
    production_basis ENUM('ROM','Beneficiado') NOT NULL,
    source_id INT,
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
    project_id INT NOT NULL,
    year INT NOT NULL,
    scenario ENUM('conservador','referencia','expansao') NOT NULL,
    projected_production_t DECIMAL(14,2),
    energy_demand_mwh DECIMAL(14,2),
    source_id INT,
    data_acesso DATE,
    periodo_referencia VARCHAR(20),
    valor_observado_estimado ENUM('Real','Projetado') DEFAULT 'Projetado',
    status_validacao VARCHAR(50),
    responsavel_validacao VARCHAR(100),
    FOREIGN KEY (mineral_id) REFERENCES tb_minerais(mineral_id),
    FOREIGN KEY (project_id) REFERENCES tb_projetos(project_id),
    FOREIGN KEY (source_id) REFERENCES tb_fontes(source_id)
);
