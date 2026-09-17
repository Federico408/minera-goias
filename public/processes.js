/* ANM claims snapshot, decoded once and shared: the atlas draws the polygons, the radar lists them.
   The packet is ~2.6 MB, so it is only fetched when a view actually asks for it. */
(()=>{'use strict';
let pending=null;
async function decode(){
 const p=await api('/atlas/processes');
 const bin=(s,T)=>{const b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));return new T(b.buffer)};
 const xy=bin(p.xy,Uint16Array),rs=bin(p.ringStart,Uint32Array),rp=bin(p.ringPoly,Uint16Array),
  gr=bin(p.g,Uint8Array),fa=bin(p.fase,Uint8Array),su=bin(p.subs,Uint16Array),ar=bin(p.area,Float32Array),
  ids=p.processo.split('\x01'),b=p.bounds;
 const records=Array.from({length:p.n},(_,i)=>({id:ids[i],group:gr[i],phase:p.dFase[fa[i]]||t('at.notInformed'),
  mineral:p.dSubs[su[i]]||t('at.notInformed'),area:ar[i],rings:[]}));
 for(let r=0;r<rp.length;r++){const ring=[];
  for(let i=rs[r];i<rs[r+1];i++)ring.push([b.lat1-xy[2*i+1]/65535*(b.lat1-b.lat0),b.lon0+xy[2*i]/65535*(b.lon1-b.lon0)]);
  records[rp[r]].rings.push(ring)}
 return {packet:p,records}}
window.loadProcesses=()=>pending||(pending=decode().catch(e=>{pending=null;throw e}));
})();
