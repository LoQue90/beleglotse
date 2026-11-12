const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync(require('node:path').join(__dirname,'../index.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];new vm.Script(script);
const elements=new Map();function element(){return {value:'',textContent:'',hidden:false,children:[],replaceChildren(){this.children=[]},append(...items){this.children.push(...items)}}}
const context=vm.createContext({$,document:{createElement:element},token:'test',archive:[]});
function $(id){if(!elements.has(id))elements.set(id,element());return elements.get(id)}
const code=script.slice(script.indexOf('// HISTORY_FILTERS_START'),script.indexOf("$('reset-history').onclick"));
vm.runInContext("function displayDate(v){return /^\\d{4}-\\d{2}-\\d{2}$/.test(v||'')?v.split('-').reverse().join('.'):v||''}function isoDate(v){return /^\\d{2}\\.\\d{2}\\.\\d{4}$/.test(v)?v.split('.').reverse().join('-'):v}",context);
vm.runInContext(code,context);
const rows=[{internal:'VTUER26001',number:'ORIGINAL-128',provider:'Müller',date:'2026-10-15',amount:'1.234,50',destination:'C:/verbucht/Rechnung.pdf'},{number:'RE-2',date:'2026-10-16',amount:'-12,50'},{number:'RE-3',date:'2026-10-17',amount:'0,00'},{}];context.archive=rows;
const defaults={query:'',dateFrom:'',dateTo:'',amountFrom:null,amountTo:null};
function matches(f){return rows.filter(r=>context.historyMatches(r,{...defaults,...f}))}
assert.equal(matches({query:'original-128'}).length,1);
assert.equal(matches({query:'15.10.2026'}).length,1);
assert.equal(matches({query:'1234.50'}).length,1);
assert.equal(matches({query:'rechnung.pdf'}).length,1);
assert.equal(matches({dateFrom:'2026-10-15',dateTo:'2026-10-16'}).length,2);
assert.equal(matches({amountFrom:-1250,amountTo:0}).length,2);
assert.equal(matches({query:'müller',dateFrom:'2026-10-15',dateTo:'2026-10-15',amountFrom:123450,amountTo:123450}).length,1);
assert.equal(matches({query:'RE-2',amountFrom:0}).length,0);
for(const s of ['12,50','12.50','12,50 €'])assert.equal(context.historyAmount(s),1250);
assert(Number.isNaN(context.historyAmount('abc')));
context.paintHistory();assert.equal($('history').children.length,4);
$('history-amount-from').value='foo';context.paintHistory();assert.equal($('history-filter-error').hidden,false);
context.resetHistoryFilters();assert.equal($('history-filter-error').hidden,true);assert.equal($('history-count').textContent,'4 von 4 Belegen');
$('history-date-from').value='2026-10-17';$('history-date-to').value='2026-10-15';context.paintHistory();assert.equal($('history-filter-error').hidden,false);
context.resetHistoryFilters();$('history-search').value='unauffindbar';context.paintHistory();assert.equal($('history-count').textContent,'0 von 4 Belegen');
console.log('History search: filtering, rendering, validation and reset passed.');
