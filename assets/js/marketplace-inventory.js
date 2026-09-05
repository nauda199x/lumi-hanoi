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
  const type=root.dataset.listingType==="rent"?"rent":"sale";
  const base=type==="rent"?"/cho-thue-lumi-hanoi/":"/mua-ban-lumi-hanoi/";
  const homeTitle=/\/page\/\d+\/$/.test(location.pathname)?root.dataset.inventoryHomeTitle||document.title:document.title;
  const quick=root.querySelector("[data-inventory-quick]");
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
    document.title=page>1?`${type==="rent"?"Cho thuê":"Mua bán"} căn hộ Lumi Hanoi – Trang ${page}`:homeTitle;
  };
  const area=value=>Number(value)>0?`${Number(value).toLocaleString("vi-VN",{maximumFractionDigits:1})} m²`:"";
  const icons={
    pin:'<path d="M12 21s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/>',
    area:'<path d="M9 3H3v6m12-6h6v6M3 15v6h6m12-6v6h-6M3 3l5 5m8 8 5 5m0-18-5 5M8 16l-5 5"/>',
    bed:'<path d="M3 18V7m18 11V7M3 15h18M6 11V7h12v4M3 11h18v9M3 15v5"/>',
    floor:'<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
    phone:'<path d="m8 3 3 5-3 3c2 3 3 4 6 5l3-3 4 3c-1 4-3 5-6 4C8 18 3 12 3 6c0-2 2-3 5-3Z"/>',
    image:'<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8" cy="9" r="1.5"/><path d="m3 17 5-5 4 4 3-3 6 6"/>'
  };
  const icon=name=>{const span=el("span");span.innerHTML=`<svg class="inventory-icon" viewBox="0 0 24 24" aria-hidden="true">${icons[name]||""}</svg>`;return span.firstElementChild;};
  const initials=name=>String(name||"").trim().split(/\s+/).filter(p=>/[\p{L}\p{N}]/u.test(p)).slice(-2).map(p=>p.match(/[\p{L}\p{N}]/u)[0]).join("").toLocaleUpperCase("vi");
  const rowFor=(listing,index)=>{
    const row=el("article","inventory-row");
    const url=api.listingUrl(listing);
    const media=el("a","inventory-media");media.href=url;media.setAttribute("aria-label",`Xem ${listing.title||"căn hộ"}`);
    const images=[...(listing.listing_images||[])].filter(i=>i.storage_path).sort((a,b)=>Number(a.sort_order)-Number(b.sort_order));
    media.append(el("span","inventory-placeholder","Chưa có ảnh"));
    if(images.length){
      const image=el("img");image.src=api.imageUrl(images[0].storage_path);image.alt=images[0].alt_text||listing.title||"Ảnh căn hộ Lumi Hanoi";
      image.width=560;image.height=420;image.loading=index===0?"eager":"lazy";image.decoding="async";
      image.addEventListener("error",()=>image.remove(),{once:true});media.append(image);
      const counter=el("span","inventory-image-count");counter.append(icon("image"),document.createTextNode(`${images.length} ảnh`));media.append(counter);
    }
    media.append(el("span","inventory-status",type==="rent"?"CHO THUÊ":"MUA BÁN"));
    const info=el("div","inventory-info");
    const place=[listing.phase,listing.tower].filter(Boolean).join(" · ");
    if(place){const location=el("p","inventory-location");location.title=place;location.append(icon("pin"),el("span","",place));info.append(location);}
    const heading=el("h3");const title=el("a","",listing.title||"Xem căn hộ");title.href=url;title.title=listing.title||"";heading.append(title);info.append(heading);
    const specs=el("p","inventory-specs");
    const facts=[["area",area(listing.area_sqm)],["bed",listing.unit_type],["floor",listing.floor_label?`Tầng ${String(listing.floor_label).toLocaleLowerCase("vi")}`:""]].filter(([,value])=>value);
    facts.forEach(([name,value],i)=>{const item=el("span");item.append(icon(name),document.createTextNode(value+(i<facts.length-1?", ":"")));specs.append(item);});
    if(specs.childElementCount)info.append(specs);
    const price=el("div","inventory-price");price.append(el("span","inventory-price-label",type==="rent"?"Giá thuê":"Giá bán"));
    const formatted=api.formatCurrency(listing.price_vnd,type),parts=formatted.match(/^(.*?) (tỷ|triệu\/tháng|triệu)$/);
    const amount=el("strong","",parts?parts[1]:formatted);
    if(parts)amount.append(document.createTextNode(" "),el("span","inventory-price-unit",parts[2]));price.append(amount);
    if(type==="sale"&&Number(listing.price_vnd)>0&&Number(listing.area_sqm)>0)price.append(el("small","",`${(listing.price_vnd/listing.area_sqm/1e6).toLocaleString("vi-VN",{maximumFractionDigits:1})} tr/m²`));
    const poster=el("div","inventory-poster");
    if(listing.poster_name){const avatar=el("span","inventory-avatar",initials(listing.poster_name));avatar.setAttribute("aria-hidden","true");poster.append(avatar);}
    const person=el("div");
    if(listing.poster_name){const name=el("strong","",listing.poster_name);name.title=listing.poster_name;person.append(name);}
    const date=new Date(listing.approved_at||listing.created_at||"");
    if(!Number.isNaN(date.getTime())){const time=el("time","",`Đăng ${date.toLocaleDateString("vi-VN")}`);time.dateTime=date.toISOString();person.append(time);}
    poster.append(person);
    const actions=el("div","inventory-actions");
    const phone=String(listing.contact_phone||"").trim();const tel=phone.replace(/[^+\d]/g,"");
    if(tel){
      const call=el("a","inventory-call");call.href=`tel:${tel}`;call.setAttribute("aria-label",`Gọi ${listing.poster_name||"người đăng"}, ${phone}`);
      call.append(icon("phone"),el("span","inventory-phone",phone),el("span","inventory-call-label","Gọi"));actions.append(call);
      const zalo=el("a","inventory-zalo","Zalo");zalo.href=`https://zalo.me/${phone.replace(/\D/g,"")}`;zalo.target="_blank";zalo.rel="noopener";actions.append(zalo);
    }
    const view=el("a","inventory-view");view.href=url;view.append(el("span","","Xem chi tiết"),el("span","","→"));actions.append(view);
    row.append(media,info,price,poster,actions);return row;
  };
  const syncControls=()=>{
    const active=keys.filter(k=>k!=="sort"&&values()[k]).length;
    toggle.textContent=`Bộ lọc${active?` (${active})`:""}`;
    quick?.querySelectorAll("[data-unit-filter]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.unitFilter===form.elements.bedroom.value)));
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
      const result=await api.listPublicPage(type,filters(),page,{signal:controller.signal});
      if(requestVersion!==version)return;
      total=result.total;
      const last=Math.max(1,Math.ceil(total/10));
      if(page>last){page=last;updateUrl(true);return load({scroll});}
      grid.replaceChildren(...result.rows.map(rowFor));count.textContent=`${total} tin đăng`;
      const schema=document.querySelector("[data-inventory-schema]");
      if(schema)schema.textContent=JSON.stringify({"@context":"https://schema.org","@type":"ItemList",numberOfItems:result.rows.length,itemListElement:result.rows.map((row,i)=>({"@type":"ListItem",position:(page-1)*10+i+1,url:`https://lumi-hanoi.com${api.listingUrl(row)}`,name:row.title}))});
      if(!total){
        const active=keys.some(k=>k!=="sort"&&values()[k]);
        showState(active?"Không tìm thấy căn phù hợp":(type==="rent"?"Chưa có căn đang cho thuê":"Chưa có căn đang rao bán"),active?"Anh/chị có thể xóa bớt bộ lọc để xem thêm quỹ căn.":"Tin mới sẽ được hiển thị sau khi duyệt.");
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
    syncControls();
    timer=setTimeout(()=>load(),delay);
  };
  quick?.addEventListener("click",e=>{const button=e.target.closest("[data-unit-filter]");if(button){form.elements.bedroom.value=button.dataset.unitFilter;changed();}});
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
  window.addEventListener("popstate",()=>{clearTimeout(timer);readLocation();syncControls();load();});
  readLocation();syncControls();load();
})();
