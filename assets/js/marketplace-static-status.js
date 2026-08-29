(()=>{
  const root=document.querySelector("[data-static-listing]");
  if(!root||!window.LumiMarketplace)return;
  const slug=root.dataset.listingSlug||"";
  if(!slug)return;
  const note=root.querySelector("[data-live-status]");
  const contactButtons=[...root.querySelectorAll(".detail-contact a")];

  const markUnavailable=()=>{
    let robots=document.querySelector('meta[name="robots"]');
    if(!robots){
      robots=document.createElement("meta");
      robots.name="robots";
      document.head.append(robots);
    }
    robots.content="noindex,follow";
    if(note){
      note.hidden=false;
      note.className="marketplace-live-note is-unavailable";
      note.textContent="Tin này hiện không còn trong danh sách đang giao dịch. Anh/chị vui lòng quay lại trang mua bán/cho thuê để xem nguồn hàng đang còn.";
    }
    contactButtons.forEach(link=>{
      link.removeAttribute("href");
      link.setAttribute("aria-disabled","true");
      link.classList.add("is-disabled");
    });
  };

  window.LumiMarketplace.getPublicListing(slug)
    .then(listing=>{if(!listing)markUnavailable();})
    .catch(()=>{});
})();