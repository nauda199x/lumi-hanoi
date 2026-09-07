const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../assets/js/marketplace-api.js'),'utf8');
const sessionKey='lumi_marketplace_admin_session';
function fixture({session=true,admin=true,handler}={}){
  const calls=[],memory=new Map();
  if(session)memory.set(sessionKey,JSON.stringify({access_token:'test-admin-token',refresh_token:'test-refresh',expires_at:Math.floor(Date.now()/1000)+3600,user:{id:'admin-id'}}));
  const sandbox={window:{LUMI_MARKETPLACE_CONFIG:{supabaseUrl:'https://test.invalid',supabasePublishableKey:'test-public-key',listingLifetimeDays:45}},sessionStorage:{getItem:key=>memory.get(key),setItem:(key,value)=>memory.set(key,value),removeItem:key=>memory.delete(key)},URLSearchParams,Blob,ArrayBuffer,AbortController,console,
    fetch:async(url,options)=>{
      const call={url:new URL(url),options};calls.push(call);
      let response;
      if(call.url.pathname.endsWith('/admin_users'))response={rows:admin?[{user_id:'admin-id'}]:[]};
      else response=await handler?.(call)||{rows:[]};
      const status=response.status||200;
      return {status,ok:status<400,headers:{get:()=>response.total===undefined?null:`*/${response.total}`},text:async()=>options.method==='HEAD'?'':JSON.stringify(response.rows)};
    }};
  vm.createContext(sandbox);vm.runInContext(source,sandbox);
  return {api:sandbox.window.LumiMarketplace,calls,memory};
}
function listingRequests(f){return f.calls.filter(call=>call.url.pathname.endsWith('/listings'));}
test('625 records remain reachable past the old 300 limit, with bounded pages and no duplicates',async()=>{
  const all=Array.from({length:625},(_,i)=>({id:String(i+1)}));
  const f=fixture({handler:({url})=>{const p=url.searchParams;return {total:all.length,rows:all.slice(Number(p.get('offset')),Number(p.get('offset'))+Number(p.get('limit')))};}});
  const ids=[];
  for(let page=1;page<=32;page++){const result=await f.api.listAdminPage({},page);assert.equal(result.total,625);assert.ok(result.rows.length<=20);ids.push(...result.rows.map(row=>row.id));}
  assert.equal(ids.length,625);assert.equal(new Set(ids).size,625);assert.equal(ids.at(-1),'625');
  const last=listingRequests(f).at(-1);assert.equal(last.url.searchParams.get('offset'),'620');assert.equal(last.options.headers.Prefer,'count=exact');assert.equal(last.options.headers.Authorization,'Bearer test-admin-token');
  assert.equal(last.url.searchParams.get('listing_images.limit'),'1');assert.equal(last.url.searchParams.get('open_reports.limit'),'1');assert.ok(!last.url.searchParams.get('select').includes('description'));
});
test('20/50/100 size choices, exact 4PN and combined filters all reach the database',async()=>{
  const f=fixture({handler:()=>({rows:[],total:0})});
  await f.api.listAdminPage({status:'approved',type:'rent',phase:'Signature',tower:'S3',unit_type:'4PN',featured:'yes',sort:'oldest',keyword:'LH-ABCD'},4,{pageSize:50});
  const p=listingRequests(f).at(-1).url.searchParams;
  assert.equal(p.get('limit'),'50');assert.equal(p.get('offset'),'150');assert.equal(p.get('listing_type'),'eq.rent');assert.equal(p.get('phase'),'eq.Signature');assert.equal(p.get('tower'),'eq.S3');assert.equal(p.get('unit_type'),'eq.4PN');assert.equal(p.get('is_featured'),'eq.true');assert.equal(p.get('order'),'created_at.asc,id.asc');
  assert.match(p.get('and'),/status.eq.approved/);assert.match(p.get('and'),/expires_at.is.null,expires_at.gt./);assert.match(p.get('and'),/listing_code.ilike/);
  for(const [size,expected] of [[100,100],[99999,20]]){await f.api.listAdminPage({},1,{pageSize:size});assert.equal(listingRequests(f).at(-1).url.searchParams.get('limit'),String(expected));}
});
test('expiry and unresolved-report queues use matching effective state semantics',async()=>{
  const f=fixture({handler:()=>({rows:[],total:0})});
  await f.api.listAdminPage({status:'expired'});assert.match(listingRequests(f).at(-1).url.searchParams.get('and'),/or\(status.eq.expired,and\(status.eq.approved,expires_at.lte./);
  await f.api.listAdminPage({status:'expiring'});const clause=listingRequests(f).at(-1).url.searchParams.get('and');assert.match(clause,/expires_at.gt./);assert.match(clause,/expires_at.lte./);
  await f.api.listAdminPage({status:'reported'});const p=listingRequests(f).at(-1).url.searchParams;assert.equal(p.get('open_reports'),'not.is.null');assert.equal(p.get('open_reports.resolved_at'),'is.null');
});
test('global counters use HEAD requests, including total beyond 300, and no content download',async()=>{
  const f=fixture({handler:()=>({total:625})});const counts=await f.api.adminCounts();assert.equal(counts.all,625);
  const calls=listingRequests(f);assert.equal(calls.length,5);for(const call of calls){assert.equal(call.options.method,'HEAD');assert.equal(call.options.headers.Prefer,'count=exact');assert.equal(call.url.searchParams.get('limit'),'1');}
});
test('search punctuation and wildcard input stay quoted; formatted phones also get normalized',async()=>{
  const f=fixture({handler:()=>({total:0,rows:[]})});
  await f.api.listAdminPage({keyword:'x"),status.eq.approved%_*\\'});const p=listingRequests(f).at(-1).url.searchParams;assert.match(p.get('and'),/\\"\),status.eq.approved/);assert.match(p.get('and'),/\\\\%/);assert.equal(p.has('status'),false);
  await f.api.listAdminPage({keyword:'090 123 4567'});assert.match(listingRequests(f).at(-1).url.searchParams.get('and'),/contact_phone.ilike."%0901234567%"/);
});
test('unauthenticated and non-admin sessions cannot read or mutate inventory',async()=>{
  for(const options of [{session:false},{admin:false}]){
    const f=fixture(options);
    await assert.rejects(()=>f.api.listAdminPage(),{status:401});
    await assert.rejects(()=>f.api.adminCounts(),{status:401});
    await assert.rejects(()=>f.api.updateListing('x',{status:'approved'}),{status:401});
    await assert.rejects(()=>f.api.applyAdminAction([{id:'x'}],'hide'),{status:401});
    assert.equal(listingRequests(f).length,0);
  }
});
test('concurrent edit conflicts are errors, never silent successful saves',async()=>{
  const f=fixture({handler:()=>({rows:[]})});
  await assert.rejects(()=>f.api.updateListing('x',{title:'Changed'},'2026-09-01T10:00:00Z'),{status:409});
  const call=listingRequests(f)[0];assert.equal(call.url.searchParams.get('updated_at'),'eq.2026-09-01T10:00:00Z');assert.equal(call.options.headers.Prefer,'return=representation');
});
test('bulk operations report partial failure, cap concurrent writes at 3 and use each transaction type',async()=>{
  let inFlight=0,maximum=0;
  const f=fixture({handler:async({url})=>{inFlight++;maximum=Math.max(maximum,inFlight);await new Promise(resolve=>setTimeout(resolve,2));inFlight--;const id=url.searchParams.get('id').slice(3);return {rows:id==='conflict'?[]:[{id}]};}});
  const items=Array.from({length:9},(_,i)=>({id:i===4?'conflict':String(i),listing_code:`LH-${i}`,listing_type:i%2?'rent':'sale',updated_at:'2026-09-01T00:00:00Z'}));
  const progress=[];const result=await f.api.applyAdminAction(items,'done',{onProgress:p=>progress.push(p.done)});
  assert.equal(result.success.length,8);assert.equal(result.failed.length,1);assert.equal(result.failed[0].code,'LH-4');assert.ok(maximum<=3);assert.equal(progress.at(-1),9);
  for(const call of listingRequests(f)){const id=call.url.searchParams.get('id').slice(3);const body=JSON.parse(call.options.body);assert.equal(body.status,id!=='conflict'&&Number(id)%2?'rented':'sold');assert.equal(body.is_featured,false);assert.ok(call.url.searchParams.get('updated_at'));}
});
test('approval preserves original published date and enforces contact consent',async()=>{
  const f=fixture({handler:()=>({rows:[{id:'ok'}]})});
  const rows=[{id:'ok',contact_public:true,updated_at:'2026-09-01',approved_at:'2026-08-20T00:00:00Z'},{id:'no-consent',contact_public:false,updated_at:'2026-09-01'}];
  const result=await f.api.applyAdminAction(rows,'approve');assert.equal(result.success.length,1);assert.equal(result.failed.length,1);
  const patch=JSON.parse(listingRequests(f)[0].options.body);assert.equal(patch.approved_at,rows[0].approved_at);assert.ok(new Date(patch.expires_at)>new Date());assert.equal(patch.status,'approved');
  await assert.rejects(()=>f.api.applyAdminAction(Array(101).fill(rows[0]),'approve'),{status:400});
  await assert.rejects(()=>f.api.applyAdminAction(rows,'delete'),{status:400});
});
test('only reports reviewed for this listing are marked resolved; fresh reports remain untouched',async()=>{
  const f=fixture({handler:()=>({rows:[{id:1},{id:2}]})});
  const count=await f.api.resolveAdminReports('listing-a',[1,2,'bad-id']);assert.equal(count,2);
  const call=f.calls.find(c=>c.url.pathname.endsWith('/listing_reports'));const p=call.url.searchParams;
  assert.equal(p.get('listing_id'),'eq.listing-a');assert.equal(p.get('id'),'in.(1,2)');assert.equal(p.get('resolved_at'),'is.null');assert.equal(JSON.parse(call.options.body).resolved_by,'admin-id');
});
test('last-page deletion preserves exact total and canceled request signals reach fetch',async()=>{
  const f=fixture({handler:()=>({status:416,total:300,rows:{code:'PGRST103'}})});const signal=new AbortController().signal;
  const result=await f.api.listAdminPage({},32,{signal});assert.equal(result.total,300);assert.equal(result.rows.length,0);assert.equal(listingRequests(f)[0].options.signal,signal);
});
test('parallel admin loads share a single token refresh',async()=>{
  let refreshes=0;
  const f=fixture({handler:async({url})=>{if(url.pathname==='/auth/v1/token'){refreshes++;await new Promise(resolve=>setTimeout(resolve,2));return {rows:{access_token:'new-test-token',refresh_token:'new-test-refresh',expires_in:3600,user:{id:'admin-id'}}};}return {total:0,rows:[]};}});
  f.memory.set(sessionKey,JSON.stringify({access_token:'old',refresh_token:'refresh',expires_at:1,user:{id:'admin-id'}}));
  await Promise.all([f.api.listAdminPage(),f.api.adminCounts()]);assert.equal(refreshes,1);assert.ok(JSON.parse(f.memory.get(sessionKey)).expires_at>Date.now()/1000);
});
