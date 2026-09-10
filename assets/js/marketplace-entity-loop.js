(()=>{
  "use strict";
  const knownTower=/^(?:S[12356]|P[12]|E[12])$/i;
  const saleUnits={
    "1PN":"/mua-ban-can-ho-1-phong-ngu-lumi-hanoi/",
    "2PN":"/mua-ban-can-ho-2-phong-ngu-lumi-hanoi/",
    "3PN":"/mua-ban-can-ho-3-phong-ngu-lumi-hanoi/"
  };
  const normalizeTower=value=>{const tower=String(value||"").trim().toUpperCase();return knownTower.test(tower)?tower:"";};
  const normalizeUnit=value=>String(value||"").trim().toUpperCase();
  const marketIndexUrl=tower=>{const value=normalizeTower(tower);return value?`/gia-can-ho-lumi-hanoi/#market-index-${value.toLowerCase()}`:"/gia-can-ho-lumi-hanoi/";};
  const saleTowerUrl=tower=>{const value=normalizeTower(tower);return value?`/mua-ban-toa-${value.toLowerCase()}-lumi-hanoi/`:"/mua-ban-lumi-hanoi/";};
  const saleUnitUrl=unit=>saleUnits[normalizeUnit(unit)]||"";
  const update=root=>{
    const tower=normalizeTower(root.querySelector("[data-detail-tower]")?.textContent);
    const unit=normalizeUnit(root.querySelector("[data-detail-unit]")?.textContent);
    root.querySelectorAll("[data-detail-market-index]").forEach(link=>link.href=marketIndexUrl(tower));
    const isSale=/mua\s*bán/i.test(root.querySelector("[data-detail-type]")?.textContent||"");
    if(isSale&&tower)root.querySelectorAll("[data-detail-same-tower]").forEach(link=>link.href=saleTowerUrl(tower));
    const unitUrl=isSale?saleUnitUrl(unit):"";
    if(unitUrl)root.querySelectorAll("[data-detail-same-unit]").forEach(link=>link.href=unitUrl);
  };
  const bind=root=>{
    update(root);
    if(!window.MutationObserver)return;
    const observer=new MutationObserver(()=>update(root));
    observer.observe(root,{subtree:true,childList:true,characterData:true});
  };
  const init=()=>document.querySelectorAll(".ld-page").forEach(bind);
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
  window.LumiMarketplaceEntityLoop={marketIndexUrl,saleTowerUrl,saleUnitUrl};
})();
