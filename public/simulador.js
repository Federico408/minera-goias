(function () {
  'use strict';

  var CAMINHO_PARAMETROS = '/data/simulador/parametros_v0.json';
  var $ = function (id) { return document.getElementById(id); };
  var estado = { parametros: null, scenario: 'referencia', ganho: 0 };

  var num = function (v, casas) {
    return v.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas });
  };
  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  var data = function (iso) {
    var p = String(iso).split('-');
    return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : iso;
  };

  function escalaBonita(valor) {
    if (!(valor > 0)) return 1;
    var potencia = Math.pow(10, Math.floor(Math.log10(valor))), n = valor / potencia;
    return (n <= 1 ? 1 : n <= 1.5 ? 1.5 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 3 ? 3 : n <= 4 ? 4 : n <= 5 ? 5 : n <= 7.5 ? 7.5 : 10) * potencia;
  }
  var topoEscala = function (v) { return escalaBonita(v / 4) * 4; };

  function graficoAnos(resultados, selecionado) {
    var L = 60, R = 18, T = 18, B = 40, W = 900, H = 340;
    var anos = resultados[0].anos;
    var maximo = 0;
    resultados.forEach(function (r) {
      r.serie.forEach(function (p) { if (p.energia_twh > maximo) maximo = p.energia_twh; });
    });
    var topo = topoEscala(maximo) || 1;
    var x = function (i) { return L + (W - L - R) * (anos.length === 1 ? 0 : i / (anos.length - 1)); };
    var y = function (v) { return T + (H - T - B) * (1 - v / topo); };

    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Demanda de energia por ano em cada cenário">';
    for (var i = 0; i <= 4; i++) {
      var valor = topo * i / 4, yy = y(valor);
      svg += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + yy + '" y2="' + yy + '" stroke="#e8e2d6"/>';
      svg += '<text x="' + (L - 10) + '" y="' + (yy + 4) + '" text-anchor="end" font-size="11" fill="#6b7780">' + esc(num(valor, 1)) + '</text>';
    }
    svg += '<text x="' + L + '" y="' + (H - 8) + '" font-size="10" fill="#6b7780">TWh por ano</text>';
    anos.forEach(function (ano, i) {
      svg += '<text x="' + x(i) + '" y="' + (H - B + 20) + '" text-anchor="middle" font-size="10" fill="#6b7780">' + ano + '</text>';
    });

    resultados.forEach(function (r) {
      var atual = r.scenario === selecionado;
      var pontos = r.serie.map(function (p, i) { return x(i) + ',' + y(p.energia_twh); }).join(' ');
      svg += '<polyline points="' + pontos + '" fill="none" stroke="' + r.cor + '"'
        + ' stroke-width="' + (atual ? 3 : 1.6) + '" stroke-opacity="' + (atual ? 1 : 0.42) + '"'
        + ' stroke-linejoin="round" stroke-linecap="round"/>';
      if (atual) {
        r.serie.forEach(function (p, i) {
          svg += '<circle cx="' + x(i) + '" cy="' + y(p.energia_twh) + '" r="3.5" fill="' + r.cor + '">'
            + '<title>' + esc(r.rotulo + ' · ' + p.ano + ': ' + num(p.energia_twh, 3) + ' TWh') + '</title></circle>';
        });
        var ultimo = r.serie[r.serie.length - 1];
        svg += '<text x="' + (x(anos.length - 1) - 4) + '" y="' + (y(ultimo.energia_twh) - 12) + '"'
          + ' text-anchor="end" font-size="12" font-weight="700" fill="' + r.cor + '">'
          + esc(num(ultimo.energia_twh, 2)) + ' TWh</text>';
      }
    });
    return svg + '</svg>';
  }

  function graficoMinerais(minerais, cor) {
    if (!minerais.length) return '<p class="ajuda">Sem dados para o ano selecionado.</p>';
    var linha = 40, L = 168, R = 92, W = 900, H = minerais.length * linha + 16;
    var topo = topoEscala(minerais[0].energia_twh) || 1;
    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Demanda de energia por mineral">';
    minerais.forEach(function (m, i) {
      var yy = i * linha + 8, largura = (W - L - R) * (m.energia_twh / topo);
      svg += '<text x="' + (L - 12) + '" y="' + (yy + 19) + '" text-anchor="end" font-size="12" fill="#26313A">' + esc(m.mineral_name) + '</text>';
      svg += '<rect x="' + L + '" y="' + yy + '" width="' + (W - L - R) + '" height="22" fill="#f2efe7"/>';
      svg += '<rect x="' + L + '" y="' + yy + '" width="' + Math.max(largura, 1) + '" height="22" fill="' + cor + '">'
        + '<title>' + esc(m.mineral_name + ': ' + num(m.energia_twh, 3) + ' TWh') + '</title></rect>';
      svg += '<text x="' + (W - R + 10) + '" y="' + (yy + 16) + '" font-size="12" font-weight="700" fill="#26313A">' + esc(num(m.energia_twh, 3)) + '</text>';
      svg += '<text x="' + (W - R + 10) + '" y="' + (yy + 29) + '" font-size="9" fill="#6b7780">TWh</text>';
    });
    return svg + '</svg>';
  }

  function tabelaAnos(resultados) {
    var cab = '<tr><th>Ano</th>' + resultados.map(function (r) {
      return '<th>' + esc(r.rotulo) + ' · TWh</th>';
    }).join('') + '</tr>';
    var corpo = resultados[0].anos.map(function (ano, i) {
      return '<tr><td>' + ano + '</td>' + resultados.map(function (r) {
        return '<td class="num">' + esc(num(r.serie[i].energia_twh, 3)) + '</td>';
      }).join('') + '</tr>';
    }).join('');
    return '<table><thead>' + cab + '</thead><tbody>' + corpo + '</tbody></table>';
  }

  function tabelaMinerais(minerais) {
    var linhas = minerais.map(function (m) {
      return '<tr><td>' + esc(m.mineral_name) + '</td>'
        + '<td class="num">' + esc(num(m.producao_t / 1e6, 3)) + '</td>'
        + '<td class="num">' + esc(num(m.energia_twh, 3)) + '</td>'
        + '<td class="num">' + m.operacoes.length + '</td></tr>';
    }).join('');
    return '<table><thead><tr><th>Mineral</th><th>Produção · Mt</th><th>Energia · TWh</th><th>Operações</th></tr></thead>'
      + '<tbody>' + linhas + '</tbody></table>';
  }

  function selo(natureza) {
    return '<span class="selo ' + (natureza === 'observado' ? 'observado' : 'ilustrativo') + '">'
      + esc(natureza) + '</span>';
  }

  function indiceFontes() {
    var mapa = {};
    estado.parametros.fontes.forEach(function (f) { mapa[f.source_id] = f; });
    return mapa;
  }

  function linhaParametro(nome, valor, fonte, natureza) {
    return '<tr><td>' + esc(nome) + '</td><td class="num">' + esc(valor) + '</td>'
      + '<td>' + esc(fonte.source_name) + '</td><td>' + esc(data(fonte.data_acesso)) + '</td>'
      + '<td>' + selo(natureza) + '</td></tr>';
  }

  function blocoParametros() {
    var p = estado.parametros, fontes = indiceFontes();
    var cen = window.SimuladorEngine.cenarioPorId(p, estado.scenario);
    var padrao = estado.ganho === cen.ganho_eficiencia_anual_padrao;
    var linhas = [
      linhaParametro('Fator de produção do cenário', num(cen.fator_producao, 2) + '×',
        fontes[cen.fator_producao_source_id], 'ilustrativo'),
      linhaParametro('Ganho de eficiência em uso (g)', num(estado.ganho * 100, 1) + '% ao ano',
        fontes[cen.ganho_eficiencia_source_id],
        padrao ? 'ilustrativo' : 'definido pelo usuário nesta simulação'),
      linhaParametro('Ganho padrão deste cenário', num(cen.ganho_eficiencia_anual_padrao * 100, 1) + '% ao ano',
        fontes[cen.ganho_eficiencia_source_id], 'ilustrativo')
    ].join('');
    return '<table><thead><tr><th>Parâmetro</th><th>Valor</th><th>Fonte</th>'
      + '<th>Data de acesso</th><th>Natureza</th></tr></thead><tbody>' + linhas + '</tbody></table>';
  }

  function blocoOperacoes() {
    var fontes = indiceFontes();
    var linhas = estado.parametros.operacoes.map(function (op) {
      var f = fontes[op.source_id];
      return '<tr><td>' + esc(op.company_name) + '</td><td>' + esc(op.mineral_name) + '</td>'
        + '<td>' + esc(op.municipality_name) + '</td>'
        + '<td class="num">' + esc(num(op.production_mt_publicado, 3)) + '</td>'
        + '<td class="num">' + esc(num(op.energy_intensity_mwh_t, 2)) + '</td>'
        + '<td class="num">' + esc(num(op.energy_twh_publicado, 2)) + '</td>'
        + '<td>' + esc(data(f.data_acesso)) + '</td>'
        + '<td>' + selo(op.valor_observado_estimado) + '</td></tr>';
    }).join('');
    return '<table><thead><tr><th>Empresa</th><th>Mineral</th><th>Município</th>'
      + '<th>Produção · Mt</th><th>IE · MWh/t</th><th>Energia · TWh</th>'
      + '<th>Data de acesso</th><th>Natureza</th></tr></thead><tbody>' + linhas + '</tbody></table>';
  }

  function blocoCatalogo() {
    return estado.parametros.fontes.map(function (f) {
      var campos = [
        ['Identificador', f.source_id],
        ['Origem', f.source_url || 'sem URL pública'],
        ['Período de referência', f.periodo_referencia],
        ['Tipo de fonte', f.tipo_fonte],
        ['Data de acesso', data(f.data_acesso)],
        ['Método de estimação', f.metodo_estimacao || 'não se aplica'],
        ['Status de validação', f.status_validacao],
        ['Responsável pela validação', f.responsavel_validacao]
      ].map(function (c) {
        return '<tr><td>' + esc(c[0]) + '</td><td>' + esc(c[1]) + '</td></tr>';
      }).join('');
      return '<h3>' + esc(f.source_name) + ' ' + selo(f.valor_observado_estimado) + '</h3>'
        + '<p>' + esc(f.notas) + '</p>'
        + '<div class="tabela-wrap"><table><tbody>' + campos + '</tbody></table></div>';
    }).join('');
  }

  function abrirModal() {
    var p = estado.parametros, cen = window.SimuladorEngine.cenarioPorId(p, estado.scenario);
    var conf = p.conferencia_baseline;
    $('modal-sub').textContent = 'Cenário ' + cen.rotulo.toLowerCase() + ' · arquivo de parâmetros v'
      + p.versao + ', de ' + data(p.data_versao) + '.';
    $('modal-corpo').innerHTML =
      '<h3>Como o resultado é calculado</h3>'
      + '<p>Energia(t) = produção(t) × intensidade(t). A intensidade evolui por '
      + 'IE(t) = IE<sub>base</sub> × (1 − g)<sup>t − ' + p.ano_base + '</sup> e a produção é o baseline '
      + 'multiplicado pelo fator do cenário. Não há modelo estatístico intermediário: os números da tela '
      + 'saem apenas dos parâmetros listados abaixo.</p>'
      + '<p>' + esc(p.ano_base_nota) + '</p>'

      + '<h3>Parâmetros do cenário selecionado</h3>'
      + '<div class="tabela-wrap">' + blocoParametros() + '</div>'

      + '<h3>Baseline por operação</h3>'
      + '<p>Sete operações transcritas da tabela do material FGV Energia-EPGE. '
      + 'A coluna de energia é o valor publicado, guardado para conferência; o simulador calcula a energia '
      + 'a partir de produção × intensidade.</p>'
      + '<div class="tabela-wrap">' + blocoOperacoes() + '</div>'

      + '<h3>Conferência do baseline</h3>'
      + '<p>Produção × intensidade soma <b>' + esc(num(conf.energia_calculada_twh, 4)) + ' TWh</b>, '
      + 'contra <b>' + esc(num(conf.energia_publicada_twh, 2)) + ' TWh</b> publicados — diferença de '
      + esc(num(conf.divergencia_percentual, 2)) + '%. ' + esc(conf.nota) + '</p>'

      + '<h3>Catálogo de fontes</h3>'
      + blocoCatalogo();
    $('modal').hidden = false;
    $('modal-fechar').focus();
  }

  function fecharModal() { $('modal').hidden = true; }

  function kpis(resumo, cenario) {
    var itens = [
      ['Energia em 2040', num(resumo.energiaFinalTwh, 2) + ' TWh',
        (resumo.variacaoPercentual >= 0 ? '+' : '−') + num(Math.abs(resumo.variacaoPercentual), 1) + '% em relação a 2027', true],
      ['Energia acumulada', num(resumo.energiaAcumuladaTwh, 1) + ' TWh', '2027 a 2040', false],
      ['Produção anual', num(resumo.producaoFinalMt, 2) + ' Mt', 'fator do cenário: ' + num(cenario.fatorProducao, 2), false],
      ['Intensidade média', num(resumo.intensidadeFinalMwhT, 2) + ' MWh/t', 'em 2040', false]
    ];
    return itens.map(function (it) {
      return '<div class="kpi' + (it[3] ? ' destaque' : '') + '"><span>' + esc(it[0]) + '</span>'
        + '<strong>' + esc(it[1]) + '</strong><small>' + esc(it[2]) + '</small></div>';
    }).join('');
  }

  function botoesCenario() {
    $('cenarios').innerHTML = estado.parametros.cenarios.map(function (c) {
      return '<button type="button" role="radio" data-cenario="' + esc(c.scenario) + '"'
        + ' aria-checked="' + (c.scenario === estado.scenario) + '">'
        + '<span class="ponto"></span>' + esc(c.rotulo) + '</button>';
    }).join('');
    Array.prototype.forEach.call($('cenarios').querySelectorAll('button'), function (b) {
      b.onclick = function () { estado.scenario = b.dataset.cenario; desenhar(); };
    });
  }

  function desenhar() {
    var engine = window.SimuladorEngine, p = estado.parametros;
    var resultados = engine.simularCenarios(p, estado.ganho);
    var atual = resultados.filter(function (r) { return r.scenario === estado.scenario; })[0];
    var anoFinal = p.horizonte.fim;
    var minerais = engine.energiaPorMineral(atual, anoFinal);
    var cenario = engine.cenarioPorId(p, estado.scenario);

    Array.prototype.forEach.call($('cenarios').querySelectorAll('button'), function (b) {
      b.setAttribute('aria-checked', String(b.dataset.cenario === estado.scenario));
    });
    $('ganho').value = (estado.ganho * 100).toFixed(1);
    $('ganho-valor').textContent = num(estado.ganho * 100, 1) + '%';
    $('ajuda-cenario').innerHTML = 'Fator de produção aplicado ao baseline: <b>' + esc(num(atual.fatorProducao, 2))
      + '</b>. Padrão de eficiência deste cenário: <b>' + esc(num(cenario.ganho_eficiencia_anual_padrao * 100, 1)) + '%</b> ao ano.';

    $('kpis').innerHTML = kpis(engine.resumo(atual), atual);
    $('grafico-anos').innerHTML = graficoAnos(resultados, estado.scenario);
    $('legenda-anos').innerHTML = resultados.map(function (r) {
      return '<span class="' + (r.scenario === estado.scenario ? 'atual' : '') + '">'
        + '<i style="background:' + r.cor + '"></i>' + esc(r.rotulo)
        + (r.scenario === estado.scenario ? ' · selecionado' : '') + '</span>';
    }).join('');
    $('tabela-anos').innerHTML = tabelaAnos(resultados);
    $('grafico-minerais').innerHTML = graficoMinerais(minerais, atual.cor);
    $('tabela-minerais').innerHTML = tabelaMinerais(minerais);
    $('ano-final-1').textContent = anoFinal;
  }

  function iniciar(parametros) {
    window.SimuladorEngine.validar(parametros);
    estado.parametros = parametros;
    estado.ganho = window.SimuladorEngine.cenarioPorId(parametros, estado.scenario).ganho_eficiencia_anual_padrao;

    $('version-tag').textContent = 'parâmetros v' + parametros.versao + ' · ' + data(parametros.data_versao);
    $('aviso-ilustrativo').innerHTML = '<b>Dado ilustrativo, aguardando o Squad 2.</b> ' + esc(parametros.aviso);
    $('linha-fonte').textContent = 'Fontes: ' + parametros.fontes.map(function (f) { return f.source_name; }).join(' · ')
      + '. Arquivo de parâmetros v' + parametros.versao + ', de ' + data(parametros.data_versao) + '.';

    botoesCenario();
    $('ganho').oninput = function () { estado.ganho = Number(this.value) / 100; desenhar(); };
    $('btn-padrao').onclick = function () {
      estado.ganho = window.SimuladorEngine.cenarioPorId(estado.parametros, estado.scenario).ganho_eficiencia_anual_padrao;
      desenhar();
    };
    $('btn-fontes').hidden = false;
    $('btn-fontes').onclick = abrirModal;
    $('modal-fechar').onclick = fecharModal;
    $('modal').onclick = function (e) { if (e.target === $('modal')) fecharModal(); };
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') fecharModal(); });

    desenhar();
    $('carregando').hidden = true;
    $('conteudo').hidden = false;
  }

  function falhar(mensagem) {
    $('carregando').hidden = true;
    $('erro').hidden = false;
    $('erro').textContent = 'Não foi possível carregar o simulador: ' + mensagem;
  }

  fetch(CAMINHO_PARAMETROS, { cache: 'no-store' })
    .then(function (r) {
      if (!r.ok) throw new Error('arquivo de parâmetros não encontrado (' + r.status + ').');
      return r.json();
    })
    .then(iniciar)
    .catch(function (e) { falhar(e.message); });
})();
