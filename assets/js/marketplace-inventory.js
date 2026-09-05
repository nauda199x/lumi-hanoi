/* Public inventory: native SEO links, ten records per request, no UI dependency. */
(()=>{
  const root=document.querySelector("[data-inventory]");
  const api=window.LumiMarketplace;
  if(!root||!api)return;
  const form=root.querySelector("[data-listing-filters]");
  const grid=root.querySelector("[data-listing-grid]");
  const state=root.querySelector("[data-listing-state]");
  const pager=root.querySelector("[data-inventory-pagination]");
  const summary=root.querySelector("[data-inventory-summary]");
  const count=root.querySelector("[data-listing-count]");
  const sort=root.querySelector("[name=sort]");
  const toggle=root.querySelector("[data-inventory-filter-toggle]");
  const base="/mua-ban-lumi-hanoi/";
  const towers={Signature:["S1","S2","S3","S5","S6"],Prestige:["P1","P2"],Elite:["E1","E2"]};
  const keys=["keyword","phase","tower","bedroom","max_price","area","sort"];
  let page=1,version=0,timer,controller,total=0,initial=true;
  const el=(tag,cls,text)=>{const n=document.createElement(tag);n.className=cls||"";if(text!==undefined)n.textContent=text;return n;};
  const values=()=>Object.fromEntries(new FormData(form));
  const filters=()=>{const v=values();return {...v,maxPrice:v.max_price};};
  const refreshTowers=(selected=form.elements.tower.value)=>{
    const options=towers[form.elements.phase.value]||Object.values(towers).flat();
    form.elements.tower.replaceChildren(new Option("Tất cả tòa",""),...options.map(v=>new Option(v,v)));
    if(options.includes(selected))form.elements.tower.value=selected;
  };
  const readLocation=()=>{
    const params=new URLSearchParams(location.search);
    const hashParams=new URLSearchParams(location.hash.slice(1));
    const candidate=params.get("page")||location.pathname.match(/\/page\/(\d+)\//)?.[1]||1;
    page=Math.max(1,Math.min(100000,Math.floor(Number(candidate)||1)));
    for(const key of keys){
      if(key!=="tower")form.elements[key].value=params.get(key)||(key==="sort"?"newest":"");
    }
    const tower=(params.get("tower")||hashParams.get("tower")||"").toUpperCase();
    if(tower&&!form.elements.phase.value)form.elements.phase.value=Object.entries(towers).find(([,list])=>list.includes(tower))?.[0]||"";
    refreshTowers(tower);
    if(!sort.value)sort.value="newest";
  };
  const pageUrl=(number,v=values())=>{
    const params=new URLSearchParams();
    for(const key of keys)if(v[key]&&!(key==="sort"&&v[key]==="newest"))params.set(key,v[key]);
    // A newly approved page may precede the next static SEO sync. Query URLs
    // still resolve on GitHub Pages during that short interval.
    const generated=Number(root.dataset.inventoryStaticPages)||1;
    let path=number>1&&number<=generated?`${base}page/${number}/`:base;
    if(number>generated)params.set("page",number);
    return path+(params.size?`?${params}`:"");
  };
  const updateUrl=(replace=false)=>{
    const url=pageUrl(page);
    if(location.pathname+location.search!==url)history[replace?"replaceState":"pushState"]({},"",url);
    const canonical=new URL(pageUrl(page,{sort:"newest"}),location.origin);
    canonical.hostname="lumi-hanoi.com";canonical.protocol="https:";canonical.port="";
    document.querySelector('link[rel="canonical"]')?.setAttribute("href",canonical.href);
    document.querySelector('meta[property="og:url"]')?.setAttribute("content",canonical.href);
    document.title=`Mua bán căn hộ Lumi Hanoi – ${page>1?`Trang ${page}`:"Quỹ căn đang chuyển nhượng"}`;
  };
  const area=value=>Number(value)>0?`${Number(value).toLocaleString("vi-VN",{maximumFractionDigits:1})} m²`:"";
  const rowFor=(listing,index)=>{
    const row=el("article","inventory-row");
    const url=api.listingUrl(listing);
    const media=el("a","inventory-media");media.href=url;media.setAttribute("aria-label",`Xem ${listing.title}`);
    const images=[...(listing.listing_images||[])].filter(i=>i.storage_path).sort((a,b)=>Number(a.sort_order)-Number(b.sort_order));
    const placeholder=el("span","inventory-placeholder","Chưa có ảnh");media.append(placeholder);
    if(images.length){
      const image=el("img");image.src=api.imageUrl(images[0].storage_path);image.alt=images[0].alt_text||listing.title;
      image.width=280;image.height=210;image.loading=index===0?"eager":"lazy";image.decoding="async";
      image.addEventListener("error",()=>image.remove(),{once:true});media.append(image);
      if(images.length>1)media.append(el("span","inventory-image-count",`${images.length} ảnh`));
    }
    const info=el("div","inventory-info");
    const heading=el("h3");const title=el("a","",listing.title||"Xem căn hộ");title.href=url;title.title=listing.title||"";heading.append(title);info.append(heading);
    const specs=[area(listing.area_sqm),listing.unit_type,listing.floor_label?`Tầng ${listing.floor_label.toLocaleLowerCase("vi")}`:""].filter(Boolean);
    if(specs.length)info.append(el("p","inventory-specs",specs.join(" · ")));
    const place=[listing.phase,listing.tower].filter(Boolean).join(" · ");
    if(place){const location=el("p","inventory-location",place);location.title=place;info.append(location);}
    const price=el("div","inventory-price");price.append(el("strong","",api.formatCurrency(listing.price_vnd,"sale")));
    if(Number(listing.price_vnd)>0&&Number(listing.area_sqm)>0)price.append(el("small","",`${(listing.price_vnd/listing.area_sqm/1e6).toLocaleString("vi-VN",{maximumFractionDigits:1})} tr/m²`));
    const poster=el("div","inventory-poster");
    if(listing.poster_name){
      const avatar=el("span","inventory-avatar",listing.poster_name.trim().split(/\s+/).slice(-2).map(p=>p[0]).join("").toUpperCase());avatar.setAttribute("aria-hidden","true");poster.append(avatar);
    }
    const person=el("div");
    if(listing.poster_name){const name=el("strong","",listing.poster_name);name.title=listing.poster_name;person.append(name);}
    const date=new Date(listing.approved_at||listing.created_at||"");
    if(!Number.isNaN(date.getTime())){
      const time=el("time","",`Đăng ${date.toLocaleDateString("vi-VN")}`);time.dateTime=date.toISOString();person.append(time);
    }
    poster.append(person);
    const actions=el("div","inventory-actions");
    const phone=String(listing.contact_phone||"").trim();const tel=phone.replace(/[^+\d]/g,"");
    if(tel){
      const call=el("a","inventory-call");call.href=`tel:${tel}`;call.setAttribute("aria-label",`Gọi ${listing.poster_name||"người đăng"}, ${phone}`);
      call.append(el("span","inventory-phone",phone),el("span","inventory-call-label","Gọi"));actions.append(call);
      const zalo=el("a","inventory-zalo","Zalo");zalo.href=`https://zalo.me/${phone.replace(/\D/g,"")}`;zalo.target="_blank";zalo.rel="noopener";actions.append(zalo);
    }
    const view=el("a","inventory-view","Xem chi tiết →");view.href=url;actions.append(view);
    row.append(media,info,price,poster,actions);return row;
  };
  const renderPager=()=>{
    const pages=Math.max(1,Math.ceil(total/10));pager.replaceChildren();
    const link=(n,label,rel)=>{const a=el("a","",label);a.href=pageUrl(n);a.dataset.page=n;a.setAttribute("aria-label",`Trang ${n}`);if(rel)a.rel=rel;if(n===page)a.setAttribute("aria-current","page");pager.append(a);};
    if(page>1)link(page-1,"← Trước","prev");
    const visible=new Set([1,pages,page-1,page,page+1]);if(page<3)[2,3].forEach(n=>visible.add(n));
    let last=0;
    [...visible].filter(n=>n>=1&&n<=pages).sort((a,b)=>a-b).forEach(n=>{
      if(last&&n-last>1){const gap=el("span","inventory-ellipsis","…");gap.setAttribute("aria-hidden","true");pager.append(gap);}link(n,String(n));last=n;
    });
    if(page<pages)link(page+1,"Tiếp →","next");pager.hidden=pages<=1;
    summary.textContent=total?`Hiển thị ${(page-1)*10+1}–${Math.min(page*10,total)} trong ${total} căn`:"Hiển thị 0 căn";
  };
  const showState=(title,copy,retry=false)=>{
    grid.replaceChildren();state.hidden=false;pager.hidden=true;
    state.querySelector("[data-state-title]").textContent=title;
    state.querySelector("[data-state-copy]").textContent=copy;
    state.querySelector("[data-inventory-retry]").hidden=!retry;
  };
  const load=async({scroll=false}={})=>{
    const requestVersion=++version;controller?.abort();controller=new AbortController();
    root.setAttribute("aria-busy","true");
    const requestController=controller;
    const timeout=setTimeout(()=>requestController.abort(),15000);
    // Never leave stale cards visible under a newly selected filter.
    const keepStatic=initial&&grid.querySelector("[data-static-listing-card]")&&!keys.some(k=>values()[k]&&!(k==="sort"&&values()[k]==="newest"))&&!new URLSearchParams(location.search).has("page");
    initial=false;
    if(!keepStatic){
      grid.replaceChildren(...Array.from({length:3},()=>el("div","inventory-skeleton")));
      state.hidden=true;pager.hidden=true;summary.textContent="Đang tải quỹ căn…";
    }
    try{
      const result=await api.listPublicPage("sale",filters(),page,{signal:controller.signal});
      if(requestVersion!==version)return;
      total=result.total;
      const last=Math.max(1,Math.ceil(total/10));
      if(page>last){page=last;updateUrl(true);return load({scroll});}
      grid.replaceChildren(...result.rows.map(rowFor));count.textContent=`${total} tin đăng`;
      const schema=document.querySelector("[data-inventory-schema]");
      if(schema)schema.textContent=JSON.stringify({"@context":"https://schema.org","@type":"ItemList",numberOfItems:result.rows.length,itemListElement:result.rows.map((row,i)=>({"@type":"ListItem",position:(page-1)*10+i+1,url:`https://lumi-hanoi.com${api.listingUrl(row)}`,name:row.title}))});
      if(!total){
        const active=keys.some(k=>k!=="sort"&&values()[k]);
        showState(active?"Không tìm thấy căn phù hợp":"Chưa có căn đang rao bán",active?"Anh/chị có thể xóa bớt bộ lọc để xem thêm quỹ căn.":"Tin mua bán mới sẽ được hiển thị sau khi duyệt.");
      }
      renderPager();updateUrl(true);
      if(scroll){root.querySelector("[data-inventory-results]").scrollIntoView({block:"start",behavior:"instant"});summary.focus({preventScroll:true});}
    }catch(error){
      if(requestVersion!==version)return;
      count.textContent="Chưa tải được dữ liệu";summary.textContent="";
      showState("Chưa thể tải quỹ căn","Vui lòng kiểm tra kết nối và thử lại.",true);
    }finally{clearTimeout(timeout);if(requestVersion===version)root.setAttribute("aria-busy","false");}
  };
  const changed=(delay=0)=>{
    clearTimeout(timer);++version;controller?.abort();page=1;updateUrl(delay>0);
    count.textContent="Đang tải…";grid.replaceChildren();pager.hidden=true;state.hidden=true;
    const active=keys.filter(k=>k!=="sort"&&values()[k]).length;
    toggle.textContent=`Bộ lọc${active?` (${active})`:""}`;
    timer=setTimeout(()=>load(),delay);
  };
  form.addEventListener("input",e=>{if(e.target.name==="keyword")changed(320);});
  form.addEventListener("change",e=>{if(e.target.name==="phase")refreshTowers();if(e.target.name!=="keyword")changed();});
  sort.addEventListener("change",()=>changed());
  form.addEventListener("submit",e=>{e.preventDefault();changed();});
  form.addEventListener("reset",()=>setTimeout(()=>{refreshTowers("");sort.value="newest";changed();},0));
  toggle.hidden=false;
  root.classList.add("inventory-enhanced");
  toggle.addEventListener("click",()=>{
    const open=toggle.getAttribute("aria-expanded")!=="true";toggle.setAttribute("aria-expanded",String(open));root.classList.toggle("inventory-filters-open",open);
    if(open)form.scrollIntoView({block:"start",behavior:"instant"});
  });
  form.addEventListener("keydown",e=>{if(e.key==="Escape"&&toggle.getAttribute("aria-expanded")==="true"){toggle.click();toggle.focus();}});
  pager.addEventListener("click",e=>{
    const a=e.target.closest("a[data-page]");if(!a||e.button||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
    e.preventDefault();clearTimeout(timer);page=Number(a.dataset.page);updateUrl();load({scroll:true});
  });
  state.querySelector("[data-inventory-retry]").addEventListener("click",()=>load());
  window.addEventListener("popstate",()=>{clearTimeout(timer);readLocation();load();});
  readLocation();load();
})();
