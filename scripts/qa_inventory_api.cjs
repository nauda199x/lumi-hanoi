const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

function client(response={status:206,total:56,rows:[]}){
  let last;
  const sandbox={window:{LUMI_MARKETPLACE_CONFIG:{supabaseUrl:'https://example.supabase.co',supabasePublishableKey:'public-test-key'}},URLSearchParams,Blob,ArrayBuffer,
    fetch:async(url,options)=>{last={url:new URL(url),options};return {status:response.status,ok:response.status<400,headers:{get:()=>`*/${response.total}`},text:async()=>JSON.stringify(response.rows)};}};
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../assets/js/marketplace-api.js'),'utf8'),sandbox);
  return {api:sandbox.window.LumiMarketplace,request:()=>last};
}
test('page 2 reads exactly ten records with an exact total and stable order',async()=>{
  const c=client();const result=await c.api.listPublicPage('sale',{},2);const r=c.request();
  assert.equal(result.total,56);assert.equal(r.url.searchParams.get('limit'),'10');assert.equal(r.url.searchParams.get('offset'),'10');
  assert.equal(r.options.headers.Prefer,'count=exact');assert.equal(r.url.searchParams.get('status'),'eq.approved');
  assert.equal(r.url.searchParams.get('order'),'approved_at.desc.nullslast,created_at.desc,id.desc');
  assert.ok(!r.url.searchParams.get('select').includes('description'));
});
test('all filters reach the server before pagination, including exact 4PN',async()=>{
  const c=client();await c.api.listPublicPage('sale',{phase:'Signature',tower:'S3',bedroom:'4PN',maxPrice:'7e9',area:'50-70',keyword:'căn S3',sort:'price_asc'},3);
  const p=c.request().url.searchParams;
  assert.equal(p.get('phase'),'eq.Signature');assert.equal(p.get('tower'),'eq.S3');assert.equal(p.get('unit_type'),'eq.4PN');
  assert.equal(p.get('price_vnd'),'lte.7000000000');assert.equal(p.get('and'),'(area_sqm.gte.50,area_sqm.lt.70)');
  assert.match(p.get('or'),/title\.ilike\."%căn S3%"/);assert.equal(p.get('offset'),'20');
});
test('five sort choices use deterministic database ordering; untrusted order ignored',async()=>{
  for(const [sort,first] of Object.entries({newest:'approved_at.desc',price_asc:'price_vnd.asc',price_desc:'price_vnd.desc',area_asc:'area_sqm.asc',area_desc:'area_sqm.desc',injection:'approved_at.desc'})){
    const c=client();await c.api.listPublicPage('sale',{sort});const order=c.request().url.searchParams.get('order');
    assert.ok(order.startsWith(first));assert.ok(order.endsWith('id.desc'));
  }
});
test('keyword grammar and wildcards are quoted, never new filters',async()=>{
  const c=client();await c.api.listPublicPage('sale',{keyword:'x"),status.eq.pending%_*\\'});
  const p=c.request().url.searchParams;assert.equal(p.get('status'),'eq.approved');
  assert.match(p.get('or'),/\\"\),status\.eq\.pending/);assert.match(p.get('or'),/\\\\%/);
});
test('out of range response retains total so a deleted last page can recover',async()=>{
  const c=client({status:416,total:5,rows:{code:'PGRST103'}});const r=await c.api.listPublicPage('sale',{},99);
  assert.equal(r.total,5);assert.equal(r.rows.length,0);
});
test('abort signal is forwarded and legacy rental ranking remains unchanged',async()=>{
  const c=client({status:200,total:0,rows:[]});const signal=new AbortController().signal;
  await c.api.listPublicPage('sale',{},1,{signal});assert.equal(c.request().options.signal,signal);
  await c.api.listPublic('rent',{}, {signal});const p=c.request().url.searchParams;
  assert.equal(p.get('listing_type'),'eq.rent');assert.equal(p.get('order'),'is_featured.desc,sort_priority.desc,approved_at.desc');
  assert.equal(c.request().options.signal,signal);
});
