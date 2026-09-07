USE db_minera_goias;

INSERT INTO tb_fontes (nome_fonte, source_url, tipo_fonte, descricao) VALUES
('ANM', 'https://www.gov.br/anm', 'Oficial', 'Agência Nacional de Mineração'),
('EPE', 'https://www.epe.gov.br', 'Oficial', 'Empresa de Pesquisa Energética'),
('Relatorio Empresa Ficticio', 'https://exemplo.com', 'Companhia', 'Dado mock para teste');

INSERT INTO tb_municipios (nome_municipio, latitude, longitude) VALUES
('Catalão', -18.1661, -47.9456),
('Ouvidor', -18.2989, -47.8564),
('Niquelândia', -14.4733, -48.4633);

INSERT INTO tb_minerais (mineral_name, sinonimos, observacao) VALUES
('Nióbio', 'Niobium, Columbita', 'Estratégico para ligas metálicas'),
('Níquel', 'Nickel', 'Estratégico para baterias e aço inox');

INSERT INTO tb_empresas (nome_empresa) VALUES
('Empresa Mock A'),
('Empresa Mock B');

INSERT INTO tb_projetos (company_id, mineral_id, municipality_id, nome_projeto, source_id, data_acesso, periodo_referencia, valor_observado_estimado, status_validacao, responsavel_validacao) VALUES
(1, 1, 1, 'Projeto Niobio Catalao', 3, CURDATE(), '2026-Q3', 'Real', 'Pendente', 'Kayo'),
(2, 2, 3, 'Projeto Niquel Niquelandia', 3, CURDATE(), '2026-Q3', 'Real', 'Pendente', 'Kayo');

INSERT INTO tb_intensidade_energetica (mineral_id, intensidade_mwh_t, production_basis, source_id, data_acesso, periodo_referencia, valor_observado_estimado, status_validacao, responsavel_validacao) VALUES
(1, 2.5, 'ROM', 2, CURDATE(), '2026-Q3', 'Real', 'Pendente', 'Kayo'),
(2, 4.1, 'Beneficiado', 2, CURDATE(), '2026-Q3', 'Real', 'Pendente', 'Kayo');

INSERT INTO tb_projecoes (mineral_id, project_id, year, scenario, projected_production_t, energy_demand_mwh, source_id, data_acesso, periodo_referencia, valor_observado_estimado, status_validacao, responsavel_validacao)
WITH RECURSIVE anos AS (
    SELECT 2027 AS year
    UNION ALL
    SELECT year + 1 FROM anos WHERE year < 2040
)
SELECT p.mineral_id, p.project_id, a.year, s.scenario,
       ROUND(100000 * (1 + (a.year - 2027) * 0.05) *
             CASE s.scenario WHEN 'conservador' THEN 0.8 WHEN 'referencia' THEN 1.0 ELSE 1.3 END, 2),
       ROUND(50000 * (1 + (a.year - 2027) * 0.05) *
             CASE s.scenario WHEN 'conservador' THEN 0.8 WHEN 'referencia' THEN 1.0 ELSE 1.3 END, 2),
       1, CURDATE(), '2026-Q3', 'Projetado', 'Pendente', 'Kayo'
FROM anos a
CROSS JOIN tb_projetos p
CROSS JOIN (SELECT 'conservador' AS scenario UNION SELECT 'referencia' UNION SELECT 'expansao') s;