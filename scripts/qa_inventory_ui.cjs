// Controller regression tests: controlled DOM/network, no live data or writes.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(process.env.INVENTORY_SCRIPT||path.join(__dirname,'../assets/js/marketplace-inventory.js'),'utf8');

class Node {
  constructor(tag='div',text=''){
    this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.listeners={};
    this.hidden=false;this.disabled=false;this.inert=false;this.value='';this.className='';this._text=text;
    this.classList={add:name=>{this.className+=' '+name;},toggle:()=>{},remove:()=>{}};
  }
  get childNodes(){return this.children;}
  get childElementCount(){return this.children.length;}
  get firstElementChild(){return this.children[0]||null;}
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(n=>n.textContent||'').join('');}
  set innerHTML(value){this.children=value?[new Node('svg')]:[];this._text='';}
  append(...nodes){for(const n of nodes){n.parent=this;this.children.push(n);}}
  replaceChildren(...nodes){this.children=[];this.append(...nodes);this._text='';}
  set src(value){this.attributes.src=value;}
  get src(){return this.attributes.src;}
  remove(){this.removed=true;if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);}
  setAttribute(name,value){this.attributes[name]=String(value);}
  getAttribute(name){return this.attributes[name]??null;}
  addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
  emit(name,event={}){for(const fn of this.listeners[name]||[])void fn({target:this,preventDefault(){},...event});}
  all(){return this.children.flatMap(n=>[n,...n.all()]);}
  querySelectorAll(selector){return this.all().filter(n=>{
    if(selector==='.inventory-row')return n.className.split(/\s+/).includes('inventory-row');
    if(selector==='.inventory-row:not(.inventory-skeleton-row)')return n.className.split(/\s+/).includes('inventory-row')&&!n.className.includes('inventory-skeleton-row');
    if(selector==='img[data-inventory-original]')return n.tagName==='img'&&Boolean(n.dataset.inventoryOriginal);
    return false;
  });}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  focus(){}
  scrollIntoView(){}
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const listing=(id='live')=>({id,slug:id,listing_type:'sale',title:'Căn '+id,phase:'Signature',tower:'S1',unit_type:'2PN',area_sqm:55,price_vnd:4e9,listing_images:[]});
function fixture({url='https://lumi-hanoi.com/mua-ban-lumi-hanoi/',defaults={},seed=true,thumbnails={},seedImage=null}={}){
  const location=new URL(url),requests=[],timers=new Map(),nodes=new Map();let timerId=0;
  const get=selector=>{if(!nodes.has(selector))nodes.set(selector,new Node());return nodes.get(selector);};
  const root=new Node();root.dataset={listingType:location.pathname.startsWith('/cho-thue-')?'rent':'sale',inventoryBase:location.pathname.replace(/page\/\d+\/$/,''),inventoryStaticPages:'3',...defaults};
  root.querySelector=get;
  const form=get('[data-listing-filters]');
  const keys=['keyword','phase','tower','bedroom','min_price','max_price','area','furnishing','sort'];
  form.elements=Object.fromEntries(keys.map(name=>[name,Object.assign(new Node('input'),{name})]));
  nodes.set('[name=sort]',form.elements.sort);
  const grid=get('[data-listing-grid]'),pager=get('[data-inventory-pagination]'),summary=get('[data-inventory-summary]'),count=get('[data-listing-count]'),state=get('[data-listing-state]');
  state.querySelector=get;state.hidden=true;pager.hidden=false;
  const seedNode=new Node('article','Static listing');seedNode.className='inventory-row';seedNode.href='/mua-ban-lumi-hanoi/static/';
  if(seedImage){const img=Object.assign(new Node('img'),seedImage);img.dataset.inventoryOriginal=seedImage.original;seedNode.append(img);}
  if(seed)grid.append(seedNode);
  summary.textContent=seed?'Hiển thị 1–3 trong 23 căn':'';count.textContent=seed?'23 tin đăng':'';
  const nextLink=new Node('a','Tiếp');nextLink.dataset.page='2';nextLink.href=root.dataset.inventoryBase+'page/2/';pager.append(nextLink);
  const schema=new Node('script');schema.textContent='{"@type":"ItemList"}';
  const document={title:'Mua bán Smart City',querySelector:s=>s==='[data-inventory]'?root:s==='[data-inventory-schema]'?schema:s==='[data-inventory-thumbnails]'?new Node('script',JSON.stringify(thumbnails)):new Node(),createElement:tag=>new Node(tag),createTextNode:t=>new Node('#text',t)};
  const api={config:{phases:{Signature:['S1'],Elite:['E1']}},listingUrl:r=>'/mua-ban-lumi-hanoi/'+r.slug+'/',imageUrl:p=>p,formatCurrency:()=>'4 tỷ',
    listPublicPage:(type,filters,page,options)=>new Promise((resolve,reject)=>requests.push({type,filters,page,options,resolve,reject}))};
  const sandbox={document,window:{LumiMarketplace:api,addEventListener(){}},location,
    history:{replaceState:(a,b,url)=>{location.href=new URL(url,location).href;},pushState:(a,b,url)=>{location.href=new URL(url,location).href;}},
    FormData:class{constructor(f){this.form=f;}*[Symbol.iterator](){for(const [name,n]of Object.entries(this.form.elements))if(!n.disabled)yield [name,n.value];}},
    Option:function(text,value){return Object.assign(new Node('option',text),{value});},URL,URLSearchParams,AbortController,
    setTimeout:(fn,delay)=>{const id=++timerId;timers.set(id,{fn,delay});return id;},clearTimeout:id=>timers.delete(id)};
  vm.runInNewContext(source,sandbox);
  const flush=async()=>{for(const [id,t]of [...timers])if(t.delay<1000){timers.delete(id);t.fn();}await tick();};
  return {root,grid,pager,summary,count,state,seedNode,requests,get,form,location,
    rows:()=>grid.querySelectorAll('.inventory-row:not(.inventory-skeleton-row)'),
    fail:async(status=0,index=requests.length-1)=>{requests[index].reject(Object.assign(new Error('Test unavailable'),{status}));await tick();},
    succeed:async(rows=[listing()],total=rows.length,index=requests.length-1)=>{requests[index].resolve({rows,total});await tick();},
    retry:async()=>{await get('[data-inventory-retry]').emit('click');await tick();},
    change:async(name,value)=>{form.elements[name].value=value;await form.emit('change',{target:form.elements[name]});await flush();},
    next:async()=>{const a=new Node('a');a.dataset.page='2';await pager.emit('click',{target:{closest:()=>a},button:0});await tick();}
  };
}

