(()=>{
  "use strict";
  const PREFIX="lumi-saved-listing:";
  const clean=value=>String(value??"").trim();
  const safeStorage=()=>{try{return window.localStorage}catch{return null}};
  const keys=()=>{const storage=safeStorage();if(!storage)return[];const result=[];for(let i=0;i<storage.length;i++){const key=storage.key(i);if(key?.startsWith(PREFIX))result.push(key);}return result;};
  const savedCount=()=>keys().length;
  const refreshSavedCount=()=>document.querySelectorAll("[data-saved-count]").forEach(node=>{node.textContent=String(savedCount());node.setAttribute("aria-label",`${savedCount()} tin đã lưu`);});
  const trackingMeta=node=>({surface:clean(node.closest("[data-conversion-surface]")?.dataset.conversionSurface||document.body.dataset.pageType||document.body.className),tower:clean(document.querySelector("[data-detail-tower]")?.textContent),unit:clean(document.querySelector("[data-detail-unit]")?.textContent),path:location.pathname});
  const track=(action,node)=>{const meta=trackingMeta(node||document.body);try{if(typeof window.gtag==="function")window.gtag("event","marketplace_conversion",{conversion_action:action,conversion_surface:meta.surface,listing_tower:meta.tower,listing_unit:meta.unit,page_path:meta.path});else if(Array.isArray(window.dataLayer))window.dataLayer.push({event:"marketplace_conversion",conversion_action:action,conversion_surface:meta.surface,listing_tower:meta.tower,listing_unit:meta.unit,page_path:meta.path});}catch{}};
  const snapshotCurrentListing=()=>{
    const root=document.querySelector("[data-static-listing]");
    if(!root)return null;
    const slug=clean(root.dataset.listingSlug)||clean(location.pathname.split("/").filter(Boolean).pop());
    if(!slug)return null;
    const canonical=document.querySelector('link[rel="canonical"]')?.href||location.href.split("#")[0];
    return {slug,url:canonical,title:clean(root.querySelector("[data-detail-title]")?.textContent)||document.title,price:clean(root.querySelector(".ld-price [data-detail-price],.ld-mobile-price [data-detail-price]")?.textContent),type:clean(root.querySelector("[data-detail-type]")?.textContent),tower:clean(root.querySelector("[data-detail-tower]")?.textContent),unit:clean(root.querySelector("[data-detail-unit]")?.textContent),saved_at:new Date().toISOString()};
  };
  const migrateCurrentSave=()=>{const storage=safeStorage(),item=snapshotCurrentListing();if(!storage||!item)return;const key=PREFIX+item.slug;const value=storage.getItem(key);if(value==="1")try{storage.setItem(key,JSON.stringify(item));}catch{}};
  const hydrateOwnerPost=()=>{
    const root=document.querySelector("[data-static-listing]");if(!root)return;
    const type=clean(root.querySelector("[data-detail-type]")?.textContent).toLowerCase(),tower=clean(root.querySelector("[data-detail-tower]")?.textContent);
    const hash=type.includes("thuê")?"#cho-thue":type.includes("bán")?"#mua-ban":"";
    document.querySelectorAll("[data-detail-owner-post]").forEach(link=>{link.href="/dang-tin-lumi-hanoi/"+hash;const label=tower&&tower!=="Chưa cập nhật"?`Có căn ${tower} tương tự? Đăng tin miễn phí`:"Có căn tương tự? Đăng tin miễn phí";link.textContent=label;});
  };
  document.addEventListener("click",event=>{
    const conversion=event.target.closest?.("[data-conversion-action]");if(conversion)track(conversion.dataset.conversionAction||"click",conversion);
    const save=event.target.closest?.("[data-detail-save]");if(save)setTimeout(()=>{const storage=safeStorage(),item=snapshotCurrentListing();if(!storage||!item)return;const key=PREFIX+item.slug;if(storage.getItem(key)==="1")try{storage.setItem(key,JSON.stringify(item));}catch{}refreshSavedCount();window.dispatchEvent(new CustomEvent("lumi:saved-listings-changed"));track(save.getAttribute("aria-pressed")==="true"?"save_listing":"unsave_listing",save);},0);
  });
  window.addEventListener("storage",refreshSavedCount);window.addEventListener("lumi:saved-listings-changed",refreshSavedCount);
  const init=()=>{migrateCurrentSave();hydrateOwnerPost();refreshSavedCount();};
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
  window.LumiMarketplaceConversion={savedCount,refreshSavedCount,track};
})();
