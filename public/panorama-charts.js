/* Panorama: small SVG charts, tables and a municipality map shared by the Panorama cards. */
(()=>{'use strict';
const PALETTE=['#0f6fb0','#c2681b','#0d9488','#b03a55','#8250c4','#d7a43a','#57768b','#5aa9d6'],OTHER='#c3ccd3',RAMP=['#d7e9f6','#a8cde9','#6fa9d4','#3684b9','#07588b'];
const E=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,d=0)=>v==null||!Number.isFinite(v)?'—':I18N.num(v,{maximumFractionDigits:d});
const money=(v,d=2)=>v==null||!Number.isFinite(v)?'—':'R$ '+fmt(v,d);
const clip=(s,n)=>{s=String(s??'');return s.length>n?s.slice(0,n-1)+'…':s};
function short(v){if(v==null||!Number.isFinite(v))return '—';const a=Math.abs(v);
 if(a>=1e9)return fmt(v/1e9,2)+' '+t('pn.u.bi');if(a>=1e6)return fmt(v/1e6,1)+' '+t('pn.u.mi');if(a>=1e4)return fmt(v/1e3,1)+' '+t('pn.u.k');return fmt(v,a<10?2:0)}
const niceStep=v=>{if(!(v>0))return 1;const p=Math.pow(10,Math.floor(Math.log10(v))),n=v/p;return (n<=1?1:n<=1.5?1.5:n<=2?2:n<=2.5?2.5:n<=3?3:n<=4?4:n<=5?5:n<=7.5?7.5:10)*p};
const niceTop=v=>niceStep(Math.max(v,1e-9)/4)*4;
const empty=()=>`<p class="empty">${E(t('pn.empty'))}</p>`;
const color=(s,j)=>s.color||PALETTE[j%PALETTE.length];
function legend(series){return `<div class="pn-legend">${series.map((s,j)=>`<span><i style="background:${color(s,j)}"></i>${E(s.name)}</span>`).join('')}</div>`}

// Horizontal bars: rows [{label,value,color}].
function hbar(rows,o={}){
 rows=rows.filter(r=>r.value>0);if(!rows.length)return empty();
 const f=o.fmt||(v=>fmt(v,1)),rowH=24,left=o.left||230,W=860,w=W-left-120,h=rows.length*rowH+8,max=niceTop(Math.max(...rows.map(r=>r.value)));
 let s=`<svg viewBox="0 0 ${W} ${h}" role="img" aria-label="${E(o.aria||'')}">`;
 rows.forEach((r,i)=>{const y=4+i*rowH,bw=r.value/max*w;
  s+=`<text x="${left-8}" y="${y+15}" text-anchor="end" font-size="11" fill="#34495a">${E(clip(r.label,36))}<title>${E(r.label)}</title></text>`
   +`<rect x="${left}" y="${y+4}" width="${bw}" height="${rowH-9}" rx="3" fill="${r.color||o.color||PALETTE[0]}"><title>${E(r.label)}: ${E(f(r.value))}</title></rect>`
   +`<text x="${left+bw+6}" y="${y+15}" font-size="10.5" fill="#4a6070" font-weight="600">${E(f(r.value))}</text>`});
 return s+'</svg>'}

function axes(left,right,top,bottom,W,max,axisFmt){let s='';
 for(let k=0;k<=4;k++){const y=bottom-(bottom-top)*k/4;s+=`<line x1="${left}" x2="${W-right}" y1="${y}" y2="${y}" stroke="#e8eef3"/><text x="${left-6}" y="${y+4}" text-anchor="end" font-size="10" fill="#8395a3">${E(axisFmt(max*k/4))}</text>`}
 return s}

// Vertical bars, grouped or stacked: series [{name,values,color}]; o.partial marks labels drawn lighter.
function vbar(labels,series,o={}){
 if(!labels.length||!series.length||!series.some(x=>x.values.some(v=>v>0)))return empty();
 const f=o.fmt||(v=>fmt(v,1)),W=860,H=280,left=70,right=10,top=14,bottom=248,n=labels.length,step=(W-left-right)/n,stacked=!!o.stacked;
 const tot=i=>stacked?series.reduce((a,x)=>a+(x.values[i]||0),0):Math.max(...series.map(x=>x.values[i]||0));
 const max=niceTop(Math.max(...labels.map((_,i)=>tot(i))));
 let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${E(o.aria||'')}">`+axes(left,right,top,bottom,W,max,o.axis||short);
 const every=Math.ceil(n/18);
 labels.forEach((lab,i)=>{const x0=left+i*step,op=o.partial&&o.partial.has(lab)?.55:1;
  if(stacked){let base=bottom;series.forEach((se,j)=>{const v=se.values[i]||0,hh=v/max*(bottom-top);if(hh>0){s+=`<rect x="${x0+step*.18}" y="${base-hh}" width="${step*.64}" height="${hh}" fill="${color(se,j)}" opacity="${op}"><title>${E(lab)} · ${E(se.name)}: ${E(f(v))}</title></rect>`;base-=hh}})}
  else{const bw=step*.7/series.length;series.forEach((se,j)=>{const v=se.values[i]||0,hh=Math.max(v,0)/max*(bottom-top);s+=`<rect x="${x0+step*.15+j*bw}" y="${bottom-hh}" width="${bw*.9}" height="${hh}" rx="2" fill="${color(se,j)}" opacity="${op}"><title>${E(lab)}${series.length>1?' · '+E(se.name):''}: ${E(f(v))}</title></rect>`})}
  if((stacked||series.length===1)&&n<=20){const v=tot(i);if(v>0)s+=`<text x="${x0+step/2}" y="${bottom-v/max*(bottom-top)-5}" text-anchor="middle" font-size="9.5" fill="#4a6070" font-weight="600">${E(short(v))}</text>`}
  if(i%every===0)s+=`<text x="${x0+step/2}" y="${bottom+16}" text-anchor="middle" font-size="10" fill="#8395a3">${E(lab)}</text>`});
 return s+'</svg>'+(series.length>1?legend(series):'')}

// Lines: null values break the line.
function line(labels,series,o={}){
 const all=series.flatMap(x=>x.values).filter(v=>v!=null&&Number.isFinite(v));if(!labels.length||!all.length)return empty();
 const f=o.fmt||(v=>fmt(v,1)),W=860,H=280,left=70,right=14,top=14,bottom=248,n=labels.length,step=n>1?(W-left-right-20)/(n-1):0,max=niceTop(Math.max(...all,0));
 let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${E(o.aria||'')}">`+axes(left,right,top,bottom,W,max,o.axis||short);
 const X=i=>left+10+i*step,Y=v=>bottom-v/max*(bottom-top),every=Math.ceil(n/14);
 series.forEach((se,j)=>{let d='';se.values.forEach((v,i)=>{if(v==null||!Number.isFinite(v)){d+=' ';return}d+=(d===''||d.endsWith(' ')?'M':'L')+X(i).toFixed(1)+' '+Y(v).toFixed(1)});
  s+=`<path d="${d.replace(/ M/g,'M').trim()}" fill="none" stroke="${color(se,j)}" stroke-width="2.2"/>`;
  se.values.forEach((v,i)=>{if(v!=null&&Number.isFinite(v))s+=`<circle cx="${X(i)}" cy="${Y(v)}" r="${n>30?1.8:3}" fill="${color(se,j)}"><title>${E(labels[i])}${series.length>1?' · '+E(se.name):''}: ${E(f(v))}</title></circle>`})});
 labels.forEach((lab,i)=>{if(i%every===0)s+=`<text x="${X(i)}" y="${bottom+16}" text-anchor="middle" font-size="10" fill="#8395a3">${E(lab)}</text>`});
 return s+'</svg>'+(series.length>1?legend(series):'')}

// Table with "show all": cols [{label,key|get,fmt,num}], rows of objects.
function table(box,cols,rows,o={}){const base=o.limit||10;let limit=base;
 const draw=()=>{const head=cols.map(c=>`<th${c.num?' class="num"':''}>${E(c.label)}</th>`).join('');
  const body=rows.slice(0,limit).map(r=>'<tr>'+cols.map(c=>{const v=c.get?c.get(r):r[c.key];return `<td${c.num?' class="num"':''}>${E(c.fmt?c.fmt(v,r):v)}</td>`}).join('')+'</tr>').join('');
  box.innerHTML=`<div class="table-wrap"><table class="pn-table"><thead><tr>${head}</tr></thead><tbody>${body||`<tr><td colspan="${cols.length}" class="empty">${E(t('pn.empty'))}</td></tr>`}</tbody></table></div>`
   +(rows.length>limit?`<button type="button" class="link-button pn-more">${E(t('pn.showAll',{n:fmt(rows.length)}))}</button>`:limit>base?`<button type="button" class="link-button pn-more">${E(t('pn.showLess'))}</button>`:'');
  const b=box.querySelector('.pn-more');if(b)b.onclick=()=>{limit=limit>base?base:rows.length;draw()}};
 draw()}

// Municipality choropleth drawn from the atlas rings ([lat,lon]); quantile colours of the positive values.
function map(box,muns,values,o={}){
 let lon0=Infinity,lon1=-Infinity,lat0=Infinity,lat1=-Infinity;
 muns.forEach(m=>m.rings.forEach(r=>r.forEach(([la,lo])=>{if(lo<lon0)lon0=lo;if(lo>lon1)lon1=lo;if(la<lat0)lat0=la;if(la>lat1)lat1=la})));
 const W=560,H=500,k=Math.cos((lat0+lat1)/2*Math.PI/180),sc=Math.min((W-20)/((lon1-lon0)*k),(H-20)/(lat1-lat0)),X=lo=>10+(lo-lon0)*k*sc,Y=la=>10+(lat1-la)*sc;
 const f=o.fmt||(v=>fmt(v,1)),vals=[...values.values()].filter(v=>v>0).sort((a,b)=>a-b);
 const cuts=[...new Set([1,2,3,4].map(i=>vals[Math.floor(vals.length*i/5)]).filter(v=>v!=null&&v>vals[0]))];
 const paint=v=>!(v>0)?'#edf1f4':RAMP[cuts.filter(c=>v>=c).length];
 let s=`<svg viewBox="0 0 ${W} ${H}" class="pn-map" role="img" aria-label="${E(o.aria||'')}">`,sel='';
 muns.forEach(m=>{const v=values.get(m.code),d=m.rings.map(r=>'M'+r.map(([la,lo])=>X(lo).toFixed(1)+' '+Y(la).toFixed(1)).join('L')+'Z').join('');
  const p=`<path d="${d}" fill="${paint(v)}" stroke="${m.code===o.selected?'#07345c':'#ffffff'}" stroke-width="${m.code===o.selected?2:.5}" fill-rule="evenodd" data-code="${E(m.code)}"><title>${E(m.name)}: ${E(v>0?f(v):t('pn.noRecord'))}</title></path>`;
  if(m.code===o.selected)sel=p;else s+=p});
 s+=sel+'</svg>';
 const steps=vals.length?[vals[0],...cuts]:[];
 box.innerHTML=s+`<div class="pn-legend">`+[['#edf1f4',t('pn.noRecord')],...steps.map((c,i)=>[RAMP[i],t('pn.from')+' '+f(c)])].map(([c,l])=>`<span><i style="background:${c}"></i>${E(l)}</span>`).join('')+'</div>';
 if(o.onPick)box.querySelectorAll('path[data-code]').forEach(p=>{p.style.cursor='pointer';p.onclick=()=>o.onPick(p.dataset.code)})}

const tiles=items=>items.map(([tone,label,value,note])=>`<div class="metric ${tone}"><span>${E(label)}</span><strong>${E(value)}</strong><small>${E(note)}</small></div>`).join('');

window.PNC={E,fmt,money,short,clip,hbar,vbar,line,table,map,tiles,empty,PALETTE,OTHER};
})();
