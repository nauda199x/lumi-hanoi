const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const source=name=>fs.readFileSync(path.join(__dirname,'../assets/js',name),'utf8');
class Element {
  constructor(){this.nodes=new Map();this.children=[];this.attributes={};this.listeners={};this.dataset={};this.hidden=false;this.textContent='';this.className='';this.clientWidth=800;this.scrollLeft=0;this.offsetLeft=0;this.offsetWidth=88;this.classList={add:()=>{},toggle:()=>{},remove:()=>{}};}
  querySelectorAll(s){return this.nodes.get(s)||[];}
  querySelector(s){return this.querySelectorAll(s)[0]||null;}
  map(s,...nodes){this.nodes.set(s,nodes);return nodes[0];}
  addEventListener(s,fn){(this.listeners[s]??=[]).push(fn);}
  async emit(s,event={}){for(const fn of this.listeners[s]||[])await fn({currentTarget:this,target:this,preventDefault(){},...event});}
  setAttribute(k,v){this.attributes[k]=String(v);}
  getAttribute(k){return this.attributes[k]??null;}
  removeAttribute(k){delete this.attributes[k];}
  append(...nodes){this.children.push(...nodes);}
  scrollTo({left}){this.scrollLeft=left;}
  focus(){} select(){}
}
function fixture(){
  const root=new Element(),page=new Element(),store=new Map(),timers=new Map();
  root.map('.ld-page',page);root.map('[data-detail-content]',page);
  for(const key of ['title','code','type','category','price','price-label','price-per-sqm','area','unit','tower','phase','floor','furnishing','description','poster','avatar','date','date-wrap','back','floorplan','same-tower','same-unit','unit-guide'])root.map(`[data-detail-${key}]`,new Element(),new Element());
  for(const selector of ['[data-detail-actions]','[data-detail-save]','[data-save-label]','[data-detail-share]','[data-detail-toast]','[data-share-fallback]','[data-share-link]']){const node=new Element();page.map(selector,node);root.map(selector,node);}
  root.map('[data-contact-empty]',new Element());root.map('[data-detail-mobile-contact]',new Element());root.map('[data-report-box]',new Element());
  const phone=new Element(),compact=new Element(),zalo=new Element();phone.map('[data-phone-label]',new Element());compact.textContent='Gọi ngay';root.map('[data-detail-phone]',phone,compact);root.map('[data-detail-zalo]',zalo);
  const api={formatCurrency:(price,type)=>price?`${price/(type==='rent'?1e6:1e9)} ${type==='rent'?'triệu/tháng':'tỷ'}`:'Liên hệ',imageUrl:src=>'https://images.example/'+encodeURIComponent(src),listingUrl:row=>`/${row.listing_type==='rent'?'cho-thue':'mua-ban'}-lumi-hanoi/${row.slug}/`};
  const context={window:{LumiMarketplace:api,matchMedia:()=>({matches:true})},document:{querySelector:()=>null,createElement:()=>new Element()},localStorage:{getItem:k=>store.get(k),setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)},navigator:{clipboard:{writeText:async()=>{}}},location:{pathname:'/tin-dang-lumi-hanoi/',href:'https://lumi-hanoi.com/tin-dang-lumi-hanoi/?slug=test',origin:'https://lumi-hanoi.com'},URL,URLSearchParams,setTimeout:fn=>{timers.set(1,fn);return 1;},clearTimeout:()=>{},requestAnimationFrame:fn=>{fn();return 1;},cancelAnimationFrame:()=>{}};
  vm.runInNewContext(source('listing-detail-ui.js'),context);
  return {root,page,context,ui:context.window.LumiListingDetail,phone,compact,zalo,store};
}
const listing={id:'id-1',slug:'can-ho-test',listing_code:'LH-TEST',title:'Căn hộ Lumi S3',description:'Thông tin mô tả căn hộ.',listing_type:'rent',unit_type:'2PN',area_sqm:54,price_vnd:10000000,tower:'S3',phase:'Signature',contact_phone:'0779 637 268',poster_name:'Ngọc Vân Realty',approved_at:'2026-09-08T03:00:00Z',listing_images:[]};
test('rent hydration keeps monthly prices, all repeated facts, valid phone and same-tower links',()=>{
  const f=fixture();f.ui.hydrate(f.root,listing);
  assert.equal(f.root.querySelector('[data-detail-price]').textContent,'10 triệu/tháng');
  assert.ok(f.root.querySelectorAll('[data-detail-price-per-sqm]').every(n=>n.textContent===''));
  assert.ok(f.root.querySelectorAll('[data-detail-area]').every(n=>n.textContent==='54 m²'));
  assert.equal(f.phone.href,'tel:0779637268');assert.equal(f.zalo.href,'https://zalo.me/0779637268');assert.equal(f.compact.textContent,'Gọi ngay');
  assert.equal(f.root.querySelector('[data-detail-same-tower]').href,'/cho-thue-lumi-hanoi/#tower=S3');
  assert.equal(f.root.querySelector('[data-detail-date]').textContent,'08/09/2026');
});
test('sale, unknown fields and missing phone never create rental ppm or fake contact actions',()=>{
  const f=fixture();f.ui.hydrate(f.root,{...listing,listing_type:'sale',price_vnd:5400000000,contact_phone:'',floor_label:null});
  assert.equal(f.root.querySelector('[data-detail-price-per-sqm]').textContent,'~100 tr/m²');
  assert.equal(f.root.querySelector('[data-detail-floor]').textContent,'Chưa cập nhật');
  assert.equal(f.phone.hidden,true);assert.equal(f.zalo.hidden,true);assert.equal(f.root.querySelector('[data-detail-mobile-contact]').hidden,true);
});
test('gallery keeps every image in order, gives only hero high priority, and escapes untrusted content',()=>{
  const f=fixture();const html=f.ui.galleryMarkup({...listing,title:'<img onerror="alert(1)">',listing_images:[{storage_path:'b.jpg',sort_order:2},{storage_path:'a.jpg',sort_order:1}]});
  assert.ok(html.indexOf('a.jpg')<html.indexOf('b.jpg'));assert.equal((html.match(/fetchpriority="high"/g)||[]).length,1);assert.equal((html.match(/<figure>/g)||[]).length,2);assert.ok(html.includes('&lt;img onerror=&quot;alert(1)&quot;&gt;'));assert.ok(!html.includes('<img onerror='));
  assert.match(f.ui.galleryMarkup({...listing,listing_images:[]}),/Hình ảnh đang được bổ sung/);
});
test('gallery buttons and keyboard select every photo and stop at boundaries',async()=>{
  const f=fixture(),gallery=new Element(),track=new Element(),stage=new Element(),counter=new Element();
  const images=[0,1,2].map(i=>Object.assign(new Element(),{src:`${i}.jpg`}));track.map('figure img',...images);gallery.map('.ld-gallery-track',track);gallery.map('.ld-gallery-stage',stage);gallery.map('[data-gallery-counter]',counter);f.root.map('[data-detail-gallery]',gallery);f.ui.init(f.root);
  await track.emit('keydown',{key:'ArrowRight'});assert.equal(track.scrollLeft,800);assert.equal(counter.textContent,'2 / 3');
  await track.emit('keydown',{key:'ArrowRight'});await track.emit('keydown',{key:'ArrowRight'});assert.equal(track.scrollLeft,1600);assert.equal(counter.textContent,'3 / 3');assert.equal(stage.children[1].disabled,true);
  await stage.children[0].emit('click');assert.equal(track.scrollLeft,800);
});
test('saving is device-local, can be undone, and static hydration does not duplicate listeners',async()=>{
  const f=fixture();f.ui.hydrate(f.root,listing);f.ui.hydrate(f.root,listing);const save=f.page.querySelector('[data-detail-save]');assert.equal(save.listeners.click.length,1);await save.emit('click');assert.equal(save.getAttribute('aria-pressed'),'true');assert.equal(f.store.get('lumi-saved-listing:can-ho-test'),'1');await save.emit('click');assert.equal(save.getAttribute('aria-pressed'),'false');
});
test('blocked clipboard gives a selectable clean listing URL instead of a false success',async()=>{
  const f=fixture();f.context.navigator.clipboard.writeText=async()=>{throw Error('denied');};f.ui.hydrate(f.root,listing);await f.page.querySelector('[data-detail-share]').emit('click');assert.equal(f.page.querySelector('[data-share-fallback]').hidden,false);assert.equal(f.page.querySelector('[data-share-link]').value,'https://lumi-hanoi.com/cho-thue-lumi-hanoi/can-ho-test/');
});
test('unpublished listing disables contacts and hides the dock; offline retains the static snapshot',async()=>{
  for(const offline of [false,true]){
    const f=fixture();f.ui.hydrate(f.root,listing);const note=new Element();f.root.map('[data-live-status]',note);f.root.map('[data-detail-phone],[data-detail-zalo],[data-static-phone],[data-static-zalo]',f.phone,f.compact,f.zalo);const dock=f.root.querySelector('[data-detail-mobile-contact]');f.root.map('[data-detail-mobile-contact],[data-report-box],.ld-contact-note',dock);const robots=new Element();f.context.document.querySelector=s=>s==='[data-static-listing]'?f.root:s==='meta[name="robots"]'?robots:null;f.context.window.LumiMarketplace.getPublicListing=()=>offline?Promise.reject(Error('offline')):Promise.resolve(null);vm.runInNewContext(source('marketplace-static-status.js'),f.context);await new Promise(resolve=>setImmediate(resolve));
    if(!offline){assert.equal(robots.content,'noindex,follow');assert.equal(f.phone.getAttribute('aria-disabled'),'true');assert.equal(dock.hidden,true);}else{assert.equal(f.phone.getAttribute('aria-disabled'),null);assert.equal(dock.hidden,false);}
  }
});
