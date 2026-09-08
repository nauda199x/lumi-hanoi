(()=>{
  const root=document.querySelector("[data-static-listing]");
  if(!root||!window.LumiMarketplace)return;
  const slug=root.dataset.listingSlug||"";
  if(!slug)return;
  const showViewCount=count=>{
    const value=Math.max(0,Math.floor(Number(count)||0)),meta=root.querySelector(".ld-meta");
    if(!meta)return;
    let node=meta.querySelector("[data-detail-views]");
    if(!node){node=document.createElement("span");node.setAttribute("data-detail-views","");meta.append(node);}
    node.hidden=value<1;
    if(value>=1){node.textContent=`${new Intl.NumberFormat("vi-VN").format(value)} lượt xem`;node.setAttribute("aria-label",`${value} lượt xem tin`);}
  };
  const recordView=async()=>{
    const id=root.dataset.listingId||"",config=window.LUMI_MARKETPLACE_CONFIG||{};
    const base=String(config.supabaseUrl||"").replace(/\/$/,""),key=String(config.supabasePublishableKey||config.supabaseAnonKey||"");
    if(!id||!base||!key||base.includes("YOUR_PROJECT"))return;
    try{
      const response=await fetch(`${base}/rest/v1/rpc/record_listing_view`,{method:"POST",headers:{apikey:key,"Content-Type":"application/json"},body:JSON.stringify({target_listing_id:id})});
      if(!response.ok)return;
      showViewCount(await response.json());
    }catch{}
  };
  const markUnavailable=()=>{
    let robots=document.querySelector('meta[name="robots"]');
    if(!robots){robots=document.createElement("meta");robots.name="robots";document.head.append(robots);}
    robots.content="noindex,follow";
    const note=root.querySelector("[data-live-status]");
    if(note){note.hidden=false;note.textContent="Tin này không còn trong danh sách đang giao dịch. Vui lòng xem các tin mua bán hoặc cho thuê khác.";}
    root.querySelectorAll("[data-detail-phone],[data-detail-zalo],[data-static-phone],[data-static-zalo]").forEach(link=>{link.removeAttribute("href");link.setAttribute("aria-disabled","true");});
    root.querySelectorAll("[data-detail-mobile-contact],[data-report-box],.ld-contact-note").forEach(node=>node.hidden=true);
    const badge=root.querySelector("[data-detail-type]");if(badge)badge.textContent="Tin ngừng hiển thị";
  };
  window.LumiMarketplace.getPublicListing(slug)
    .then(listing=>{if(!listing)markUnavailable();else{window.LumiListingDetail?.hydrate(root,listing);recordView();}})
    .catch(()=>{}); // Keep the crawlable snapshot when the public API is offline.
})();
