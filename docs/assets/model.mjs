export const RULE_VERSION='2026-11-11.1';
export const SCHEMA=Object.freeze({authenticity:['verified','unverified'],mapping:['matched','missing','conflict','wrong-operator','expired'],originalHandler:['available','unavailable'],result:['unresolved','recorded'],payload:['same','changed'],reviewer:['assigned','unassigned']});
export const DEFAULT=Object.freeze({authenticity:'verified',mapping:'matched',originalHandler:'available',result:'unresolved',payload:'same',reviewer:'assigned'});
export function evaluate(input){
 if(!input||typeof input!=='object'||Array.isArray(input)||Object.keys(input).length!==Object.keys(SCHEMA).length||Object.entries(SCHEMA).some(([k,vs])=>!Object.hasOwn(input,k)||!vs.includes(input[k])))throw new TypeError('Use exactly the six documented scenario selections.');
 const gaps=[];
 if(input.authenticity!=='verified')gaps.push('AUTHENTICITY_UNVERIFIED');
 if(input.mapping!=='matched')gaps.push(`MAPPING_${input.mapping.toUpperCase().replaceAll('-','_')}`);
 if(input.payload==='changed')gaps.push('PAYLOAD_CHANGED');
 if(input.originalHandler==='unavailable')gaps.push('ORIGINAL_HANDLER_UNAVAILABLE');
 if(input.result==='unresolved')gaps.push('RESULT_UNRESOLVED');
 if(input.reviewer==='unassigned')gaps.push('REVIEWER_UNASSIGNED');
 let status,nextAction;
 if(input.authenticity==='unverified'){
  status='HOLD_AUTHENTICITY';nextAction='Establish callback authenticity under the provider contract before trusting an ownership lookup.';
 }else if(input.mapping!=='matched'){
  status='HOLD_MAPPING';nextAction='Locate a retained mapping for the exact operator, provider and round. Resolve its scope, validity and conflicting versions before selecting an owner.';
 }else if(input.payload==='changed'){
  status='HOLD_PAYLOAD';nextAction='Compare the original event intent and retained payload reference. Escalate the mismatch before treating this as a duplicate.';
 }else if(input.originalHandler==='unavailable'){
  status='HOLD_ORIGINAL_HANDLER';nextAction='Restore access to the original handler or obtain an explicitly reviewed recovery path. Preserve its mapping and unresolved evidence.';
 }else if(input.result==='recorded'){
  status='REVIEW_RECORDED_RESULT';nextAction='Review the assumed recorded result against the original event and response contract. No wallet operation is authorized by this report.';
 }else{
  status='RECONCILE_ORIGINAL_RESULT';nextAction='Reconcile the original event reference with the retained handler and ledger evidence. Keep the wallet result unresolved until supported.';
 }
 return {schemaVersion:1,ruleVersion:RULE_VERSION,synthetic:true,input:{...input},operator:'OP-41',provider:'P-41',round:'R-41',event:'E-41',originalHandler:'Gateway A',newRoundDefault:'Gateway B',mappingReference:'mapping-v7',receiptReference:'receipt-41',candidateOwner:input.authenticity==='verified'&&input.mapping==='matched'?'Gateway A':null,walletResult:input.result==='recorded'?'RECORDED_ASSUMPTION':'UNRESOLVED',reviewer:input.reviewer==='assigned'?'Demo integration reviewer':'UNASSIGNED',status,nextAction,gaps,walletEffectAuthorized:false,liveChecks:0};
}
export function toCSV(report){
 const quote=x=>'"'+String(x).replaceAll('"','""')+'"';
 return [['field','value'],...Object.entries(report).map(([k,v])=>[k,typeof v==='object'?JSON.stringify(v):v===null?'null':String(v)])].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
}
