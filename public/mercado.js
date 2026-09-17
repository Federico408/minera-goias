/* Market tab: public-source reading of the critical-minerals market around Goiás.
   Everything rendered here comes from public/data/mercado/mercado_v1.json — press,
   published company results and sector studies — never from the consolidated base. */
(()=>{'use strict';
const el=id=>document.getElementById(id),escape=esc;
const SOURCE='/data/mercado/mercado_v1.json';
const VIZ={a:'#0f6fb0',b:'#0d9488',c:'#c2681b',d:'#8250c4'};
let loaded=false;

// Every prose field in the file carries both languages; plain strings pass through.
const L=v=>v&&typeof v==='object'&&!Array.isArray(v)?(v[I18N.lang]??v.pt):v;

function metrics(rows){
 return rows.map(r=>`<div class="metric tone-${escape(r.tom)}"><span>${escape(L(r.rotulo))}</span>`
  +`<strong>${escape(L(r.valor))}</strong><small>${escape(L(r.detalhe))}</small></div>`).join('')}

function operationsTable(rows){
 return `<table><thead><tr><th>${escape(t('mk.thMineral'))}</th><th>${escape(t('mk.thLocal'))}</th>`
  +`<th>${escape(t('mk.thSituacao'))}</th></tr></thead><tbody>`
  +rows.map(r=>`<tr><td><b>${escape(L(r.mineral))}</b><div class="mk-note">${escape(L(r.nota))}</div></td>`
   +`<td>${escape(L(r.local))}</td><td><span class="pill">${escape(L(r.situacao))}</span></td></tr>`).join('')
  +'</tbody></table>'}

function dealBars(rows){
 const max=Math.max(...rows.map(r=>r.valor_usd_milhoes),1);
 return rows.map(r=>`<div class="bar-row"><span class="bar-label" title="${escape(L(r.ativo))}">${escape(L(r.ativo))}</span>`
  +`<div class="bar-track"><div class="bar-fill" style="width:${r.valor_usd_milhoes/max*100}%;background:${VIZ.a}"></div></div>`
  +`<span class="bar-value">${escape(L(r.rotulo))}</span></div>`
  +`<p class="mk-note">${escape(r.comprador)} · ${escape(I18N.num(r.ano,{useGrouping:false}))}</p>`).join('')}

function priceBlock(block){
 const max=Math.max(...block.pontos.map(p=>p.valor),1);
 return `<h3 class="mk-sub">${escape(L(block.rotulo))}</h3>`
  +block.pontos.map(p=>`<div class="bar-row"><span class="bar-label">${escape(L(p.quando))}</span>`
   +`<div class="bar-track"><div class="bar-fill" style="width:${p.valor/max*100}%;background:${VIZ.c}"></div></div>`
   +`<span class="bar-value">${escape(L(p.rotulo))}</span></div>`).join('')
  +`<p class="mk-note">${escape(L(block.nota))}</p>`}

function referenceTable(rows){
 return `<table><thead><tr><th>${escape(t('mk.thEmpresa'))}</th><th>${escape(t('mk.thMineral'))}</th>`
  +`<th>${escape(t('mk.thReceita'))}</th><th>${escape(t('mk.thResultado'))}</th></tr></thead><tbody>`
  +rows.map(r=>`<tr><td><b>${escape(r.empresa)}</b><div class="mk-note">${escape(L(r.onde))} · ${escape(L(r.praca))}</div>`
   +`<div class="mk-note">${escape(L(r.nota))}</div></td><td>${escape(L(r.mineral))}</td>`
   +`<td>${escape(L(r.receita))}</td><td>${escape(L(r.resultado))}</td></tr>`).join('')+'</tbody></table>'}

function ruleList(rows){
 return '<ul class="mk-list">'+rows.map(r=>`<li><b class="mk-code">${escape(r.sigla)}</b>`
  +`<b>${escape(L(r.nome))}</b><span class="muted">${escape(L(r.descricao))}</span></li>`).join('')+'</ul>'}

function newsList(rows){
 return '<ul class="rd-news">'+rows.map(r=>{
   const quando=String(r.data||'');
   return `<li><a href="${escape(r.link)}" target="_blank" rel="noopener noreferrer">${escape(L(r.titulo))}</a>`
    +`<span class="muted">${escape(r.fonte)}${quando?' · '+escape(quando):''}</span>`
    +`<span class="mk-note">${escape(L(r.resumo))}</span></li>`}).join('')+'</ul>'}

function plainList(rows){
 return '<ul class="mk-bullets">'+rows.map(r=>`<li>${escape(L(r))}</li>`).join('')+'</ul>'}

function sourceList(rows){
 return rows.map(r=>`<a href="${escape(r.link)}" target="_blank" rel="noopener noreferrer">${escape(r.nome)}</a>`).join(' · ')}

async function load(){
 el('mercado-error').textContent='';
 try{
  const r=await fetch(SOURCE,{cache:'no-store'});
  if(!r.ok)throw Error(t('mk.fail'));
  const d=await r.json();
  el('mk-metrics').innerHTML=metrics(d.indicadores);
  el('mk-nota').textContent=L(d.nota);
  el('mk-operacoes').innerHTML=operationsTable(d.operacoes);
  el('mk-transacoes').innerHTML=dealBars(d.transacoes);
  el('mk-preco').innerHTML=priceBlock(d.preco_referencia);
  el('mk-referencias').innerHTML=referenceTable(d.referencias);
  el('mk-regulacao').innerHTML=ruleList(d.regulacao);
  el('mk-noticias').innerHTML=newsList(d.noticias);
  el('mk-oportunidades').innerHTML=plainList(d.oportunidades);
  el('mk-riscos').innerHTML=plainList(d.riscos);
  el('mk-fontes').innerHTML=escape(t('mk.sourcePrefix'))+' '+sourceList(d.fontes);
  el('mk-updated').textContent=t('mk.updated',{data:d.atualizado_em,autoria:L(d.autoria)});
  el('mercado-content').hidden=false;
 }catch(e){el('mercado-error').textContent=e.message}
 finally{el('mercado-loading').hidden=true}}

window.showMercado=()=>{if(loaded)return;loaded=true;load()};
})();
