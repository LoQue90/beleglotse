const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync(require('node:path').join(__dirname,'../index.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];new vm.Script(script);
const code=script.slice(script.indexOf('async function deleteHistoryEntry('),script.indexOf('async function loadHistory()'));
(async()=>{
 let accepted=false,prompt='',calls=[],invalidations=0,loads=0;
 const context=vm.createContext({confirm:s=>{prompt=s;return accepted},run:async(b,f)=>f(),api:async(path,p)=>{calls.push([path,p]);return {internal:'VTUER26001'}},cfg:{year_file:'2026.belegdb'},invalidate:()=>invalidations++,showStatus:()=>{},loadHistory:async()=>loads++});
 vm.runInContext(code,context);const row={id:'hash',internal:'VTUER26001',provider:'Lieferant',number:'R1'};
 await context.deleteHistoryEntry(row,{});assert.equal(calls.length,0);assert(prompt.includes('VTUER26001'));assert(prompt.includes('PDF und TSV bleiben erhalten'));
 accepted=true;await context.deleteHistoryEntry(row,{});assert.equal(calls[0][0],'history/delete');assert.equal(calls[0][1].id,'hash');assert.equal(calls[0][1].year_file,'2026.belegdb');assert.equal(calls[0][1].confirmed,true);assert.equal(invalidations,1);assert.equal(loads,1);
 console.log('History deletion UI: confirmation/cancel, request and refresh passed.');
})().catch(e=>{console.error(e);process.exit(1)});
