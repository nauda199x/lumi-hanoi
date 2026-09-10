(()=>{
  "use strict";
  const known=/^(?:S[12356]|P[12]|E[12])$/i;
  const normalize=value=>{const tower=String(value||"").trim().toUpperCase();return known.test(tower)?tower:"";};
  const marketIndexUrl=tower=>{const value=normalize(tower);return value?`/gia-can-ho-lumi-hanoi/#market-index-${value.toLowerCase()}`:"/gia-can-ho-lumi-hanoi/";};
  const saleTowerUrl=tower=>{const value=normalize(tower);return value?`/mua-ban-toa-${value.toLowerCase()}-lumi-hanoi/`:"/mua-ban-lumi-hanoi/";};
  const update=root=>{
    const tower=normalize(root.querySelector("[data-detail-tower]")?.textContent);
    root.querySelectorAll("[data-detail-market-index]").forEach(link=>link.href=marketIndexUrl(tower));
    const isSale=/mua\s*bán/i.test(root.querySelector("[data-detail-type]")?.textContent||"");
    if(isSale&&tower)root.querySelectorAll("[data-detail-same-tower]").forEach(link=>link.href=saleTowerUrl(tower));
  };
  const bind=root=>{
    update(root);
    if(!window.MutationObserver)return;
    const observer=new MutationObserver(()=>update(root));
    observer.observe(root,{subtree:true,childList:true,characterData:true});
  };
  const init=()=>document.querySelectorAll(".ld-page").forEach(bind);
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
  window.LumiMarketplaceEntityLoop={marketIndexUrl,saleTowerUrl};
})();
