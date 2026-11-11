import {DEFAULT,evaluate,toCSV} from './model.mjs';
const form=document.querySelector('#scenario'),json=document.querySelector('#json-report');
let report;const blobURLs=[];
function render(){
 const values=Object.fromEntries(new FormData(form)); report=evaluate(values);
 document.querySelector('#status').textContent=report.status.replaceAll('_',' ');
 document.querySelector('#owner').textContent=report.candidateOwner??'Not established';
 document.querySelector('#wallet-result').textContent=report.walletResult.replaceAll('_',' ');
 document.querySelector('#reviewer-result').textContent=report.reviewer;
 document.querySelector('#action').textContent=report.nextAction;
 const list=document.querySelector('#gaps');list.replaceChildren();
 for(const gap of report.gaps.length?report.gaps:['No unresolved model gaps. Contract review still required.']){const li=document.createElement('li');li.textContent=gap.replaceAll('_',' ');list.append(li);}
 json.textContent=JSON.stringify(report,null,2);
 for(const url of blobURLs.splice(0))URL.revokeObjectURL(url);
 for(const[id,body,type]of [['download-json',json.textContent+'\n','application/json'],['download-csv',toCSV(report),'text/csv']]){const url=URL.createObjectURL(new Blob([body],{type}));blobURLs.push(url);document.querySelector('#'+id).href=url;}
}
const presets={baseline:DEFAULT,missing:{...DEFAULT,mapping:'missing'},outage:{...DEFAULT,originalHandler:'unavailable'},recorded:{...DEFAULT,result:'recorded'},conflict:{...DEFAULT,mapping:'wrong-operator',payload:'changed',reviewer:'unassigned'}};
function load(values){for(const[k,v]of Object.entries(values))form.elements.namedItem(k).value=v;render();}
form.addEventListener('change',render);form.addEventListener('submit',e=>e.preventDefault());
document.querySelector('#preset').addEventListener('change',e=>load(presets[e.target.value]));
document.querySelector('#reset').addEventListener('click',()=>{document.querySelector('#preset').value='baseline';load(DEFAULT);});
render();
