import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT, SCHEMA, evaluate, toCSV } from '../docs/assets/model.mjs';

test('baseline separates original owner from unknown outcome',()=>{
 const r=evaluate(DEFAULT);
 assert.equal(r.status,'RECONCILE_ORIGINAL_RESULT');
 assert.equal(r.candidateOwner,'Gateway A');
 assert.equal(r.newRoundDefault,'Gateway B');
 assert.deepEqual(r.gaps,['RESULT_UNRESOLVED']);
 assert.equal(r.walletEffectAuthorized,false);
});
test('authenticity gates ownership and records other gaps',()=>{
 const r=evaluate({...DEFAULT,authenticity:'unverified',mapping:'missing',reviewer:'unassigned'});
 assert.equal(r.status,'HOLD_AUTHENTICITY');
 assert.equal(r.candidateOwner,null);
 assert.deepEqual(r.gaps,['AUTHENTICITY_UNVERIFIED','MAPPING_MISSING','RESULT_UNRESOLVED','REVIEWER_UNASSIGNED']);
});
test('all invalid mapping states hold even with a recorded result',()=>{
 for(const mapping of SCHEMA.mapping.filter(x=>x!=='matched')){
  const r=evaluate({...DEFAULT,mapping,result:'recorded'});
  assert.equal(r.status,'HOLD_MAPPING');assert.equal(r.candidateOwner,null);
 }
});
test('changed payload never resolves through prior recorded result',()=>{
 assert.equal(evaluate({...DEFAULT,payload:'changed',result:'recorded'}).status,'HOLD_PAYLOAD');
});
test('original handler outage never uses new default',()=>{
 const r=evaluate({...DEFAULT,originalHandler:'unavailable'});
 assert.equal(r.status,'HOLD_ORIGINAL_HANDLER');assert.equal(r.candidateOwner,'Gateway A');
 assert.match(r.nextAction,/Restore access/);
});
test('recorded result remains review-only without wallet authority',()=>{
 const r=evaluate({...DEFAULT,result:'recorded'});
 assert.equal(r.status,'REVIEW_RECORDED_RESULT');assert.equal(r.walletEffectAuthorized,false);
});
test('unassigned reviewer remains visible alongside primary decision',()=>{
 const r=evaluate({...DEFAULT,reviewer:'unassigned'});
 assert.equal(r.reviewer,'UNASSIGNED');assert.ok(r.gaps.includes('REVIEWER_UNASSIGNED'));
});
test('strict schema rejects malformed input',()=>{
 for(const x of [null,[],{}, {...DEFAULT,extra:true},{...DEFAULT,mapping:'yes'},{...DEFAULT,reviewer:true}]) assert.throws(()=>evaluate(x),TypeError);
});
test('does not mutate inputs or share report state',()=>{
 const x=Object.freeze({...DEFAULT}); const a=evaluate(x); a.input.mapping='missing';
 assert.equal(x.mapping,'matched');assert.equal(evaluate(x).input.mapping,'matched');
});
test('all 160 combinations are synthetic and cannot authorize any effect',()=>{
 let n=0; const keys=Object.keys(SCHEMA);
 function walk(x,i){if(i===keys.length){const r=evaluate(x);n++;assert.equal(r.synthetic,true);assert.equal(r.liveChecks,0);assert.equal(r.walletEffectAuthorized,false);assert.notEqual(r.candidateOwner,'Gateway B');return;}
 for(const v of SCHEMA[keys[i]])walk({...x,[keys[i]]:v},i+1);}
 walk({},0);assert.equal(n,160);
});
test('exports are deterministic and preserve report evidence',()=>{
 const a=evaluate(DEFAULT),b=evaluate({...DEFAULT});assert.equal(JSON.stringify(a),JSON.stringify(b));
 const csv=toCSV(a);assert.ok(csv.includes('"walletEffectAuthorized","false"'));assert.ok(csv.includes('"mappingReference","mapping-v7"'));
 assert.equal(csv,toCSV(b));assert.ok(csv.endsWith('\r\n'));
});
