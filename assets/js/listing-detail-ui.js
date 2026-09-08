(()=>{
  "use strict";
  const pages=new WeakSet(),galleries=new WeakSet();
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const text=(root,selector,value)=>root.querySelectorAll(selector).forEach(node=>node.textContent=value??"");
  const reduced=()=>window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const initials=name=>String(name||"Người đăng").trim().split(/\s+/).slice(-2).map(word=>word[0]).join("").toLocaleUpperCase("vi");
  const floorplanUrl=tower=>{const t=String(tower||"").toLowerCase();return /^(s[12356]|p[12]|e[12])$/.test(t)?`/mat-bang-lumi-hanoi/lumi-${t[0]==="s"?"signature":t[0]==="p"?"prestige":"elite"}/${t}/`:"/mat-bang-lumi-hanoi/";};
  const toast=(root,message)=>{const node=root.querySelector("[data-detail-toast]");if(!node)return;clearTimeout(node._timer);node.textContent=message;node.hidden=false;node._timer=setTimeout(()=>node.hidden=true,3500);};
  const sortedImages=listing=>[...(listing.listing_images||[])].filter(image=>image.storage_path).sort((a,b)=>Number(a.sort_order||0)-Number(b.sort_order||0));
  const galleryMarkup=listing=>{
    const images=sortedImages(listing);
    if(!images.length)return '<div class="ld-empty-gallery"><strong>Hình ảnh đang được bổ sung</strong><p>Liên hệ người đăng để xem hình ảnh và hiện trạng căn.</p></div>';
    const figures=images.map((item,index)=>`<figure><img src="${esc(window.LumiMarketplace.imageUrl(item.storage_path))}" alt="${esc(item.alt_text||`${listing.title} — ảnh ${index+1}`)}" width="1200" height="900" loading="${index?"lazy":"eager"}" ${index?"":'fetchpriority="high"'} decoding="async"></figure>`).join("");
    return `<div class="ld-gallery-stage"><div class="ld-gallery-track" tabindex="0" aria-label="Ảnh tin đăng, dùng phím trái và phải để chuyển ảnh">${figures}</div><span class="ld-gallery-counter" data-gallery-counter>1 / ${images.length}</span></div>`;
  };
  const initGallery=gallery=>{
    const track=gallery?.querySelector(".ld-gallery-track");if(!track||galleries.has(track))return;galleries.add(track);
    const images=[...track.querySelectorAll("figure img")];if(!images.length)return;
    const stage=gallery.querySelector(".ld-gallery-stage"),counter=gallery.querySelector("[data-gallery-counter]");
    let active=0,frame=0,width=track.clientWidth;
    const thumbs=document.createElement("div");thumbs.className="ld-thumbs";thumbs.setAttribute("aria-label","Chọn ảnh");
    const previous=document.createElement("button"),next=document.createElement("button");
    [previous,next].forEach(button=>{button.type="button";button.className="ld-gallery-nav";});
    previous.classList.add("ld-gallery-nav--prev");previous.setAttribute("aria-label","Ảnh trước");previous.textContent="‹";
    next.classList.add("ld-gallery-nav--next");next.setAttribute("aria-label","Ảnh tiếp theo");next.textContent="›";
    const buttons=[];
    const update=index=>{
      active=Math.max(0,Math.min(images.length-1,index));if(counter)counter.textContent=`${active+1} / ${images.length}`;
      previous.disabled=active===0;next.disabled=active===images.length-1;
      buttons.forEach((button,i)=>button.setAttribute("aria-current",String(i===active)));
      const button=buttons[active];if(button){const left=button.offsetLeft-thumbs.offsetLeft;if(left<thumbs.scrollLeft||left+button.offsetWidth>thumbs.scrollLeft+thumbs.clientWidth)thumbs.scrollTo({left:Math.max(0,left-thumbs.clientWidth/2+button.offsetWidth/2),behavior:reduced()?"auto":"smooth"});}
    };
    const go=index=>{const target=Math.max(0,Math.min(images.length-1,index));track.scrollTo({left:target*track.clientWidth,behavior:reduced()?"auto":"smooth"});update(target);};
    if(images.length>1){
      images.forEach((image,index)=>{const button=document.createElement("button");button.type="button";button.className="ld-thumb";button.setAttribute("aria-label",`Xem ảnh ${index+1}`);const thumb=document.createElement("img");thumb.src=image.src;thumb.alt="";thumb.width=88;thumb.height=66;thumb.loading="lazy";thumb.decoding="async";button.append(thumb);button.addEventListener("click",()=>go(index));buttons.push(button);thumbs.append(button);});
      stage.append(previous,next);gallery.append(thumbs);previous.addEventListener("click",()=>go(active-1));next.addEventListener("click",()=>go(active+1));
    }
    track.addEventListener("keydown",event=>{if(event.key==="ArrowLeft"||event.key==="ArrowRight"){event.preventDefault();go(active+(event.key==="ArrowRight"?1:-1));}});
    track.addEventListener("scroll",()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>update(Math.round(track.scrollLeft/(track.clientWidth||1))));},{passive:true});
    if(window.ResizeObserver)new ResizeObserver(()=>{if(width===track.clientWidth||!track.clientWidth)return;width=track.clientWidth;track.scrollTo({left:active*width,behavior:"instant"});update(active);}).observe(track);
    images.forEach(image=>image.addEventListener("error",()=>{image.alt="Ảnh chưa tải được. Vui lòng thử lại sau.";},{once:true}));update(0);
  };
  const hydrateContact=(root,listing)=>{
    const phone=String(listing.contact_phone||"").trim(),tel=phone.replace(/[^+\d]/g,""),zalo=phone.replace(/\D/g,"");
    text(root,"[data-detail-poster]",listing.poster_name||"Người đăng");text(root,"[data-detail-avatar]",initials(listing.poster_name));
    root.querySelectorAll("[data-detail-phone]").forEach(link=>{link.hidden=!tel;if(tel){link.href=`tel:${tel}`;link.removeAttribute("aria-disabled");const label=link.querySelector("[data-phone-label]");if(label)label.textContent=phone;link.setAttribute("aria-label",`Gọi người đăng: ${phone}`);}else link.removeAttribute("href");});
    root.querySelectorAll("[data-detail-zalo]").forEach(link=>{link.hidden=!zalo;if(zalo){link.href=`https://zalo.me/${zalo}`;link.removeAttribute("aria-disabled");}else link.removeAttribute("href");});
    const empty=root.querySelector("[data-contact-empty]");if(empty)empty.hidden=!!tel;const dock=root.querySelector("[data-detail-mobile-contact]");if(dock)dock.hidden=!tel;
  };
  const hydrate=(root,listing)=>{
    const api=window.LumiMarketplace,rent=listing.listing_type==="rent",category=rent?"Cho thuê Lumi Hanoi":"Mua bán Lumi Hanoi",base=rent?"/cho-thue-lumi-hanoi/":"/mua-ban-lumi-hanoi/";
    const price=api.formatCurrency(listing.price_vnd,listing.listing_type),area=Number(listing.area_sqm)>0?`${Number(listing.area_sqm).toLocaleString("vi-VN")} m²`:"Chưa cập nhật";
    const ppsm=!rent&&Number(listing.price_vnd)>0&&Number(listing.area_sqm)>0?`~${(Number(listing.price_vnd)/Number(listing.area_sqm)/1e6).toLocaleString("vi-VN",{maximumFractionDigits:1})} tr/m²`:"";
    const fields={title:listing.title,code:listing.listing_code,type:rent?"Cho thuê":"Mua bán",category,price,"price-label":rent?"cho thuê":"bán","price-per-sqm":ppsm,area,unit:listing.unit_type||"Chưa cập nhật",tower:listing.tower||"Chưa cập nhật",phase:listing.phase||"Chưa cập nhật",floor:listing.floor_label||"Chưa cập nhật",furnishing:listing.furnishing||"Chưa cập nhật",description:listing.description||"Người đăng chưa bổ sung mô tả."};
    Object.entries(fields).forEach(([key,value])=>text(root,`[data-detail-${key}]`,value));root.dataset.listingId=listing.id||"";root.dataset.listingSlug=listing.slug||"";
    const date=String(listing.approved_at||listing.created_at||"").slice(0,10),dateNode=root.querySelector("[data-detail-date]"),dateWrap=root.querySelector("[data-detail-date-wrap]");if(dateWrap)dateWrap.hidden=!/^\d{4}-\d{2}-\d{2}$/.test(date);if(dateNode){dateNode.dateTime=date;dateNode.textContent=date.split("-").reverse().join("/");}
    const links={back:base,floorplan:floorplanUrl(listing.tower),"same-tower":base+"#"+new URLSearchParams(listing.tower?{tower:listing.tower}:{}),"same-unit":base+"#"+new URLSearchParams(listing.unit_type?{bedroom:listing.unit_type}:{})};Object.entries(links).forEach(([key,value])=>root.querySelectorAll(`[data-detail-${key}]`).forEach(link=>link.href=value));
    const gallery=root.querySelector("[data-detail-gallery]");if(gallery){const urls=sortedImages(listing).map(image=>api.imageUrl(image.storage_path)),current=[...gallery.querySelectorAll(".ld-gallery-track img")].map(image=>image.getAttribute("src"));if(urls.join("\n")!==current.join("\n")||!gallery.children.length)gallery.innerHTML=galleryMarkup(listing);}
    const unitLinks={"1PN":"/can-ho-1-phong-ngu-lumi-hanoi/","2PN":"/can-ho-2-phong-ngu-lumi-hanoi/","3PN":"/can-ho-3-phong-ngu-lumi-hanoi/","4PN":"/can-ho-4-phong-ngu-lumi-hanoi/","Duplex":"/duplex-penthouse-lumi-hanoi/","Penthouse":"/duplex-penthouse-lumi-hanoi/","Shop chân đế":"/cho-thue-shop-chan-de-lumi-hanoi/"};
    const guide=root.querySelector("[data-detail-unit-guide]");if(guide){guide.hidden=!unitLinks[listing.unit_type];guide.href=unitLinks[listing.unit_type]||"/mat-bang-lumi-hanoi/";}
    root.dataset.listingUrl=api.listingUrl(listing);
    hydrateContact(root,listing);const report=root.querySelector("[data-report-box]");if(report)report.hidden=!listing.id;document.title=`${listing.title} | Lumi Hanoi`;const content=root.querySelector("[data-detail-content]");if(content)content.hidden=false;init(root);
  };
  const init=root=>{
    const page=root.querySelector(".ld-page");if(!page)return;initGallery(root.querySelector("[data-detail-gallery]"));if(pages.has(page))return;pages.add(page);
    const actions=page.querySelector("[data-detail-actions]");if(actions)actions.hidden=false;
    const key=()=>`lumi-saved-listing:${root.dataset.listingSlug||location.pathname}`,save=page.querySelector("[data-detail-save]");
    const saved=()=>{try{return localStorage.getItem(key())==="1";}catch{return false;}};
    const updateSave=()=>{save?.setAttribute("aria-pressed",String(saved()));text(page,"[data-save-label]",saved()?"Đã lưu":"Lưu tin");};updateSave();
    save?.addEventListener("click",()=>{try{const value=!saved();if(value)localStorage.setItem(key(),"1");else localStorage.removeItem(key());updateSave();toast(root,value?"Đã lưu tin trên thiết bị này.":"Đã bỏ lưu tin.");}catch{toast(root,"Trình duyệt chưa cho phép lưu tin trên thiết bị này.");}});
    page.querySelector("[data-detail-share]")?.addEventListener("click",async()=>{
      const url=document.querySelector('link[rel="canonical"]')?.href||(root.dataset.listingUrl?new URL(root.dataset.listingUrl,location.origin).href:location.href.split("#")[0]);
      try{if(navigator.share){await navigator.share({title:document.title,url});return;}}catch(error){if(error.name==="AbortError")return;}
      try{if(!navigator.clipboard?.writeText)throw new Error("clipboard unavailable");await navigator.clipboard.writeText(url);toast(root,"Đã sao chép đường dẫn tin đăng.");}catch{const box=page.querySelector("[data-share-fallback]"),input=page.querySelector("[data-share-link]");if(box&&input){box.hidden=false;input.value=url;input.focus();input.select();}}
    });
    page.querySelector("[data-share-close]")?.addEventListener("click",()=>{page.querySelector("[data-share-fallback]").hidden=true;page.querySelector("[data-detail-share]").focus();});
    const description=page.querySelector("[data-detail-description]"),more=page.querySelector("[data-detail-readmore]");if(description&&more&&description.textContent.length>850){description.classList.add("is-collapsed");more.hidden=false;more.addEventListener("click",()=>{const expanded=more.getAttribute("aria-expanded")!=="true";description.classList.toggle("is-collapsed",!expanded);more.setAttribute("aria-expanded",String(expanded));more.textContent=expanded?"Thu gọn mô tả ↑":"Xem đầy đủ mô tả ↓";});}
    const nav=[...page.querySelectorAll(".ld-sections a")];if(window.IntersectionObserver){const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting)nav.forEach(link=>{if(link.hash===`#${entry.target.id}`)link.setAttribute("aria-current","location");else link.removeAttribute("aria-current");});}),{rootMargin:"-20% 0px -55% 0px"});page.querySelectorAll(".ld-section").forEach(section=>observer.observe(section));}
    page.querySelector("[data-report-form]")?.addEventListener("submit",async event=>{event.preventDefault();const form=event.currentTarget,button=form.querySelector('button[type="submit"]'),status=form.querySelector("[data-report-status]");if(!root.dataset.listingId||button.disabled)return;button.disabled=true;button.textContent="Đang gửi…";try{await window.LumiMarketplace.createReport(root.dataset.listingId,form.elements.reason.value,form.elements.details.value);status.textContent="Cảm ơn anh/chị. Báo cáo đã được gửi cho quản trị viên.";form.reset();}catch{status.textContent="Chưa gửi được báo cáo. Anh/chị vui lòng thử lại.";}finally{button.disabled=false;button.textContent="Gửi báo cáo";}});
  };
  window.LumiListingDetail={init,hydrate,hydrateContact,galleryMarkup,floorplanUrl};
  const root=document.querySelector("[data-static-listing]");if(root)init(root);
})();
