// Testes do motor de cálculo do simulador (public/simulador-engine.js).
// Execução: node tests/simulador.test.js

function executarTestes(engine, parametros) {
  var falhas = [], total = 0;

  function ok(nome, condicao, detalhe) {
    total++;
    if (!condicao) falhas.push(nome + (detalhe ? ' — ' + detalhe : ''));
  }
  function perto(nome, obtido, esperado, tolerancia) {
    total++;
    var t = tolerancia === undefined ? 1e-9 : tolerancia;
    if (!(Math.abs(obtido - esperado) <= t)) {
      falhas.push(nome + ' — esperado ' + esperado + ', obtido ' + obtido);
    }
  }
  function lanca(nome, fn) {
    total++;
    try { fn(); falhas.push(nome + ' — deveria ter lançado erro'); } catch (e) { /* esperado */ }
  }

  perto('intensidade sem ganho fica constante', engine.intensidade(10, 0, 2040, 2025), 10);
  perto('intensidade cai 1% em um ano', engine.intensidade(10, 0.01, 2026, 2025), 9.9);
  perto('intensidade compõe ao longo dos anos',
    engine.intensidade(45.4, 0.009, 2030, 2025), 45.4 * Math.pow(0.991, 5));

  var base = engine.simular(parametros, { scenario: 'referencia', ganhoEficiencia: 0 });
  ok('horizonte cobre 2027 a 2040', base.anos.length === 14 && base.anos[0] === 2027 && base.anos[13] === 2040);
  perto('produção do baseline é 3,0 Mt', base.serie[0].producao_t, 3000000, 1e-6);
  perto('energia do baseline é 4,4904 TWh', base.serie[0].energia_twh, 4.4904, 1e-9);
  perto('sem ganho de eficiência a série é plana',
    base.serie[13].energia_twh, base.serie[0].energia_twh, 1e-12);

  var conservador = engine.simular(parametros, { scenario: 'conservador', ganhoEficiencia: 0 });
  var expansao = engine.simular(parametros, { scenario: 'expansao', ganhoEficiencia: 0 });
  perto('fator conservador reduz a produção em 10%', conservador.serie[0].energia_twh, 4.4904 * 0.9, 1e-9);
  perto('fator expansão aumenta a produção em 15%', expansao.serie[0].energia_twh, 4.4904 * 1.15, 1e-9);
  ok('conservador fica abaixo de expansão', conservador.serie[0].energia_twh < expansao.serie[0].energia_twh);

  var comGanho = engine.simular(parametros, { scenario: 'referencia', ganhoEficiencia: 0.009 });
  perto('eficiência aplica-se desde o ano base', comGanho.serie[0].energia_twh,
    4.4904 * Math.pow(0.991, 2), 1e-9);
  perto('eficiência acumula até 2040', comGanho.serie[13].energia_twh,
    4.4904 * Math.pow(0.991, 15), 1e-9);
  ok('eficiência reduz a energia ao longo do tempo',
    comGanho.serie[13].energia_twh < comGanho.serie[0].energia_twh);
  ok('eficiência não altera a produção física',
    Math.abs(comGanho.serie[13].producao_t - base.serie[13].producao_t) < 1e-6);

  var padrao = engine.simular(parametros, { scenario: 'referencia' });
  perto('sem ganho informado usa o padrão do cenário', padrao.ganhoEficiencia, 0.009);

  var minerais = engine.energiaPorMineral(base, 2027);
  ok('agrupa as sete operações em seis minerais', minerais.length === 6, 'obtido ' + minerais.length);
  ok('ordena do maior para o menor', minerais[0].mineral_id === 'MIN_005');
  perto('níquel soma as duas operações',
    minerais.filter(function (m) { return m.mineral_id === 'MIN_001'; })[0].energia_twh, 1.6854, 1e-9);
  perto('soma dos minerais reproduz o total do ano',
    minerais.reduce(function (s, m) { return s + m.energia_mwh; }, 0), base.serie[0].energia_mwh, 1e-6);

  var r = engine.resumo(comGanho);
  perto('resumo usa o último ano do horizonte', r.energiaFinalTwh, comGanho.serie[13].energia_twh, 1e-12);
  perto('energia acumulada soma os catorze anos', r.energiaAcumuladaTwh,
    comGanho.serie.reduce(function (s, x) { return s + x.energia_twh; }, 0), 1e-9);
  ok('variação percentual é negativa quando há eficiência', r.variacaoPercentual < 0);

  var todos = engine.simularCenarios(parametros, 0.005);
  ok('simularCenarios devolve os três cenários', todos.length === 3);
  ok('os três usam a mesma hipótese de eficiência',
    todos.every(function (x) { return x.ganhoEficiencia === 0.005; }));

  perto('conferência do baseline confere com os parâmetros',
    parametros.conferencia_baseline.energia_calculada_twh, 4.4904, 1e-9);

  lanca('cenário inexistente é rejeitado', function () {
    engine.simular(parametros, { scenario: 'otimista' });
  });
  lanca('ganho fora da faixa é rejeitado', function () {
    engine.simular(parametros, { scenario: 'referencia', ganhoEficiencia: 1.5 });
  });
  lanca('parâmetros sem operações são rejeitados', function () {
    engine.validar({ versao: '0', ano_base: 2025, horizonte: {}, cenarios: [], operacoes: [], fontes: [] });
  });

  return { total: total, falhas: falhas };
}

if (typeof module === 'object' && module.exports) {
  module.exports = executarTestes;
  if (require.main === module) {
    var fs = require('fs'), path = require('path');
    var engine = require(path.join(__dirname, '..', 'public', 'simulador-engine.js'));
    var parametros = JSON.parse(fs.readFileSync(
      path.join(__dirname, '..', 'public', 'data', 'simulador', 'parametros_v0.json'), 'utf8'));
    var r = executarTestes(engine, parametros);
    r.falhas.forEach(function (f) { console.error('FALHOU: ' + f); });
    console.log((r.total - r.falhas.length) + '/' + r.total + ' verificações passaram.');
    process.exit(r.falhas.length ? 1 : 0);
  }
}
