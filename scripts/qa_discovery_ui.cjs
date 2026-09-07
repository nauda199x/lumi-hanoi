// Exercise actual asynchronous controller behavior with controlled network timing.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
class Node {
  constructor(tag='div'){
    this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.listeners={};
    this.hidden=false;this.value='';this.className='';this._text='';
    this.classList={add:c=>this.classList.toggle(c,true),remove:c=>this.classList.toggle(c,false),toggle:(c,on)=>{
      const values=new Set(this.className.split(' ').filter(Boolean));
      if(on??!values.has(c))values.add(c);else values.delete(c);this.className=[...values].join(' ');
    }};
  }
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(n=>n?.textContent||'').join('');}
  set innerHTML(value){this.children=[new Node('svg')];}
  get firstElementChild(){return this.children[0];}
  get childElementCount(){return this.children.length;}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;this._text='';}
  setAttribute(key,value){this.attributes[key]=String(value);}
  getAttribute(key){return this.attributes[key]??null;}
  hasAttribute(key){return key in this.attributes;}
  removeAttribute(key){delete this.attributes[key];}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
  async emit(type,event={}){for(const fn of this.listeners[type]||[])await fn({target:this,preventDefault(){},...event});}
  all(){return this.children.flatMap(child=>child instanceof Node?[child,...child.all()]:[]);}
  querySelectorAll(selector){return this.all().filter(n=>selector.startsWith('.')?n.className.split(' ').includes(selector.slice(1)):n.hasAttribute(selector.slice(1,-1)));}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  focus(){}
  scrollIntoView(){}
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const row=(id,title=id)=>({id,title,slug:id,listing_type:'rent',unit_type:'2PN',phase:'Signature',tower:'S3',price_vnd:10000000,area_sqm:54,listing_images:[]});
function fixture({staticCards=true}={}){
  const nodes=new Map(),timers=new Map(),requests=[];let timerId=0;
  const get=selector=>{if(!nodes.has(selector))nodes.set(selector,new Node());return nodes.get(selector);};
  const root=new Node();root.dataset={listingType:'rent',inventoryStaticPages:'1'};root.querySelector=get;
  const form=get('[data-listing-filters]');
  const keys=['keyword','phase','tower','bedroom','max_price','area','sort'];
  form.elements=Object.fromEntries(keys.map(name=>[name,Object.assign(new Node('input'),{name,value:name==='sort'?'newest':''})]));
  nodes.set('[name=sort]',form.elements.sort);
  const grid=get('[data-listing-grid]');
  const staticRow=new Node('article');staticRow.className='inventory-row';staticRow.setAttribute('data-static-listing-card','');
  if(staticCards)grid.append(staticRow);
  const state=get('[data-listing-state]');state.hidden=true;state.querySelector=get;
  const location={href:'https://lumi-hanoi.com/cho-thue-lumi-hanoi/',origin:'https://lumi-hanoi.com',pathname:'/cho-thue-lumi-hanoi/',search:'',hash:''};
  const history={pushState(a,b,url){const u=new URL(url,location.href);Object.assign(location,{href:u.href,pathname:u.pathname,search:u.search});}};history.replaceState=history.pushState;
  const api={listPublicPage:(type,filters,page,options)=>new Promise((resolve,reject)=>requests.push({type,filters,page,options,resolve,reject})),listingUrl:r=>'/cho-thue-lumi-hanoi/'+r.id+'/',formatCurrency:()=> '10 triệu/tháng',imageUrl:p=>p};
  const window={LumiMarketplace:api,addEventListener(){}};
  const document={title:'Cho thuê Lumi Hanoi',querySelector:s=>s==='[data-inventory]'?root:null,createElement:tag=>new Node(tag),createTextNode:text=>({textContent:text})};
  const context={window,document,location,history,URL,URLSearchParams,AbortController,console,
    FormData:class{constructor(f){this.f=f;}[Symbol.iterator](){return Object.entries(this.f.elements).map(([k,n])=>[k,n.value])[Symbol.iterator]();}},
    Option:class extends Node{constructor(text,value){super('option');this.textContent=text;this.value=value;}},
    setTimeout:(fn,delay)=>{const id=++timerId;timers.set(id,{fn,delay});return id;},clearTimeout:id=>timers.delete(id)};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../assets/js/marketplace-inventory.js'),'utf8'),context);
  const flush=async delay=>{for(const [id,t] of [...timers])if(t.delay===delay){timers.delete(id);t.fn();}await tick();};
  return {root,grid,form,get,requests,staticRow,flush};
}
test('filters retain layout, block stale card actions, and ignore an out-of-order response',async()=>{
  const f=fixture();
  assert.equal(f.grid.children[0],f.staticRow);
  assert.equal(f.grid.inert,true);
  let blocked=false;await f.grid.emit('click',{preventDefault(){blocked=true;}});assert.ok(blocked);
  f.form.elements.bedroom.value='3PN';await f.form.emit('change',{target:f.form.elements.bedroom});await f.flush(0);
  assert.equal(f.requests.length,2);assert.equal(f.requests[0].options.signal.aborted,true);
  f.requests[0].resolve({total:1,rows:[row('old')]});await tick();
  assert.equal(f.grid.children[0],f.staticRow);assert.equal(f.grid.inert,true);
  f.requests[1].resolve({total:1,rows:[row('new','Căn ba phòng ngủ')]});await tick();
  assert.match(f.grid.textContent,/Căn ba phòng ngủ/);assert.doesNotMatch(f.grid.textContent,/old/);
  assert.equal(f.grid.inert,false);assert.equal(f.root.getAttribute('aria-busy'),'false');
});
test('real initial wait has card skeletons; error and retry restore usable results',async()=>{
  const f=fixture({staticCards:false});
  assert.equal(f.grid.children.length,3);
  assert.ok(f.grid.children.every(n=>n.className.includes('inventory-skeleton-row')&&n.getAttribute('aria-hidden')==='true'));
  f.requests[0].reject(new Error('Offline'));await tick();
  assert.equal(f.grid.children.length,0);assert.equal(f.grid.inert,false);
  assert.equal(f.get('[data-listing-state]').hidden,false);assert.equal(f.get('[data-inventory-retry]').hidden,false);
  const retry=f.get('[data-inventory-retry]').emit('click');await tick();
  f.requests[1].resolve({total:1,rows:[row('available')]});await retry;await tick();
  assert.equal(f.get('[data-listing-state]').hidden,true);assert.equal(f.grid.children.length,1);
  assert.equal(f.grid.inert,false);assert.equal(f.get('[data-inventory-pagination]').inert,false);
});
test('rapid keyword input sends only the final request and keeps cards during debounce',async()=>{
  const f=fixture();f.requests[0].resolve({total:1,rows:[row('current')]});await tick();
  const previous=f.grid.children[0];
  for(const keyword of ['S','S3','S3 2PN']){f.form.elements.keyword.value=keyword;await f.form.emit('input',{target:f.form.elements.keyword});}
  assert.equal(f.grid.children[0],previous);assert.equal(f.grid.inert,true);
  await f.flush(320);assert.equal(f.requests.length,2);assert.equal(f.requests[1].filters.keyword,'S3 2PN');
  f.requests[1].resolve({total:0,rows:[]});await tick();
  assert.equal(f.grid.inert,false);assert.match(f.get('[data-state-title]').textContent,/Không tìm thấy/);
});

