(()=>{
  const root=document.querySelector("[data-static-listing]");
  if(!root||!window.LumiMarketplace)return;
  const slug=root.dataset.listingSlug||"";
  if(!slug)return;
  const note=root.querySelector("[data-live-status]");
  const contactButtons=[...root.querySelectorAll("[data-static-phone],[data-static-zalo]")];
  const posterNode=root.querySelector("[data-static-poster] strong");
  const phoneLinks=[...root.querySelectorAll("[data-static-phone]")];
  const zaloLinks=[...root.querySelectorAll("[data-static-zalo]")];

  const initGallery=()=>{
    const track=root.querySelector(".detail-gallery-track");
    const counter=root.querySelector("[data-static-gallery-counter]");
    if(!track||!counter)return;
    const slides=[...track.querySelectorAll("figure")];
    if(!slides.length)return;
    let ticking=false;
    const update=()=>{
      ticking=false;
      const width=track.clientWidth||1;
      const index=Math.min(slides.length-1,Math.max(0,Math.round(track.scrollLeft/width)));
      counter.textContent=`${index+1}/${slides.length}`;
    };
    track.addEventListener("scroll",()=>{
      if(ticking)return;
      ticking=true;
      requestAnimationFrame(update);
    },{passive:true});
    update();
  };

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
    const poster=String(listing?.poster_name||"").trim();
    if(posterNode&&poster)posterNode.textContent=poster;
    const phone=String(listing?.contact_phone||"").trim();
    const tel=phone.replace(/[^+\d]/g,"");
    const zalo=phone.replace(/\D/g,"");
    phoneLinks.forEach(link=>{
      if(tel){link.href=`tel:${tel}`;link.textContent=phone;}
      else link.hidden=true;
    });
    zaloLinks.forEach(link=>{
      if(zalo){link.href=`https://zalo.me/${zalo}`;link.hidden=false;}
      else link.hidden=true;
    });
  };

  initGallery();
  window.LumiMarketplace.getPublicListing(slug)
    .then(listing=>{if(!listing)markUnavailable();else hydrateContact(listing);})
    .catch(()=>{});
})();