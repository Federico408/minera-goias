/* Panorama cards: declared use, territory, mineral research and availability rounds. */
(()=>{'use strict';
const cards=window.PN_CARDS=window.PN_CARDS||[];
cards.push(
{id:'usos',sec:'usos',wide:true,filters:['mun','min','emp','fase'],render(X){const C=X.C,rows=X.proc(),n=X.sumBy(rows,r=>r[5],()=>1),tot=rows.length;
 return C.hbar([...n.entries()].sort((a,b)=>b[1]-a[1]).slice(0,14).map(([u,v])=>({label:X.P.dims.uso[u],value:v})),{fmt:v=>C.fmt(v)+' · '+C.fmt(tot?v/tot*100:0,1)+'%',aria:X.t('pn.c.usos')})}},

{id:'fases',sec:'terr',filters:['mun','min','emp'],render(X,box){const C=X.C,rows=X.proc(['fase']),n=X.sumBy(rows,r=>r[0],()=>1),a=X.sumBy(rows,r=>r[0],r=>r[4]),tot=[...a.values()].reduce((s,v)=>s+v,0);
 C.table(box,[{label:X.t('pn.h.fase'),key:'f'},{label:X.t('pn.h.proc'),key:'n',num:1,fmt:v=>C.fmt(v)},{label:X.t('pn.h.area'),key:'a',num:1,fmt:v=>C.fmt(v,0)},{label:X.t('pn.h.pctArea'),key:'p',num:1,fmt:v=>C.fmt(v,1)}],
  [...n.entries()].map(([f,v])=>({f:X.P.dims.fase[f],n:v,a:a.get(f)||0,p:tot?(a.get(f)||0)/tot*100:0})).sort((x,y)=>y.a-x.a),{limit:15})}},
{id:'area_min',sec:'terr',filters:['mun','emp','fase'],render(X){const C=X.C,by=X.sumBy(X.proc(['min']),r=>r[1],r=>r[4]);
 return C.hbar(X.topRows(by,12,i=>X.min(i)),{fmt:v=>C.fmt(v,0)+' ha',aria:X.t('pn.c.area_min')})}},
{id:'decadas',sec:'terr',filters:['mun','min','emp','fase'],render(X){const C=X.C,by=X.sumBy(X.proc().filter(r=>r[7]>0),r=>Math.floor(r[7]/10)*10,()=>1),keys=[...by.keys()].sort((a,b)=>a-b);
 return C.vbar(keys.map(k=>X.t('pn.decade',{d:k})),[{name:X.t('pn.h.proc'),values:keys.map(k=>by.get(k))}],{fmt:v=>C.fmt(v),axis:v=>C.fmt(v),aria:X.t('pn.c.decadas')})}},

{id:'inv_ano',sec:'pesq',filters:['ano','min','rub'],render(X){const C=X.C,years=X.years(2001,2025),by=X.sumBy(X.inv(),r=>r[0],r=>r[3]);
 return C.vbar(years.map(String),[{name:X.t('pn.h.invest'),values:years.map(y=>by.get(y)||0)}],{fmt:v=>C.money(v,0),aria:X.t('pn.c.inv_ano')})}},
{id:'inv_share',sec:'pesq',filters:['ano','rub'],render(X){const C=X.C;
 if(X.F.min>=0)return `<p class="notice">${X.E(X.t('pn.invShareMin'))}</p>`;
 const years=X.years(2001,2025),go=X.sumBy(X.inv(),r=>r[0],r=>r[3]),br=X.sumBy(X.invBr(),r=>r[0],r=>r[2]);
 return C.line(years.map(String),[{name:X.t('pn.h.shareGo'),values:years.map(y=>br.get(y)?(go.get(y)||0)/br.get(y)*100:null)}],{fmt:v=>C.fmt(v,2)+' %',axis:v=>C.fmt(v,1)+'%',aria:X.t('pn.c.inv_share')})}},
{id:'inv_sub',sec:'pesq',filters:['ano','rub'],render(X){const C=X.C,by=X.sumBy(X.inv(['min']),r=>r[1],r=>r[3]);
 return C.hbar(X.topRows(by,12,i=>X.P.dims.subinv[i][0]),{fmt:v=>C.money(v,0),aria:X.t('pn.c.inv_sub')})}},
{id:'inv_rub',sec:'pesq',filters:['ano','min'],render(X){const C=X.C,by=X.sumBy(X.inv(['rub']),r=>r[2],r=>r[3]);
 return C.hbar(X.topRows(by,12,i=>X.t(`pn.rub.${X.P.dims.rubrica[i]}`)),{fmt:v=>C.money(v,0),aria:X.t('pn.c.inv_rub')})}},
{id:'tr',sec:'pesq',wide:true,filters:['ano','rub'],render(X,box){const C=X.C,P=X.P,F=X.F,tr=P.dims.min.findIndex(m=>/TERRAS.RARAS/.test(X.norm(m[1])));
 const isTr=i=>P.dims.subinv[i][1]===tr||/TERRAS.RARAS|MONAZITA/.test(X.norm(P.dims.subinv[i][0]));
 const inv=X.sumBy(P.inv_go.rows.filter(r=>r[0]>=F.y0&&r[0]<=F.y1&&(F.rub<0||r[2]===F.rub)&&isTr(r[1])),r=>r[0],r=>r[3]);
 const amb=P.amb_go.rows.filter(r=>tr>=0&&r[1]===tr&&r[0]>=F.y0&&r[0]<=F.y1),q=X.sumBy(amb,r=>r[0],r=>r[4]),v=X.sumBy(amb,r=>r[0],r=>r[5]);
 const years=[...new Set([...inv.keys(),...q.keys(),...v.keys()])].sort((a,b)=>b-a);
 C.table(box,[{label:X.t('pn.h.year'),key:'y'},{label:X.t('pn.h.invest'),key:'i',num:1,fmt:x=>x?C.money(x,0):'—'},{label:X.t('pn.h.benefT'),key:'q',num:1,fmt:x=>x?C.fmt(x,2):'—'},
  {label:X.t('pn.h.benefRs'),key:'v',num:1,fmt:x=>x?C.money(x,0):'—'},{label:X.t('pn.h.rsT'),key:'p',num:1,fmt:x=>x?C.money(x,0):'—'}],
  years.map(y=>({y,i:inv.get(y)||0,q:q.get(y)||0,v:v.get(y)||0,p:(q.get(y)||0)>0?(v.get(y)||0)/q.get(y):0})),{limit:16})}},

{id:'rod_sit',sec:'rod',filters:['mun','min'],render(X,box){const C=X.C,g=new Map();
 X.rod().forEach(r=>{const a=g.get(r[1])||{n:0,ha:0,l:0};a.n++;a.ha+=r[5];a.l+=r[6];g.set(r[1],a)});
 C.table(box,[{label:X.t('pn.h.sit'),get:e=>X.P.dims.sit[e[0]]},{label:X.t('pn.h.areas'),get:e=>e[1].n,num:1,fmt:v=>C.fmt(v)},{label:X.t('pn.h.area'),get:e=>e[1].ha,num:1,fmt:v=>C.fmt(v,0)},
  {label:X.t('pn.h.lances'),get:e=>e[1].l,num:1,fmt:v=>C.money(v,0)}],[...g.entries()].sort((a,b)=>b[1].n-a[1].n),{limit:10})}},
{id:'rod_mun',sec:'rod',filters:['min'],render(X){const C=X.C,by=X.sumBy(X.rod(['mun']),r=>r[4],()=>1);
 return C.hbar(X.topRows(by,12,i=>X.mun(i)),{fmt:v=>C.fmt(v),aria:X.t('pn.c.rod_mun')})}},
{id:'rod_top',sec:'rod',wide:true,filters:['mun','min'],render(X,box){const C=X.C,P=X.P;
 C.table(box,[{label:X.t('pn.h.rodada'),get:r=>r[0]},{label:X.t('pn.h.processo'),get:r=>r[8]},{label:X.t('pn.h.mun'),get:r=>X.mun(r[4])},{label:X.t('pn.h.min'),get:r=>r[9]>=0?X.min(r[9]):'—'},
  {label:X.t('pn.h.area'),get:r=>r[5],num:1,fmt:v=>C.fmt(v,2)},{label:X.t('pn.h.lance'),get:r=>r[6],num:1,fmt:v=>C.money(v,0)},{label:X.t('pn.h.venc'),get:r=>r[7]<0?'—':(P.dims.venc[r[7]]||X.t('pn.pf'))}],
  X.rod().filter(r=>r[6]>0).sort((a,b)=>b[6]-a[6]),{limit:10})}}
);
})();
