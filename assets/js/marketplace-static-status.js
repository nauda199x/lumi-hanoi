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
    const gallery=root.querySelector(".detail-gallery");
    const track=root.querySelector(".detail-gallery-track");
    const counter=root.querySelector("[data-static-gallery-counter]");
    if(!gallery||!track||!counter)return;
    const slides=[...track.querySelectorAll("figure")];
    if(!slides.length)return;
    track.tabIndex=0;
    track.setAttribute("aria-label","Thư viện ảnh căn hộ");
    const currentIndex=()=>Math.min(slides.length-1,Math.max(0,Math.round(track.scrollLeft/(track.clientWidth||1))));
    const prev=document.createElement("button");prev.type="button";prev.className="detail-gallery-nav detail-gallery-nav--prev";prev.setAttribute("aria-label","Ảnh trước");prev.textContent="‹";
    const next=document.createElement("button");next.type="button";next.className="detail-gallery-nav detail-gallery-nav--next";next.setAttribute("aria-label","Ảnh tiếp theo");next.textContent="›";
    const update=()=>{const index=currentIndex();counter.textContent=`${index+1}/${slides.length}`;prev.disabled=index===0;next.disabled=index===slides.length-1;};
    const go=index=>{const target=Math.min(slides.length-1,Math.max(0,index));track.scrollTo({left:target*track.clientWidth,behavior:"smooth"});};
    prev.addEventListener("click",()=>go(currentIndex()-1));
    next.addEventListener("click",()=>go(currentIndex()+1));
    track.addEventListener("keydown",event=>{if(event.key==="ArrowLeft"){event.preventDefault();go(currentIndex()-1);}if(event.key==="ArrowRight"){event.preventDefault();go(currentIndex()+1);}});
    let ticking=false;
    track.addEventListener("scroll",()=>{if(ticking)return;ticking=true;requestAnimationFrame(()=>{ticking=false;update();});},{passive:true});
    window.addEventListener("resize",update,{passive:true});
    if(slides.length>1)gallery.append(prev,next);
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