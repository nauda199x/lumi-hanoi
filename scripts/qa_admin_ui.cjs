// Exercise the admin controller with a small DOM fixture and controlled network
// timing. No real credentials, production writes or browser dependency required.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
class Node {
  constructor(tag='div'){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.listeners={};this.hidden=false;this.disabled=false;this.value='';this.open=false;this.className='';this._text='';this.classList={toggle:()=>{},add:()=>{},remove:()=>{}};}
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(child=>child.textContent||'').join('');}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;this._text='';}
  setAttribute(key,value){this.attributes[key]=String(value);}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
  async emit(type,event={}){await Promise.all((this.listeners[type]||[]).map(fn=>fn({target:this,preventDefault(){},...event})));}
  all(){return this.children.flatMap(child=>[child,...child.all()]);}
  querySelectorAll(selector){return this.all().filter(node=>selector.split(',').some(s=>s==='button'?node.tagName==='button':s==='input'?node.tagName==='input':s==='select'?node.tagName==='select':s==='textarea'?node.tagName==='textarea':s==='[data-row-id]'?!!node.dataset.rowId:s==='input[type=checkbox]'?node.type==='checkbox':false));}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  showModal(){this.open=true;}
  close(){this.open=false;void this.emit('close');}
  focus(){}
}
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const row=(id='row-a')=>({id,title:'Căn hộ Lumi Hanoi cần cho thuê',listing_code:'LH-12345678',listing_type:'rent',status:'approved',phase:'Signature',tower:'S3',unit_type:'2PN',area_sqm:54,price_vnd:10000000,poster_name:'Chủ nhà',contact_phone:'0901234567',description:'Mô tả gốc của tin',listing_images:[],open_reports:[],listing_reports:[],created_at:'2026-09-01',updated_at:'2026-09-01',expires_at:'2027-01-01'});
function fixture({savedView,failSave=false}={}){
  const nodes=new Map(),timers=new Map(),requests=[],storage=new Map();let timerId=0;
  if(savedView)storage.set('lumi_admin_view_v2',JSON.stringify(savedView));
  const get=selector=>{if(!nodes.has(selector))nodes.set(selector,new Node());return nodes.get(selector);};
  const root=new Node();root.querySelector=get;root.querySelectorAll=()=>[];
  function form(selector,names){const node=get(selector);node.elements=Object.fromEntries(names.map(name=>[name,Object.assign(new Node('input'),{name,value:''})]));node.reset=()=>Object.values(node.elements).forEach(input=>input.value='');Object.values(node.elements).forEach(input=>node.append(input));return node;}
  const filters=form('[data-admin-filters]',['keyword','status','type','phase','tower','unit_type','featured','sort']);filters.elements.sort.value='newest';
  const edit=form('[data-admin-edit-form]',['id','title','price','phase','tower','unit_type','area_sqm','floor_label','furnishing','poster_name','contact_phone','description']);edit.append(new Node('button'));
  const login=form('[data-admin-login-form]',['email','password']);login.append(new Node('button'));
  const dialog=get('[data-admin-dialog]');dialog.append(edit);
  const api={config:{listingLifetimeDays:45},configured:()=>true,requireAdmin:async()=>({user:{id:'admin'}}),adminCounts:async()=>({all:625,pending:10,approved:600,expiring:5,reported:2}),
    listAdminPage:(filters,page,options)=>{const d=deferred();requests.push({filters:{...filters},page,options,...d});return d.promise;},
    getAdminListing:async id=>row(id),updateListing:async()=>{if(failSave)throw new Error('Mất kết nối');return row();},requestSeoSync:async()=>({dispatched:true}),signOut:async()=>{},
    formatCurrency:value=>String(value),listingUrl:item=>'/tin/'+item.id,cleanText:(value,max)=>String(value??'').trim().slice(0,max),imageUrl:path=>path};
  const document={querySelector:()=>root,createElement:tag=>new Node(tag),addEventListener(){},hidden:false};
  const sandbox={document,window:{LumiMarketplace:api},sessionStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value),removeItem:key=>storage.delete(key)},AbortController,console,
    FormData:class{constructor(form){this.form=form;}entries(){return Object.entries(this.form.elements).map(([key,node])=>[key,node.value]);}},
    setTimeout:fn=>{const id=++timerId;timers.set(id,fn);return id;},clearTimeout:id=>timers.delete(id),setInterval:()=>1,clearInterval(){} };
  vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'../assets/js/marketplace-admin.js'),'utf8'),sandbox);
  return {get,requests,filters,edit,dialog,storage,runTimers:()=>{for(const [id,fn] of timers){timers.delete(id);fn();}}};
}
test('late responses cannot overwrite a newer filter result; selection is cleared on filter change',async()=>{
  const f=fixture();await tick();f.requests[0].resolve({rows:[row('initial')],total:625});await tick();
  const select=f.get('[data-admin-select-page]');select.checked=true;await select.emit('change');assert.equal(f.get('[data-admin-bulk]').hidden,false);
  f.filters.elements.keyword.value='S1';await f.filters.elements.keyword.emit('input');f.runTimers();await tick();
  assert.equal(f.get('[data-admin-bulk]').hidden,true);
  f.filters.elements.keyword.value='S3';await f.filters.elements.keyword.emit('input');f.runTimers();await tick();
  assert.equal(f.requests[1].options.signal.aborted,true);assert.equal(f.requests[2].filters.keyword,'S3');
  f.requests[2].resolve({rows:[row('newest-result')],total:1});await tick();
  f.requests[1].resolve({rows:[row('stale-result')],total:400});await tick();
  assert.equal(f.get('[data-admin-list]').children[0].dataset.rowId,'newest-result');assert.equal(f.get('[data-admin-result-count]').textContent,'1–1 / 1 tin đăng');
});
test('a saved page that no longer exists returns to the current last page',async()=>{
  const f=fixture({savedView:{page:32,pageSize:20,filters:{}}});await tick();assert.equal(f.requests[0].page,32);
  f.requests[0].resolve({rows:[],total:300});await tick();assert.equal(f.requests[1].page,15);
  f.requests[1].resolve({rows:[row('last-page')],total:300});await tick();assert.match(f.get('[data-admin-pagination]').textContent,/Trang 15 \/ 15/);
});
test('failed edits keep the dialog and typed content intact and re-enable controls',async()=>{
  const f=fixture({failSave:true});await tick();f.requests[0].resolve({rows:[row()],total:1});await tick();
  const title=f.get('[data-admin-list]').all().find(node=>node.className==='admin-title');await title.emit('click');await tick();
  assert.equal(f.dialog.open,true);f.edit.elements.description.value='Nội dung mới chưa được lưu';
  await f.edit.emit('submit');await tick();
  assert.equal(f.dialog.open,true);assert.equal(f.edit.elements.description.value,'Nội dung mới chưa được lưu');assert.match(f.get('[data-dialog-status]').textContent,/Mất kết nối/);assert.equal(f.edit.elements.description.disabled,false);
});
test('logout clears private rendered content and ignores an in-flight listing response',async()=>{
  const f=fixture();await tick();await f.get('[data-admin-logout]').emit('click');f.requests[0].resolve({rows:[row('private')],total:1});await tick();
  assert.equal(f.get('[data-admin-dashboard]').hidden,true);assert.equal(f.get('[data-admin-login]').hidden,false);assert.equal(f.get('[data-admin-list]').children.length,0);assert.equal(f.storage.has('lumi_admin_view_v2'),false);
});
