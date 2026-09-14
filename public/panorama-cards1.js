/* Panorama cards: summary, CFEM, geography, substances and production (AMB). */
(()=>{'use strict';
const cards=window.PN_CARDS=window.PN_CARDS||[];
const sum=(rows,i)=>rows.reduce((s,r)=>s+(r[i]||0),0);
const lastYear=rows=>rows.reduce((m,r)=>Math.max(m,r[0]),0);
// A caption line above a table; returns the element the table goes into.
const tableIn=(X,box,caption)=>{box.innerHTML=`<p class="small muted">${X.E(caption)}</p><div></div>`;return box.lastElementChild};
cards.push(
{id:'tiles',sec:'resumo',wide:true,filters:['ano','mes','mun','min','emp'],render(X){const C=X.C,amb=X.amb(),last=lastYear(amb),pr=X.proc(),muns=new Set(pr.map(r=>r[2]).filter(i=>i>=0)).size;
 return '<div class="metrics pn-tiles">'+C.tiles([
  ['tone-a',X.t('pn.k.cfem'),'R$ '+C.short(sum(X.cfem(),5)),X.t('pn.k.cfemSub',{p:X.period(2022,2026)})],
  ['tone-b',X.t('pn.k.benef'),last?'R$ '+C.short(sum(amb.filter(r=>r[0]===last),5)):'—',X.t('pn.k.benefSub',{y:last||'—'})],
  ['tone-c',X.t('pn.k.proc'),C.fmt(pr.length),X.t('pn.k.procSub',{ha:C.short(sum(pr,4)),m:C.fmt(muns)})],
  ['tone-d',X.t('pn.k.inv'),'R$ '+C.short(sum(X.inv(),3)),X.t('pn.k.invSub',{p:X.period(2001,2025)})],
  ['tone-a',X.t('pn.k.ee'),C.fmt(sum(X.ccee(),6)/1000,1)+' GWh',X.t('pn.k.eeSub',{p:X.period(2024,2026)})]])+'</div>'}},

{id:'cfem_ano',sec:'cfem',filters:['ano','mes','mun','min','emp'],render(X){const C=X.C,years=X.years(2022,2026),by=X.sumBy(X.cfem(),r=>r[0],r=>r[5]);
 return C.vbar(years.map(String),[{name:'CFEM',values:years.map(y=>by.get(y)||0)}],{fmt:v=>C.money(v),partial:new Set(['2026']),aria:X.t('pn.c.cfem_ano')})}},
{id:'cfem_janjul',sec:'cfem',filters:['ano','mun','min','emp'],render(X){const C=X.C,years=X.years(2022,2026),by=X.sumBy(X.cfem(['mes']).filter(r=>r[1]<=7),r=>r[0],r=>r[5]);
 return C.vbar(years.map(String),[{name:'CFEM',values:years.map(y=>by.get(y)||0)}],{fmt:v=>C.money(v),aria:X.t('pn.c.cfem_janjul')})}},
{id:'cfem_mes',sec:'cfem',wide:true,filters:['ano','mes','mun','min','emp'],render(X){const C=X.C,by=X.sumBy(X.cfem(),r=>r[0]*100+r[1],r=>r[5]),keys=[...by.keys()].sort((a,b)=>a-b);
 return C.line(keys.map(k=>Math.floor(k/100)+'-'+String(k%100).padStart(2,'0')),[{name:'CFEM',values:keys.map(k=>by.get(k))}],{fmt:v=>C.money(v),aria:X.t('pn.c.cfem_mes')})}},

{id:'mapa',sec:'geo',wide:true,filters:['ano','mes','mun','min','emp','fase','ramo'],render(X,box){const C=X.C,F=X.F;
 if(!X.A)return `<p class="empty">${X.E(X.t('pn.noAtlas'))}</p>`;
 const metric=X.mapMetric,vals=new Map(),add=(i,v)=>{if(i>=0){const c=X.munCode(i);vals.set(c,(vals.get(c)||0)+v)}};
 if(metric==='cfem')X.cfem().forEach(r=>add(r[2],r[5]));
 else if(metric==='proc'||metric==='area')X.proc().forEach(r=>add(r[2],metric==='proc'?1:r[4]));
 else X.ccee().forEach(r=>add(r[1],r[6]/1000));
 const f={cfem:v=>C.money(v,0),proc:v=>C.fmt(v),area:v=>C.fmt(v,0)+' ha',ee:v=>C.fmt(v,1)+' GWh'}[metric];
 box.innerHTML=`<div class="pn-map-tools"><label>${X.E(X.t('pn.mapMetric'))} <select class="pn-map-metric">`
  +['cfem','proc','area','ee'].map(m=>`<option value="${m}"${m===metric?' selected':''}>${X.E(X.t(`pn.map.${m}`))}</option>`).join('')
  +`</select></label><span class="small muted">${X.E(X.t('pn.mapHint'))}</span></div><div class="pn-map-box"></div>`;
 box.querySelector('.pn-map-metric').onchange=e=>{X.mapMetric=e.target.value;X.renderCard('mapa')};
 C.map(box.querySelector('.pn-map-box'),X.A.municipalities,vals,{fmt:f,selected:F.mun>=0?X.munCode(F.mun):'',onPick:X.pickMun,aria:X.t('pn.c.mapa')})}},
{id:'mun_cfem',sec:'geo',filters:['ano','mes','min','emp'],render(X,box){const C=X.C,by=X.sumBy(X.cfem(['mun']),r=>r[2],r=>r[5]),tot=[...by.values()].reduce((s,v)=>s+v,0);let acc=0;
 const list=[...by.entries()].sort((a,b)=>b[1]-a[1]).map(([m,v],i)=>{acc+=v;return {pos:i+1,mun:X.mun(m),v,p:tot?v/tot*100:0,a:tot?acc/tot*100:0}});
 C.table(box,[{label:'#',key:'pos',num:1},{label:X.t('pn.h.mun'),key:'mun'},{label:X.t('pn.h.cfem'),key:'v',num:1,fmt:v=>C.money(v)},{label:'%',key:'p',num:1,fmt:v=>C.fmt(v,1)},{label:X.t('pn.h.acum'),key:'a',num:1,fmt:v=>C.fmt(v,1)}],list,{limit:12})}},
{id:'mun_proc',sec:'geo',filters:['min','emp','fase'],render(X,box){const C=X.C,rows=X.proc(['mun']),n=X.sumBy(rows,r=>r[2],()=>1),a=X.sumBy(rows,r=>r[2],r=>r[4]);
 C.table(box,[{label:'#',key:'pos',num:1},{label:X.t('pn.h.mun'),key:'mun'},{label:X.t('pn.h.proc'),key:'n',num:1,fmt:v=>C.fmt(v)},{label:X.t('pn.h.area'),key:'a',num:1,fmt:v=>C.fmt(v,0)}],
  [...n.entries()].sort((x,y)=>y[1]-x[1]).map(([m,v],i)=>({pos:i+1,mun:X.mun(m),n:v,a:a.get(m)||0})),{limit:12})}},

{id:'cfem_min',sec:'subs',filters:['ano','mes','mun','emp'],render(X){const C=X.C,by=X.sumBy(X.cfem(['min']),r=>r[3],r=>r[5]);
 return C.hbar(X.topRows(by,15,i=>X.min(i)),{fmt:v=>C.money(v,0),aria:X.t('pn.c.cfem_min')})}},
{id:'cfem_min_ano',sec:'subs',wide:true,filters:['ano','mes','mun','min','emp'],render(X){const C=X.C,years=X.years(2022,2026);
 return C.vbar(years.map(String),X.stackSeries(X.cfem(),r=>r[3],r=>r[0],r=>r[5],years,6,i=>X.min(i)),{stacked:true,fmt:v=>C.money(v,0),partial:new Set(['2026']),aria:X.t('pn.c.cfem_min_ano')})}},

{id:'benef_ano',sec:'prod',wide:true,filters:['ano','min'],render(X){const C=X.C,years=X.years(2010,2025);
 return C.vbar(years.map(String),X.stackSeries(X.amb(),r=>r[1],r=>r[0],r=>r[5],years,6,i=>X.min(i)),{stacked:true,fmt:v=>C.money(v,0),aria:X.t('pn.c.benef_ano')})}},
{id:'benef_share',sec:'prod',filters:['ano','min'],render(X){const C=X.C,years=X.years(2010,2025),go=X.sumBy(X.amb(),r=>r[0],r=>r[5]),br=X.sumBy(X.ambBr(),r=>r[0],r=>r[3]);
 return C.line(years.map(String),[{name:X.t('pn.h.shareGo'),values:years.map(y=>br.get(y)?(go.get(y)||0)/br.get(y)*100:null)}],{fmt:v=>C.fmt(v,2)+' %',axis:v=>C.fmt(v,1)+'%',aria:X.t('pn.c.benef_share')})}},
{id:'rom_ano',sec:'prod',filters:['ano','min'],render(X){const C=X.C,years=X.years(2010,2025),by=X.sumBy(X.amb(),r=>r[0],r=>r[2]/1e6);
 return C.vbar(years.map(String),[{name:'ROM',values:years.map(y=>by.get(y)||0)}],{fmt:v=>C.fmt(v,2)+' Mt',axis:v=>C.fmt(v,0),aria:X.t('pn.c.rom_ano')})}},
{id:'prod_ultimo',sec:'prod',filters:['ano','min'],render(X,box){const C=X.C,amb=X.amb(),last=lastYear(amb),rows=amb.filter(r=>r[0]===last&&(r[2]>0||r[4]>0||r[5]>0)).sort((a,b)=>b[5]-a[5]);
 C.table(tableIn(X,box,X.t('pn.refYear',{y:last||'—'})),[{label:X.t('pn.h.min'),get:r=>X.min(r[1])},{label:X.t('pn.h.rom'),get:r=>r[2],num:1,fmt:v=>C.fmt(v,0)},
  {label:X.t('pn.h.benefT'),get:r=>r[4],num:1,fmt:v=>C.fmt(v,2)},{label:X.t('pn.h.benefRs'),get:r=>r[5],num:1,fmt:v=>C.money(v,0)}],rows,{limit:12})}},
{id:'rom_classe',sec:'prod',filters:['ano','min'],render(X){const C=X.C,amb=X.amb(),last=lastYear(amb),
  by=X.sumBy(amb.filter(r=>r[0]===last),r=>(r[1]>=0&&X.P.dims.min[r[1]][2])||X.t('pn.notInformed'),r=>r[2]/1e6);
 return `<p class="small muted">${X.E(X.t('pn.refYear',{y:last||'—'}))}</p>`+C.hbar(X.topRows(by,10,k=>k),{fmt:v=>C.fmt(v,2)+' Mt'})}},
{id:'contido',sec:'prod',filters:['ano','min'],render(X,box){const C=X.C,amb=X.amb(),last=lastYear(amb),rows=amb.filter(r=>r[0]===last&&(r[6]>0||r[7]>0)).sort((a,b)=>b[7]-a[7]||b[6]-a[6]);
 C.table(tableIn(X,box,X.t('pn.refYear',{y:last||'—'})),[{label:X.t('pn.h.min'),get:r=>X.min(r[1])},{label:X.t('pn.h.contRom'),get:r=>r[6],num:1,fmt:v=>v?C.fmt(v,2):'—'},
  {label:X.t('pn.h.contBenef'),get:r=>r[7],num:1,fmt:v=>v?C.fmt(v,2):'—'}],rows,{limit:12})}},
{id:'uf_rank',sec:'prod',filters:['ano'],render(X,box){const C=X.C,rows=X.P.amb_uf.rows.filter(r=>r[0]>=X.F.y0&&r[0]<=X.F.y1),last=lastYear(rows),cur=rows.filter(r=>r[0]===last),tot=sum(cur,3);
 C.table(tableIn(X,box,X.t('pn.refYear',{y:last||'—'})),[{label:'#',key:'pos',num:1},{label:'UF',key:'uf'},{label:X.t('pn.h.benefRs'),key:'v',num:1,fmt:v=>C.money(v,0)},{label:'%',key:'p',num:1,fmt:v=>C.fmt(v,1)},
  {label:X.t('pn.h.rom'),key:'rom',num:1,fmt:v=>C.fmt(v,0)}],cur.sort((a,b)=>b[3]-a[3]).map((r,i)=>({pos:i+1,uf:X.P.dims.uf[r[1]],v:r[3],p:tot?r[3]/tot*100:0,rom:r[2]})),{limit:10})}}
);
})();
