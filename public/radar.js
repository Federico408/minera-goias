/* Radar panel: register phases, availability rounds and the news collector's output.
   Every number here is a count of records in a source, never a forecast. */
(()=>{'use strict';
const el=id=>document.getElementById(id),escape=esc,n=v=>I18N.num(v);
const VIZ={confirmado:'#0f6fb0',analise:'#0d9488',abrindo:'#c2681b'};
let loaded=false;

function bars(rows,color){
 if(!rows.length)return `<div class="empty">${escape(t('ov.empty'))}</div>`;
 const max=Math.max(...rows.map(r=>r.value),1);
 return rows.map(r=>`<div class="bar-row"><span class="bar-label" title="${escape(r.label)}">${escape(r.label)}</span>`
  +`<div class="bar-track"><div class="bar-fill" style="width:${r.value/max*100}%;background:${color}"></div></div>`
  +`<span class="bar-value">${escape(n(r.value))}</span></div>`).join('')}

function phaseTable(fases){
 const rows=[...fases.confirmado.fases.map(f=>({...f,grupo:'confirmado'})),
             ...fases.analise.fases.map(f=>({...f,grupo:'analise'})),
             ...fases.abrindo.fases.map(f=>({...f,grupo:'abrindo'}))]
   .sort((a,b)=>b.processos-a.processos);
 return `<table><thead><tr><th>${escape(t('rd.thFase'))}</th><th>${escape(t('rd.thProcessos'))}</th></tr></thead><tbody>`
  +rows.map(r=>`<tr><td><span class="rd-dot" style="background:${VIZ[r.grupo]}"></span>${escape(r.fase)}</td>`
   +`<td>${escape(n(r.processos))}</td></tr>`).join('')+'</tbody></table>'}

function newsBlock(noticias){
 if(!noticias.disponivel){
  const motivo=noticias.motivo==='banco_ilegivel'?'rd.bancoIlegivel':'rd.semColetor';
  return `<div class="notice">${escape(t(motivo))}</div>`}
 const items=noticias.itens.length
  ? '<ul class="rd-news">'+noticias.itens.map(i=>{
      const quando=(i.published_at||i.first_seen||'').slice(0,10);
      return `<li><a href="${escape(i.link)}" target="_blank" rel="noopener noreferrer">${escape(i.title)}</a>`
       +`<span class="muted">${escape(i.fonte||'')}${quando?' · '+escape(quando):''}</span></li>`}).join('')+'</ul>'
  : `<div class="empty">${escape(t('ov.empty'))}</div>`;
 const atualizado=noticias.atualizado_em
  ? `<p class="small muted">${escape(t('rd.atualizado'))} ${escape(noticias.atualizado_em.slice(0,16).replace('T',' '))}</p>`:'';
 return atualizado+items}

function trendBlock(noticias){
 if(!noticias.disponivel)return '';
 // Only signals the collector was willing to call are worth a row here.
 const rows=noticias.tendencias.filter(x=>x.verdict==='pressao_de_alta'||x.verdict==='pressao_de_baixa');
 const body=rows.length
  ? `<table><thead><tr><th>${escape(t('rd.thSemana'))}</th><th>${escape(t('rd.thSubstancia'))}</th>`
    +`<th>${escape(t('rd.thMaterias'))}</th><th>${escape(t('rd.thVeredito'))}</th></tr></thead><tbody>`
    +rows.map(r=>`<tr><td>${escape(r.period)}</td><td>${escape(r.commodity)}</td><td>${escape(n(r.items))}</td>`
     +`<td>${escape(t('rd.v.'+r.verdict))}</td></tr>`).join('')+'</tbody></table>'
  : `<div class="empty">${escape(t('rd.semTendencia'))}</div>`;
 return `<h3>${escape(t('rd.tendencias'))}</h3>${body}<p class="small muted">${escape(t('rd.aviso'))}</p>`}

async function load(){
 el('radar-error').textContent='';
 try{
  const d=await api('/radar');
  el('rd-confirmado').textContent=n(d.fases.confirmado.total);
  el('rd-analise').textContent=n(d.fases.analise.total);
  el('rd-abrindo').textContent=n(d.fases.abrindo.total);
  el('rd-futuras').textContent=n(d.rodadas.futuras);
  el('radar-note').textContent=d.nota;
  el('rd-fases').innerHTML=phaseTable(d.fases);
  el('rd-situacoes').innerHTML=bars(d.rodadas.situacoes,VIZ.analise);
  el('rd-municipios').innerHTML=bars(d.rodadas.top_municipios,VIZ.abrindo);
  el('rd-noticias').innerHTML=newsBlock(d.noticias);
  el('rd-tendencias').innerHTML=trendBlock(d.noticias);
  el('rd-fonte').textContent=t('ov.sourcePrefix')+d.rodadas.fonte;
  el('radar-content').hidden=false;
 }catch(e){el('radar-error').textContent=e.message}
 finally{el('radar-loading').hidden=true}}

window.showRadar=()=>{if(loaded)return;loaded=true;load()};
})();