for(const status of [0,408,429,503])test('temporary failure '+status+' preserves matching HTML with explicit stale notice',async()=>{
  const f=fixture();await f.fail(status);
  assert.equal(f.rows()[0],f.seedNode);
  assert.equal(f.grid.inert,false);assert.equal(f.root.getAttribute('aria-busy'),'false');
  assert.equal(f.state.hidden,false);assert.equal(f.get('[data-inventory-retry]').hidden,false);
  assert.match(f.get('[data-state-copy]').textContent,/dữ liệu lưu sẵn/);
  assert.match(f.summary.textContent,/Chưa xác nhận cập nhật mới/);
  assert.equal(f.count.textContent,'Dữ liệu lưu sẵn');
  assert.equal(f.pager.hidden,false);assert.equal(f.pager.children[0].href,'/mua-ban-lumi-hanoi/page/2/');
});
test('rental pages use the same fallback without changing transaction type',async()=>{
  const f=fixture({url:'https://lumi-hanoi.com/cho-thue-lumi-hanoi/'});await f.fail();
  assert.equal(f.requests[0].type,'rent');assert.equal(f.rows()[0],f.seedNode);
});
test('query and hash filters never reuse unfiltered server HTML',async()=>{
  for(const suffix of ['?bedroom=4PN','#bedroom=4PN','?phase=Signature','?tower=S1','?keyword=hello','?max_price=4000000000','?area=50-70','?sort=price_asc','?page=2']){
    const f=fixture({url:'https://lumi-hanoi.com/mua-ban-lumi-hanoi/'+suffix});await f.fail();
    assert.equal(f.rows().length,0,suffix);assert.match(f.get('[data-state-title]').textContent,/Chưa thể tải quỹ căn/);
  }
});
test('a static second page can retain only its own listing nodes',async()=>{
  const f=fixture({url:'https://lumi-hanoi.com/mua-ban-lumi-hanoi/page/2/'});await f.fail();
  assert.equal(f.requests[0].page,2);assert.equal(f.rows()[0],f.seedNode);
});
test('a tower hash never reuses unfiltered HTML',async()=>{
  const f=fixture({url:'https://lumi-hanoi.com/mua-ban-lumi-hanoi/#tower=S1'});await f.fail();
  assert.equal(f.requests[0].filters.phase,'Signature');assert.equal(f.requests[0].filters.tower,'S1');assert.equal(f.rows().length,0);
});
test('no real server rows means no skeleton fallback',async()=>{
  const f=fixture({seed:false});await f.fail();assert.equal(f.grid.children.length,0);
});
test('a later refresh failure retains live nodes, not the original HTML',async()=>{
  const f=fixture();await f.succeed([listing('fresh')],1);const current=f.rows()[0];
  assert.notEqual(current,f.seedNode);await f.retry();await f.fail();
  assert.equal(f.rows()[0],current);assert.match(f.summary.textContent,/Hiển thị 1–1 trong 1 căn/);
  assert.equal(f.pager.hidden,true);
});
test('a confirmed empty result invalidates the saved listings',async()=>{
  const f=fixture();await f.succeed([],0);await f.retry();await f.fail();assert.equal(f.rows().length,0);
});
test('changing filters cannot display old rows after a failed request',async()=>{
  const f=fixture();await f.succeed();await f.change('bedroom','4PN');await f.fail();assert.equal(f.rows().length,0);
  assert.equal(f.requests[1].filters.bedroom,'4PN');
});
test('changing sort cannot reuse an incorrectly ordered snapshot',async()=>{
  const f=fixture();await f.succeed();await f.change('sort','price_asc');await f.fail();assert.equal(f.rows().length,0);
});
test('paging failure does not show page one under a page two URL',async()=>{
  const f=fixture();await f.succeed([listing()],23);await f.next();await f.fail();
  assert.equal(f.requests[1].page,2);assert.equal(f.rows().length,0);
});
test('access and validation errors stay fail-closed and invalidate the cache',async()=>{
  for(const status of [400,401,403,404]){
    const f=fixture();await f.fail(status);assert.equal(f.rows().length,0);await f.retry();await f.fail(503);assert.equal(f.rows().length,0);
  }
});
test('a stale rejected request cannot replace newer successful results',async()=>{
  const f=fixture();await f.change('bedroom','4PN');await f.succeed([listing('new-filter')],1,1);
  const row=f.rows()[0];await f.fail(503,0);assert.equal(f.rows()[0],row);assert.equal(f.state.hidden,true);
});

