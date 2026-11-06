// Node'da GameCore'u arayüzsüz çalıştırır (oyun HTML'inden CORE bloğunu çıkarır)
const fs=require('fs'); const t=fs.readFileSync(process.argv[2],'utf8');
const src=t.slice(t.indexOf('/*CORE-START*/'),t.indexOf('/*CORE-END*/'));
const CORE=new Function(src+';return CORE;')();
let seed=12345; const R=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296}, rr=(a,b)=>a+R()*(b-a);
const ok=(c,m)=>{console.log((c?'OK  ':'FAIL')+' '+m); if(!c) process.exitCode=1};
ok(CORE.rankOf(0).name==='Gezgin'&&CORE.rankOf(19500).name==='Ölümsüz','unvanlar');
ok(CORE.rankGain(0,20,'orc',10).add===0,'9 seviyeden düşük canavar puan vermez');
ok(CORE.rankGain(0,20,'orc',11).add>0,'9 seviye farkı puan verir');
ok(CORE.rankGain(19990,30,'boss',30).rp===20000,'üst sınır 20000');
let hits=0,miss=0,crit=0,dmgSum=0; for(let i=0;i<20000;i++){ const r=CORE.playerAttack({power:100,mul:1,mobLvl:10,dex:4,quiet:false},R,rr); if(r.miss) miss++; else {hits++; dmgSum+=r.dmg; if(r.crit) crit++;} }
ok(Math.abs(miss/20000-0.0668)<.01,'ıska oranı ~%7 ('+(miss/200).toFixed(1)+'%)'); ok(Math.abs(crit/hits-0.136)<.015,'kritik oranı ~%13.6 ('+(crit/hits*100).toFixed(1)+'%)');
const kr=CORE.killRewards('boss',16,true,14,R,rr); ok(kr.xp===CORE.mobExp(16,14)&&kr.drops.filter(d=>d.kind==='yang').length===2&&kr.drops.some(d=>d.kind==='ustone'&&d.amount===3),'boss ödülleri');
ok(CORE.damageToPlayer(100,20,.75)===Math.round((100-8)*.75),'savunma hesabı');
console.log('expNeed(10)=',CORE.expNeed(10),' maxHP(18,12)=',CORE.maxHP(18,12),' mobHP(wolf,10)=',CORE.mobHP(1,10));
