-- Dados fictícios para desenvolvimento local. NÃO aplicar em produção.
-- Para carregar as fontes reais da ANM use load_anm.py; ver README_backend.md.
-- Este arquivo acompanha o schema atual: empresa chaveada por nome normalizado,
-- documento opcional, e polígonos em tabela própria.

USE db_minera_goias;

INSERT INTO tb_fontes (source_id, titulo, instituicao, url_arquivo, cobertura, notas_metodologicas) VALUES
('DEMO_ANM', 'Cadastro mineiro (amostra fictícia)', 'ANM', 'exemplo/demo.csv', 'Goiás', 'Dados inventados para teste local.'),
('DEMO_EPE', 'Balanço energético (amostra fictícia)', 'EPE', 'exemplo/demo-energia.csv', 'Brasil', 'Dados inventados para teste local.');

INSERT INTO tb_municipios (codigo_ibge, nome_municipio) VALUES
('5205109', 'Catalão'),
('5215702', 'Ouvidor'),
('5214606', 'Niquelândia');

INSERT INTO tb_minerais (id_substancia_anm, mineral_name, sinonimos, observacao) VALUES
(101300, 'NIÓBIO', 'Columbita', 'Identificadores seguem o dicionário da ANM.'),
(102300, 'NÍQUEL', 'Nickel', 'Identificadores seguem o dicionário da ANM.');

INSERT INTO tb_empresas (nome_empresa, nome_empresa_normalizado, documento_cnpj_cpf, tipo_pessoa) VALUES
('Mineradora Exemplo A LTDA', 'MINERADORA EXEMPLO A LTDA', NULL, 'Jurídica'),
('Mineradora Exemplo B S.A.', 'MINERADORA EXEMPLO B S.A.', NULL, 'Jurídica');

-- A fonte cadastral não traz documento; o vínculo é por chave interna da empresa.
INSERT INTO tb_projetos (processo_anm, empresa_id, titular_nome, ultimo_evento, uf, poligonos,
                         substancia_anm, mineral_id, fase, uso, area_ha, categoria, source_id,
                         data_acesso, valor_observado_estimado, status_validacao)
SELECT '860001/2020', e.empresa_id, e.nome_empresa, 'DEMO / evento fictício', 'GO', 1,
       'NIÓBIO', m.mineral_id, 'CONCESSÃO DE LAVRA', 'Demais substâncias', 1200.00, 'demo',
       'DEMO_ANM', '2026-09-13', 'Real', 'nao_validado'
FROM tb_empresas e JOIN tb_minerais m ON m.id_substancia_anm = 101300
WHERE e.nome_empresa_normalizado = 'MINERADORA EXEMPLO A LTDA';

INSERT INTO tb_projetos (processo_anm, empresa_id, titular_nome, ultimo_evento, uf, poligonos,
                         substancia_anm, mineral_id, fase, uso, area_ha, categoria, source_id,
                         data_acesso, valor_observado_estimado, status_validacao)
SELECT '860002/2021', e.empresa_id, e.nome_empresa, 'DEMO / evento fictício', 'GO', 2,
       'NÍQUEL', m.mineral_id, 'REQUERIMENTO DE LAVRA', 'Demais substâncias', NULL, 'demo',
       'DEMO_ANM', '2026-09-13', 'Real', 'nao_validado'
FROM tb_empresas e JOIN tb_minerais m ON m.id_substancia_anm = 102300
WHERE e.nome_empresa_normalizado = 'MINERADORA EXEMPLO B S.A.';

-- Área fica por polígono quando o processo tem mais de um: eles podem se sobrepor.
INSERT INTO tb_projeto_poligono (processo_anm, id_poligono_origem, area_ha) VALUES
('860001/2020', '{DEMO-0001}', 1200.00),
('860002/2021', '{DEMO-0002}', 400.00),
('860002/2021', '{DEMO-0003}', 350.00);

INSERT INTO tb_projeto_municipio (processo_anm, codigo_ibge) VALUES
('860001/2020', '5205109'),
('860002/2021', '5214606');

INSERT INTO tb_intensidade_energetica (mineral_id, intensidade_mwh_t, production_basis, source_id,
                                       data_acesso, valor_observado_estimado, status_validacao)
SELECT mineral_id, 0.4500, 'Beneficiado', 'DEMO_EPE', '2026-09-13', 'Projetado', 'nao_validado'
FROM tb_minerais WHERE id_substancia_anm = 101300;

INSERT INTO tb_projecoes (mineral_id, processo_anm, year, scenario, projected_production,
                          unidade_producao, energy_demand_mwh, source_id, data_acesso,
                          valor_observado_estimado, status_validacao)
SELECT m.mineral_id, '860001/2020', y.year, 'referencia', 1000.00, 't', 450.00,
       'DEMO_EPE', '2026-09-13', 'Projetado', 'nao_validado'
FROM tb_minerais m
JOIN (SELECT 2027 AS year UNION SELECT 2028 UNION SELECT 2029) y
WHERE m.id_substancia_anm = 101300;
