(()=>{
  const root=document.querySelector("[data-static-listing]");
  if(!root||!window.LumiMarketplace)return;
  const slug=root.dataset.listingSlug||"";
  if(!slug)return;
  const note=root.querySelector("[data-live-status]");
  const contactButtons=[...root.querySelectorAll(".detail-contact a")];
  const phoneLink=root.querySelector("[data-static-phone]");
  const zaloLink=root.querySelector("[data-static-zalo]");

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

  const hydrateContact=listing=>{
    const phone=String(listing?.contact_phone||"").trim();
    const tel=phone.replace(/[^+\d]/g,"");
    const zalo=phone.replace(/\D/g,"");
    if(phoneLink){
      if(tel){phoneLink.href=`tel:${tel}`;phoneLink.textContent=phone;}
      else{phoneLink.hidden=true;}
    }
    if(zaloLink){
      if(zalo){zaloLink.href=`https://zalo.me/${zalo}`;zaloLink.hidden=false;}
      else{zaloLink.hidden=true;}
    }
  };

  window.LumiMarketplace.getPublicListing(slug)
    .then(listing=>{if(!listing)markUnavailable();else hydrateContact(listing);})
    .catch(()=>{});
})();