function navigationFixture(connection={},readyState='complete'){
  const document=new Node(),window=new Node(),head=new Node();document.head=head;document.readyState=readyState;document.visibilityState='visible';
  document.createElement=tag=>Object.assign(new Node(tag),{relList:{supports:()=>true}});
  const timers=new Map();let id=0;
  const context={document,window,navigator:{connection},location:{origin:'https://lumi-hanoi.com',href:'https://lumi-hanoi.com/',pathname:'/'},URL,
    setTimeout:(fn,delay)=>{timers.set(++id,{fn,delay});return id;},clearTimeout:id=>timers.delete(id)};
  const source=fs.readFileSync(path.join(__dirname,'../assets/js/site.js'),'utf8');
  vm.runInNewContext(source.slice(source.indexOf('/* Small, intent-based navigation hints')),context);
  const link=href=>{const n=new Node('a');n.href=new URL(href,context.location.href).href;n.closest=s=>s==='a[href]'?n:s==='.inventory-tabs'?{}:null;n.contains=other=>other===n;return n;};
  return {document,window,head,link};
}
test('prefetch waits for load, respects slow/data-saving connections and limits documents',async()=>{
  for(const connection of [{saveData:true},{effectiveType:'3g'}]){
    const f=navigationFixture(connection);await f.document.emit('focusin',{target:f.link('/mat-bang-lumi-hanoi/')});assert.equal(f.head.children.length,0);
  }
  const f=navigationFixture({},'loading');await f.document.emit('focusin',{target:f.link('/mat-bang-lumi-hanoi/')});assert.equal(f.head.children.length,0);
  await f.window.emit('load');
  for(const href of ['/admin/','/dang-tin-lumi-hanoi/','/mua-ban-lumi-hanoi/?bedroom=2PN','https://example.com/mat-bang-lumi-hanoi/'])await f.document.emit('focusin',{target:f.link(href)});
  assert.equal(f.head.children.length,0);
  for(const href of ['/mat-bang-lumi-hanoi/','/mat-bang-lumi-hanoi/','/gia-can-ho-lumi-hanoi/','/mua-ban-lumi-hanoi/','/cho-thue-lumi-hanoi/'])await f.document.emit('focusin',{target:f.link(href)});
  assert.equal(f.head.children.length,3);assert.ok(f.head.children.every(n=>n.rel==='prefetch'&&n.as==='document'));
});
test('tab navigation stays native and clears loading when returning with browser Back',async()=>{
  const f=navigationFixture(),link=f.link('/cho-thue-lumi-hanoi/');
  await f.document.emit('click',{target:link,ctrlKey:true});assert.equal(link.hasAttribute('aria-busy'),false);
  let prevented=false;await f.document.emit('click',{target:link,preventDefault(){prevented=true;}});
  assert.equal(prevented,false);assert.equal(link.getAttribute('aria-busy'),'true');
  await f.window.emit('pageshow');assert.equal(link.hasAttribute('aria-busy'),false);assert.equal(link.hasAttribute('data-navigation-pending'),false);
});
