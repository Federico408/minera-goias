/* Radar panel: register phases, availability rounds and the news collector's output.
   Every number here is a count of records in a source, never a forecast. */
(()=>{'use strict';
const el=id=>document.getElementById(id),escape=esc,n=v=>I18N.num(v);
const VIZ={confirmado:'#0f6fb0',analise:'#0d9488',abrindo:'#c2681b'};
const norm=s=>String(s).normalize('NFD').replace(/[̀-ͯ]/g,'').toUpperCase();
const area=v=>Number.isFinite(v)&&v>0?I18N.num(v,{maximumFractionDigits:2})+' ha':t('rd.semArea');
const PAGE=30;
let loaded=false,packet=null,records=null,phase='',shown=PAGE,selected=null;

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
  +rows.map(r=>`<tr class="rd-row" tabindex="0" role="button" data-fase="${escape(r.fase)}"`
   +` aria-label="${escape(t('rd.abrirFase',{fase:r.fase}))}">`
   +`<td><span class="rd-dot" style="background:${VIZ[r.grupo]}"></span>${escape(r.fase)}</td>`
   +`<td>${escape(n(r.processos))}</td></tr>`).join('')+'</tbody></table>'}

// The claims snapshot is ~2.6 MB, so it is only fetched once someone opens a phase.
async function openPhase(wanted){
 phase=wanted;shown=PAGE;selected=null;
 el('rd-explorer').hidden=false;
 el('rd-explorer-title').textContent=wanted;
 el('rd-search').value='';
 clearDetail();
 markPhase();
 el('rd-explorer').scrollIntoView({behavior:'smooth',block:'start'});
 if(!records){
  el('rd-explorer-sub').textContent=t('rd.carregandoProcessos');
  el('rd-list').innerHTML='';el('rd-count').textContent='';el('rd-more').hidden=true;
  try{const decoded=await window.loadProcesses();packet=decoded.packet;records=decoded.records}
  catch(e){el('rd-explorer-sub').textContent=e.message;return}
  if(phase!==wanted)return}
 renderList()}

function markPhase(){
 el('rd-fases').querySelectorAll('[data-fase]').forEach(row=>
  row.classList.toggle('active',row.dataset.fase===phase))}

function matching(){
 const q=norm(el('rd-search').value);
 return records.filter(r=>r.phase===phase&&(!q||norm(r.id+' '+r.mineral).includes(q)))}

function renderList(){
 const found=matching();
 el('rd-explorer-sub').textContent=t('rd.exploreSub',{n:n(found.length)});
 el('rd-count').textContent=found.length>shown?t('rd.mostrando',{n:n(shown),total:n(found.length)}):'';
 el('rd-list').innerHTML=found.length
  ?found.slice(0,shown).map(r=>`<button type="button" class="rd-item" data-id="${escape(r.id)}">`
    +`<b>${escape(r.id)}</b><span>${escape(r.mineral)}</span><span class="muted">${escape(area(r.area))}</span></button>`).join('')
  :`<div class="empty">${escape(t('rd.nenhumProcesso'))}</div>`;
 el('rd-more').hidden=found.length<=shown;
 el('rd-list').querySelectorAll('[data-id]').forEach(b=>b.onclick=()=>selectProcess(b.dataset.id));
 if(selected)markSelected()}

function markSelected(){
 el('rd-list').querySelectorAll('[data-id]').forEach(b=>
  b.classList.toggle('active',selected!=null&&b.dataset.id===selected.id))}

function clearDetail(){
 selected=null;
 el('rd-detail-title').textContent=t('rd.pickProcess');
 el('rd-detail-hint').hidden=false;
 el('rd-detail-body').innerHTML='';
 el('rd-detail-map').hidden=true}

function selectProcess(id){
 const found=records.find(r=>r.id===id&&r.phase===phase)||records.find(r=>r.id===id);
 if(!found)return;
 selected=found;
 el('rd-detail-title').textContent=t('rd.processo',{id:found.id});
 el('rd-detail-hint').hidden=true;
 el('rd-detail-body').innerHTML='<dl>'+[
  [t('rd.dFase'),found.phase],
  [t('rd.dGrupo'),packet.grupos[found.group]||t('rd.naoInformado')],
  [t('rd.dSubstancia'),found.mineral],
  [t('rd.dArea'),area(found.area)],
  [t('rd.dPoligonos'),n(found.rings.length)],
 ].map(([k,v])=>`<dt>${escape(k)}</dt><dd>${escape(v)}</dd>`).join('')+'</dl>';
 el('rd-detail-map').hidden=false;
 markSelected()}

function wireExplorer(){
 el('rd-fases').querySelectorAll('[data-fase]').forEach(row=>{
  const open=()=>openPhase(row.dataset.fase);
  row.onclick=open;
  row.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}}});
 el('rd-search').oninput=()=>{shown=PAGE;renderList()};
 el('rd-more').onclick=()=>{shown+=PAGE;renderList()};
 el('rd-explorer-close').onclick=()=>{el('rd-explorer').hidden=true;phase='';markPhase()};
 el('rd-detail-map').onclick=()=>{
  if(!selected)return;
  const tab=document.querySelector('[data-view="atlas"]');
  if(tab)tab.click();
  if(window.atlasShowProcess)window.atlasShowProcess(selected.id)}}

/* As matérias ficam aqui para os filtros trabalharem sem nova chamada à API. */
let NEWS=[];
const subName=s=>t('rd.s.'+s);
const viaBusca=link=>/news\.google\.com|bing\.com/.test(link||'');

