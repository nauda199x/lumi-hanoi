(()=>{
  const root=document.querySelector("[data-static-listing]");
  if(!root||!window.LumiMarketplace)return;
  const slug=root.dataset.listingSlug||"";
  if(!slug)return;
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
    .then(listing=>{if(!listing)markUnavailable();else window.LumiListingDetail?.hydrate(root,listing);})
    .catch(()=>{}); // Keep the crawlable snapshot when the public API is offline.
})();
