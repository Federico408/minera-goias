(function (raiz) {
  'use strict';

  var MWH_POR_TWH = 1e6;

  function anosDoHorizonte(parametros) {
    var anos = [], a;
    for (a = parametros.horizonte.inicio; a <= parametros.horizonte.fim; a++) anos.push(a);
    return anos;
  }

  function cenarioPorId(parametros, scenario) {
    for (var i = 0; i < parametros.cenarios.length; i++) {
      if (parametros.cenarios[i].scenario === scenario) return parametros.cenarios[i];
    }
    throw new Error('Cenário desconhecido nos parâmetros: ' + scenario);
  }

  // IE(t) = IE_base x (1 - g)^(t - ano_base)
  function intensidade(intensidadeBase, ganho, ano, anoBase) {
    return intensidadeBase * Math.pow(1 - ganho, ano - anoBase);
  }

  function validar(parametros) {
    if (!parametros || typeof parametros !== 'object') throw new Error('Parâmetros ausentes.');
    ['versao', 'ano_base', 'horizonte', 'cenarios', 'operacoes', 'fontes'].forEach(function (campo) {
      if (!(campo in parametros)) throw new Error('Parâmetros sem o campo obrigatório: ' + campo);
    });
    if (!parametros.operacoes.length) throw new Error('Parâmetros sem nenhuma operação.');
    parametros.operacoes.forEach(function (op) {
      if (!(op.production_t >= 0)) throw new Error('Produção inválida em ' + op.operation_id);
      if (!(op.energy_intensity_mwh_t >= 0)) throw new Error('Intensidade inválida em ' + op.operation_id);
    });
    return parametros;
  }

  function simular(parametros, opcoes) {
    validar(parametros);
    opcoes = opcoes || {};
    var cenario = cenarioPorId(parametros, opcoes.scenario || 'referencia');
    var ganho = typeof opcoes.ganhoEficiencia === 'number'
      ? opcoes.ganhoEficiencia
      : cenario.ganho_eficiencia_anual_padrao;
    if (!(ganho >= 0 && ganho < 1)) throw new Error('Ganho de eficiência fora da faixa 0–1: ' + ganho);

    var anoBase = parametros.ano_base;
    var anos = anosDoHorizonte(parametros);
    var detalhe = [];

    parametros.operacoes.forEach(function (op) {
      anos.forEach(function (ano) {
        var producao = op.production_t * cenario.fator_producao;
        var ie = intensidade(op.energy_intensity_mwh_t, ganho, ano, anoBase);
        detalhe.push({
          operation_id: op.operation_id,
          mineral_id: op.mineral_id,
          mineral_name: op.mineral_name,
          company_name: op.company_name,
          ano: ano,
          producao_t: producao,
          intensidade_mwh_t: ie,
          energia_mwh: producao * ie
        });
      });
    });

    return {
      scenario: cenario.scenario,
      rotulo: cenario.rotulo,
      cor: cenario.cor,
      fatorProducao: cenario.fator_producao,
      ganhoEficiencia: ganho,
      anoBase: anoBase,
      anos: anos,
      detalhe: detalhe,
      serie: agregarPorAno(detalhe, anos),
      versaoParametros: parametros.versao
    };
  }

  function agregarPorAno(detalhe, anos) {
    var mapa = {};
    anos.forEach(function (ano) { mapa[ano] = { ano: ano, producao_t: 0, energia_mwh: 0 }; });
    detalhe.forEach(function (linha) {
      mapa[linha.ano].producao_t += linha.producao_t;
      mapa[linha.ano].energia_mwh += linha.energia_mwh;
    });
    return anos.map(function (ano) {
      var r = mapa[ano];
      r.energia_twh = r.energia_mwh / MWH_POR_TWH;
      r.intensidade_media_mwh_t = r.producao_t ? r.energia_mwh / r.producao_t : 0;
      return r;
    });
  }

  function energiaPorMineral(resultado, ano) {
    var mapa = {}, ordem = [];
    resultado.detalhe.forEach(function (linha) {
      if (linha.ano !== ano) return;
      if (!mapa[linha.mineral_id]) {
        mapa[linha.mineral_id] = {
          mineral_id: linha.mineral_id,
          mineral_name: linha.mineral_name,
          producao_t: 0,
          energia_mwh: 0,
          operacoes: []
        };
        ordem.push(linha.mineral_id);
      }
      var m = mapa[linha.mineral_id];
      m.producao_t += linha.producao_t;
      m.energia_mwh += linha.energia_mwh;
      m.operacoes.push(linha.operation_id);
    });
    return ordem.map(function (id) {
      var m = mapa[id];
      m.energia_twh = m.energia_mwh / MWH_POR_TWH;
      return m;
    }).sort(function (a, b) { return b.energia_mwh - a.energia_mwh; });
  }

  function resumo(resultado) {
    var primeiro = resultado.serie[0];
    var ultimo = resultado.serie[resultado.serie.length - 1];
    var acumulado = resultado.serie.reduce(function (s, r) { return s + r.energia_mwh; }, 0);
    return {
      energiaInicialTwh: primeiro.energia_twh,
      energiaFinalTwh: ultimo.energia_twh,
      energiaAcumuladaTwh: acumulado / MWH_POR_TWH,
      producaoFinalMt: ultimo.producao_t / 1e6,
      intensidadeFinalMwhT: ultimo.intensidade_media_mwh_t,
      variacaoPercentual: primeiro.energia_mwh
        ? (ultimo.energia_mwh - primeiro.energia_mwh) / primeiro.energia_mwh * 100
        : 0
    };
  }

  // As três curvas são calculadas sob a mesma hipótese de eficiência, para que a
  // comparação isole o efeito do cenário de produção.
  function simularCenarios(parametros, ganhoEficiencia) {
    return parametros.cenarios.map(function (c) {
      return simular(parametros, { scenario: c.scenario, ganhoEficiencia: ganhoEficiencia });
    });
  }

  var api = {
    MWH_POR_TWH: MWH_POR_TWH,
    validar: validar,
    intensidade: intensidade,
    simular: simular,
    simularCenarios: simularCenarios,
    energiaPorMineral: energiaPorMineral,
    resumo: resumo,
    anosDoHorizonte: anosDoHorizonte,
    cenarioPorId: cenarioPorId
  };

  if (typeof module === 'object' && module.exports) module.exports = api;
  if (raiz) raiz.SimuladorEngine = api;
})(typeof window !== 'undefined' ? window : null);
