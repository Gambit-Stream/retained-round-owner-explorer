"use strict";
const fields = ["company","boundary","adapter_revision","provider_recipient","wallet_owner","exception_receiver","acceptance_owner","evidence_reference"];
function record(){return Object.fromEntries(fields.map(id=>[id,document.getElementById(id).value.trim()]));}
function update(){const r=record();const gaps=fields.filter(k=>!r[k]);document.getElementById("status").textContent=`${fields.length-gaps.length}/${fields.length} fields completed. ${gaps.length ? "Missing: "+gaps.map(k=>document.getElementById(k).closest("label").childNodes[0].textContent.trim()).join("; ")+"." : "All fields contain text; evidence review remains required."}`;}
fields.forEach(id=>document.getElementById(id).addEventListener("input",update));
document.getElementById("reset").addEventListener("click",()=>{fields.forEach(id=>document.getElementById(id).value="");update();});
document.getElementById("export").addEventListener("click",()=>{const payload={resource:"provider-boundary-review",version:"1.0.0",status:"USER_ENTERED_UNVERIFIED",record:record()};const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)+"\n"],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download="provider-boundary-review.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
update();