function newsItem(i){
 const iso=(i.published_at||i.first_seen||'').slice(0,10);
 const quando=/^\d{4}-\d{2}-\d{2}$/.test(iso)?iso.slice(8)+'/'+iso.slice(5,7):iso;
 const marca=i.regional?`<span class="rd-tag-go">${escape(t('rd.regional'))}</span>`:'';
 const subs=(i.substancias||[]).map(s=>`<span class="rd-sub">${escape(subName(s))}</span>`).join('');
 // O link das buscas passa por uma tela do Google antes de chegar ao veículo.
 const indireto=viaBusca(i.link)?` · <span class="rd-indireto">${escape(t('rd.viaBusca'))}</span>`:'';
 return `<li><div class="rd-meta">${marca}${subs}<span class="rd-data">${escape(quando)}</span></div>`
  +`<a href="${escape(i.link)}" target="_blank" rel="noopener noreferrer">${escape(i.title)}</a>`
  +`<span class="rd-fonte">${escape(i.fonte||'')}${indireto}</span></li>`}

/* Quantas linhas a lista desenha de uma vez. O resto sai pelos filtros: uma lista de
   180 itens dentro de um painel vira rolagem sem fim. */
const NEWS_MAX=40;

function drawNews(){
 if(!el('rd-lista'))return;
 const valor=id=>{const e=el(id);return e?e.value:''};
 const marcado=id=>{const e=el(id);return e?e.checked:false};
 const busca=(valor('rd-busca')||'').toLowerCase().trim(),sub=valor('rd-substancia');
 const soSetor=marcado('rd-so-setor'),soGoias=marcado('rd-so-go');
 const vis=NEWS.filter(i=>(!busca||(i.title||'').toLowerCase().includes(busca))
  &&(!sub||(i.substancias||[]).includes(sub))
  &&(!soSetor||i.setorial)&&(!soGoias||i.regional));
 el('rd-conta').textContent=vis.length>NEWS_MAX
  ? t('rd.newsParcial',{mostradas:n(NEWS_MAX),filtradas:n(vis.length),total:n(NEWS.length)})
  : t('rd.newsMostrando',{mostradas:n(vis.length),total:n(NEWS.length)});
 el('rd-lista').innerHTML=vis.length?vis.slice(0,NEWS_MAX).map(newsItem).join('')
  :`<li class="empty">${escape(t('rd.semFiltro'))}</li>`}

function newsBlock(noticias){
 if(!noticias.disponivel){
  const motivo=noticias.motivo==='banco_ilegivel'?'rd.bancoIlegivel':'rd.semColetor';
  return `<div class="notice">${escape(t(motivo))}</div>`}
 NEWS=noticias.itens||[];
 if(!NEWS.length)return `<div class="empty">${escape(t('ov.empty'))}</div>`;
 const nomes=[...new Set(NEWS.flatMap(i=>i.substancias||[]))]
   .sort((a,b)=>subName(a).localeCompare(subName(b)));
 const opcoes=nomes.map(s=>`<option value="${escape(s)}">${escape(subName(s))}</option>`).join('');
 // O filtro "só mineração" só aparece quando há o que filtrar. O coletor manda a
 // seleção já ordenada pelo setor, então normalmente tudo que chega é do setor e o
 // controle seria um botão morto.
 const mistura=NEWS.some(i=>i.setorial)&&NEWS.some(i=>!i.setorial);
 const acervo=noticias.total!=null
  ? `<p class="rd-conta">${escape(t('rd.acervo',{total:n(noticias.total),
      regionais:n(noticias.regionais||0),setoriais:n(noticias.regionais_setoriais||0)}))}</p>`:'';
 const atualizado=noticias.atualizado_em
  ? `<p class="rd-conta">${escape(t('rd.atualizado'))} ${escape(noticias.atualizado_em.slice(0,16).replace('T',' '))}</p>`:'';
 return acervo+atualizado+'<div class="rd-filtros">'
  +`<input type="search" id="rd-busca" placeholder="${escape(t('rd.buscaPh'))}" aria-label="${escape(t('rd.buscaPh'))}">`
  +(nomes.length?`<select id="rd-substancia" aria-label="${escape(t('rd.todasSubstancias'))}">`
    +`<option value="">${escape(t('rd.todasSubstancias'))}</option>${opcoes}</select>`
    :'<select id="rd-substancia" hidden></select>')
  +(mistura?`<label class="rd-check"><input type="checkbox" id="rd-so-setor" checked>${escape(t('rd.soSetor'))}</label>`:'')
  +`<label class="rd-check"><input type="checkbox" id="rd-so-go">${escape(t('rd.soGoias'))}</label>`
  +'</div><p class="rd-conta" id="rd-conta"></p><ul class="rd-news" id="rd-lista"></ul>'}

function wireNews(){
 if(!el('rd-lista'))return;
 for(const id of ['rd-busca','rd-substancia','rd-so-setor','rd-so-go'])
  if(el(id))el(id).addEventListener('input',drawNews);
 drawNews()}

function trendBlock(noticias){
 if(!noticias.disponivel)return '';
 // Only signals the collector was willing to call are worth a row here.
 const rows=(noticias.tendencias||[]).filter(x=>x.verdict==='pressao_de_alta'||x.verdict==='pressao_de_baixa');
 // A leitura de alta/baixa está desligada no coletor, e uma seção permanentemente
 // vazia só confunde. Sem tendência, não desenha o bloco.
 if(!rows.length)return '';
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
  wireNews();
  el('rd-tendencias').innerHTML=trendBlock(d.noticias);
  el('rd-fonte').textContent=t('ov.sourcePrefix')+d.rodadas.fonte;
  wireExplorer();
  el('radar-content').hidden=false;
 }catch(e){el('radar-error').textContent=e.message}
 finally{el('radar-loading').hidden=true}}

window.showRadar=()=>{if(loaded)return;loaded=true;load()};
})();