const thumb='/assets/media/listing-thumbnails/'+'a'.repeat(32)+'.webp';
const withPhoto=()=>({...listing(),listing_images:[{storage_path:'cover.jpg',sort_order:0}]});
test('live cards use a known thumbnail and fall back to the original only once',async()=>{
  const f=fixture({thumbnails:{'cover.jpg':thumb}});await f.succeed([withPhoto()]);
  const img=f.rows()[0].all().find(n=>n.tagName==='img');
  assert.equal(img.src,thumb);img.emit('error');assert.equal(img.src,'cover.jpg');
  img.emit('error');assert.equal(img.removed,true);
});
test('new covers missing from the manifest load their original immediately',async()=>{
  const f=fixture();await f.succeed([withPhoto()]);
  const img=f.rows()[0].all().find(n=>n.tagName==='img');
  assert.equal(img.src,'cover.jpg');img.emit('error');assert.equal(img.removed,true);
});
test('untrusted or malformed thumbnail manifest entries are ignored',async()=>{
  for(const candidate of ['https://other.example/cover.webp','javascript:alert(1)',{url:thumb},'/assets/media/listing-thumbnails/../private.webp']){
    const f=fixture({thumbnails:{'cover.jpg':candidate}});await f.succeed([withPhoto()]);
    assert.equal(f.rows()[0].all().find(n=>n.tagName==='img').src,'cover.jpg');
  }
});
test('a static thumbnail that failed before controller startup recovers the original',async()=>{
  const f=fixture({seedImage:{src:thumb,original:'cover.jpg',complete:true,naturalWidth:0}});
  const img=f.seedNode.children[0];assert.equal(img.src,'cover.jpg');
  await f.fail();assert.equal(f.rows()[0],f.seedNode);
  img.emit('error');assert.equal(img.removed,true);
});
test('cached live nodes preserve the original-image recovery handler',async()=>{
  const f=fixture({thumbnails:{'cover.jpg':thumb}});await f.succeed([withPhoto()]);
  const img=f.rows()[0].all().find(n=>n.tagName==='img');
  await f.retry();await f.fail();img.emit('error');assert.equal(img.src,'cover.jpg');
});

