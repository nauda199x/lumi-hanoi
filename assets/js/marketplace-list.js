(()=>{
  const root=document.querySelector("[data-marketplace-list]");
  if(!root||!window.LumiMarketplace)return;
  const api=window.LumiMarketplace;
  const type=root.dataset.listingType==="rent"?"rent":"sale";
  const grid=root.querySelector("[data-listing-grid]");
  const state=root.querySelector("[data-listing-state]");
  const stateMark=state?.querySelector("[data-state-mark]");
  const stateTitle=state?.querySelector("[data-state-title]");
  const stateCopy=state?.querySelector("[data-state-copy]");
  const emptyBenefits=state?.querySelector("[data-empty-benefits]");
  const skeleton=root.querySelector("[data-listing-skeleton]");
  const count=root.querySelector("[data-listing-count]");
  const form=root.querySelector("[data-listing-filters]");
  const phase=form?.querySelector('[name="phase"]');
  const tower=form?.querySelector('[name="tower"]');
  const towerMap={Signature:["S1","S2","S3","S5","S6"],Prestige:["P1","P2"],Elite:["E1","E2"]};
  const mobileQuery=window.matchMedia("(max-width:700px)");
  const pageSize=()=>mobileQuery.matches?8:10;
  let sourceRows=[];
  let filteredRows=[];
  let visibleCount=0;
  let timer=0;

  const el=(tag,className,text)=>{
    const node=document.createElement(tag);
    if(className)node.className=className;
    if(text!==undefined)node.textContent=text;
    return node;
  };
  const loadMoreWrap=el("div","marketplace-load-more");
  const loadMoreStatus=el("span","marketplace-load-more-status","");
  const loadMoreButton=el("button","btn","Xem thêm tin");
  loadMoreButton.type="button";
  loadMoreWrap.append(loadMoreStatus,loadMoreButton);
  grid.insertAdjacentElement("afterend",loadMoreWrap);
  loadMoreWrap.hidden=true;

  const setState=(title,copy,mark="0",showBenefits=false)=>{
    if(stateMark)stateMark.textContent=mark;
    if(stateTitle)stateTitle.textContent=title;
    if(stateCopy)stateCopy.textContent=copy;
    if(emptyBenefits)emptyBenefits.hidden=!showBenefits;
    if(state)state.hidden=false;
    if(grid)grid.hidden=true;
    loadMoreWrap.hidden=true;
  };
  const setLoading=loading=>{
    if(skeleton)skeleton.hidden=!loading;
    if(loading){if(state)state.hidden=true;if(grid)grid.hidden=true;loadMoreWrap.hidden=true;}
  };
  const refreshTowers=()=>{
    if(!tower)return;
    const selected=tower.value;
    const options=phase?.value?towerMap[phase.value]||[]:Object.values(towerMap).flat();
    tower.replaceChildren(new Option("Tất cả tòa",""),...options.map(value=>new Option(value,value)));
    if(options.includes(selected))tower.value=selected;
  };
  const applyQueryFilters=()=>{
    const params=new URLSearchParams(location.search);
    const hashParams=new URLSearchParams(location.hash.replace(/^#/,""));
    const requestedTower=String(params.get("tower")||hashParams.get("tower")||"").trim().toUpperCase();
    const allTowers=Object.values(towerMap).flat();
    const inferredPhase=Object.entries(towerMap).find(([,items])=>items.includes(requestedTower))?.[0]||"";
    if(phase&&inferredPhase)phase.value=inferredPhase;
    refreshTowers();
    if(tower&&allTowers.includes(requestedTower))tower.value=requestedTower;
  };
  const liveDetailUrl=listing=>{
    const slug=api.cleanText(listing?.slug,120);
    const route="/tin-dang-lumi-hanoi/";
    return slug?`${route}?slug=${encodeURIComponent(slug)}`:route;
  };
  const openLiveFor=listing=>event=>{
    if(event.defaultPrevented||(event.button&&event.button!==0)||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
    event.preventDefault();
    location.assign(liveDetailUrl(listing));
  };
  const imagesFor=listing=>[...(listing.listing_images||[])].sort((a,b)=>Number(a.sort_order)-Number(b.sort_order));
  const formatArea=value=>Number(value)>0?`${Number(value).toLocaleString("vi-VN",{maximumFractionDigits:1})} m²`:"";
  const pricePerSqm=listing=>{
    if(listing.listing_type!=="sale"||!Number(listing.price_vnd)||!Number(listing.area_sqm))return "";
    const ppm=Number(listing.price_vnd)/Number(listing.area_sqm)/1_000_000;
    return `${ppm.toLocaleString("vi-VN",{maximumFractionDigits:1})} tr/m²`;
  };
  const timeAgo=value=>{
    const date=new Date(value||"");
    if(Number.isNaN(date.getTime()))return "";
    const days=Math.max(0,Math.floor((Date.now()-date.getTime())/86400000));
    if(days===0)return "Đăng hôm nay";
    if(days===1)return "Đăng hôm qua";
    if(days<30)return `Đăng ${days} ngày trước`;
    return `Đăng ${date.toLocaleDateString("vi-VN")}`;
  };
  const initials=name=>{
    const parts=String(name||"").trim().split(/\s+/).filter(Boolean);
    if(!parts.length)return "LH";
    return parts.slice(-2).map(part=>part.charAt(0).toUpperCase()).join("");
  };

  const cardFor=listing=>{
    const article=el("article","listing-card listing-card--marketplace");
    if(listing.is_featured)article.classList.add("is-featured");
    const cleanUrl=api.listingUrl(listing);
    const openLive=openLiveFor(listing);

    const media=el("div","listing-card-media");
    const track=el("div","listing-card-gallery-track");
    const images=imagesFor(listing);
    if(images.length){
      images.forEach((item,index)=>{
        const slide=el("a","listing-card-slide");
        slide.href=cleanUrl;
        slide.setAttribute("aria-label",`Xem ${listing.title} — ảnh ${index+1}`);
        slide.addEventListener("click",openLive);
        const img=document.createElement("img");
        img.src=api.imageUrl(item.storage_path);
        img.alt=item.alt_text||`Ảnh ${index+1} — ${listing.title}`;
        img.loading="lazy";img.decoding="async";
        slide.append(img);track.append(slide);
      });
    }else{
      const slide=el("a","listing-card-slide listing-card-placeholder",`${listing.unit_type||"Căn hộ"}\n${listing.tower||"Lumi Hanoi"}`);
      slide.href=cleanUrl;slide.addEventListener("click",openLive);track.append(slide);
    }
    media.append(track);
    if(images.length>1){
      media.append(el("span","listing-card-image-count",`▧ ${images.length} ảnh`));
      const dots=el("div","listing-card-gallery-dots");
      const dotCount=Math.min(images.length,5);
      for(let i=0;i<dotCount;i++){
        const dot=el("button","listing-card-gallery-dot"+(i===0?" is-active":""));
        dot.type="button";dot.tabIndex=-1;dot.setAttribute("aria-hidden","true");dots.append(dot);
      }
      let raf=0;
      track.addEventListener("scroll",()=>{
        cancelAnimationFrame(raf);
        raf=requestAnimationFrame(()=>{
          const index=Math.min(dotCount-1,Math.max(0,Math.round(track.scrollLeft/Math.max(1,track.clientWidth))));
          [...dots.children].forEach((dot,i)=>dot.classList.toggle("is-active",i===index));
        });
      },{passive:true});
      media.append(dots);
    }
    if(listing.is_featured){
      const badges=el("div","listing-badges");
      badges.append(el("span","listing-badge listing-badge--featured","Tin nổi bật"));
      media.append(badges);
    }

    const body=el("div","listing-card-body");
    const content=el("div","listing-card-content");
    const title=el("h3");
    const titleLink=el("a","",listing.title);
    titleLink.href=cleanUrl;titleLink.addEventListener("click",openLive);title.append(titleLink);

    const facts=el("div","listing-card-facts");
    facts.append(el("strong","listing-card-fact-price",api.formatCurrency(listing.price_vnd,listing.listing_type)));
    [
      formatArea(listing.area_sqm),
      pricePerSqm(listing),
      listing.unit_type,
      listing.floor_label?("Tầng "+listing.floor_label):""
    ].filter(Boolean).forEach(value=>facts.append(el("span","",value)));

    const location=el("div","listing-card-location");
    location.append(el("span","listing-card-location-mark","⌖"));
    location.append(el("span","",["Lumi Hanoi",listing.phase,listing.tower].filter(Boolean).join(" · ")));

    const description=el("p","listing-card-description",String(listing.description||"").trim()||"Xem chi tiết căn hộ, hình ảnh và thông tin liên hệ người đăng.");
    content.append(title,facts,location,description);

    const footer=el("div","listing-card-footer");
    const poster=el("div","listing-card-poster");
    poster.append(el("span","listing-card-avatar",initials(listing.poster_name)));
    const posterText=el("span","listing-card-poster-text");
    posterText.append(el("strong","",listing.poster_name||"Người đăng"));
    posterText.append(el("small","",timeAgo(listing.approved_at||listing.created_at)));
    poster.append(posterText);

    const actions=el("div","listing-card-actions");
    const phone=String(listing.contact_phone||"").trim();
    const tel=phone.replace(/[^+\d]/g,"");
    const zalo=phone.replace(/\D/g,"");
    if(tel){
      const call=el("a","listing-card-action listing-card-action--call",mobileQuery.matches?"Gọi":`☎ ${phone}`);
      call.href=`tel:${tel}`;call.setAttribute("aria-label",`Gọi người đăng ${phone}`);actions.append(call);
    }
    if(zalo){
      const zaloLink=el("a","listing-card-action listing-card-action--zalo","Zalo");
      zaloLink.href=`https://zalo.me/${zalo}`;zaloLink.target="_blank";zaloLink.rel="noopener";actions.append(zaloLink);
    }
    const view=el("a","listing-card-action listing-card-action--view","Xem chi tiết");
    view.href=cleanUrl;view.addEventListener("click",openLive);actions.append(view);

    footer.append(poster,actions);
    body.append(content,footer);
    article.append(media,body);
    return article;
  };

  const filterValues=()=>{
    const values=Object.fromEntries(new FormData(form||document.createElement("form")).entries());
    return {keyword:values.keyword||"",phase:values.phase||"",tower:values.tower||"",bedroom:values.bedroom||"",maxPrice:values.max_price||"",area:values.area||""};
  };
  const activeFilterCount=values=>["keyword","phase","tower","bedroom","maxPrice","area"].filter(key=>String(values[key]||"").trim()).length;
  const applyClientFilters=(rows,filters)=>{
    let next=[...rows];
    if(filters.area){
      const [min,max]=String(filters.area).split("-").map(Number);
      next=next.filter(row=>{
        const area=Number(row.area_sqm||0);
        return area>=Number(min||0)&&(!max||area<=max);
      });
    }
    return next;
  };

  const renderMore=(reset=false)=>{
    if(reset){grid.replaceChildren();visibleCount=0;}
    const next=Math.min(filteredRows.length,visibleCount+pageSize());
    const fragment=document.createDocumentFragment();
    filteredRows.slice(visibleCount,next).forEach(listing=>fragment.append(cardFor(listing)));
    grid.append(fragment);visibleCount=next;
    if(count)count.textContent=`${filteredRows.length} tin đăng`;
    loadMoreStatus.textContent=filteredRows.length?`Đang hiển thị ${visibleCount}/${filteredRows.length} tin`:"";
    const remaining=Math.max(0,filteredRows.length-visibleCount);
    loadMoreButton.textContent=`Xem thêm ${Math.min(pageSize(),remaining)} tin`;
    loadMoreButton.hidden=!remaining;
    loadMoreWrap.hidden=filteredRows.length<=pageSize();
  };
  loadMoreButton.addEventListener("click",()=>renderMore(false));

  const mobileControls=el("div","marketplace-mobile-controls");
  const mobileFilterButton=el("button","marketplace-mobile-filter");
  mobileFilterButton.type="button";
  const mobileFilterLabel=el("span","marketplace-mobile-filter-label","Bộ lọc");
  const mobileFilterMeta=el("span","marketplace-mobile-filter-meta","");
  mobileFilterButton.append(mobileFilterLabel,mobileFilterMeta);
  mobileControls.append(mobileFilterButton);
  form.insertAdjacentElement("beforebegin",mobileControls);

  const quickFilters=el("div","marketplace-quick-filters");
  [["","Tất cả"],["1PN","1PN"],["2PN","2PN"],["3PN","3PN"],["Shop chân đế","Shop"]].forEach(([value,label])=>{
    const button=el("button","marketplace-quick-filter",label);
    button.type="button";button.dataset.value=value;
    button.addEventListener("click",()=>{
      const bedroom=form?.querySelector('[name="bedroom"]');
      if(!bedroom)return;
      bedroom.value=value;
      bedroom.dispatchEvent(new Event("change",{bubbles:true}));
    });
    quickFilters.append(button);
  });
  mobileControls.insertAdjacentElement("afterend",quickFilters);

  const sheetHead=el("div","marketplace-filter-sheet-head");
  sheetHead.append(el("strong","","Bộ lọc căn hộ"));
  const closeFilters=el("button","marketplace-filter-close","×");closeFilters.type="button";closeFilters.setAttribute("aria-label","Đóng bộ lọc");sheetHead.append(closeFilters);
  form.prepend(sheetHead);
  const applyFilters=el("button","btn btn-primary marketplace-filter-apply","Xem kết quả");applyFilters.type="button";form.append(applyFilters);
  const backdrop=el("button","marketplace-filter-backdrop");backdrop.type="button";backdrop.setAttribute("aria-label","Đóng bộ lọc");root.append(backdrop);

  const openFilterSheet=()=>{form.classList.add("is-mobile-open");backdrop.classList.add("is-visible");document.body.classList.add("marketplace-filter-open");};
  const closeFilterSheet=()=>{form.classList.remove("is-mobile-open");backdrop.classList.remove("is-visible");document.body.classList.remove("marketplace-filter-open");};
  mobileFilterButton.addEventListener("click",openFilterSheet);
  closeFilters.addEventListener("click",closeFilterSheet);
  applyFilters.addEventListener("click",closeFilterSheet);
  backdrop.addEventListener("click",closeFilterSheet);
  window.addEventListener("keydown",event=>{if(event.key==="Escape")closeFilterSheet();});

  const syncMobileControls=()=>{
    const values=filterValues();
    const n=activeFilterCount(values);
    mobileFilterMeta.textContent=n?String(n):"";
    [...quickFilters.children].forEach(button=>button.classList.toggle("is-active",button.dataset.value===String(values.bedroom||"")));
  };

  const showRows=()=>{
    const filters=filterValues();
    filteredRows=applyClientFilters(sourceRows,filters);
    syncMobileControls();
    applyFilters.textContent=filteredRows.length?`Xem ${filteredRows.length} căn`:"Xem kết quả";
    if(filteredRows.length){
      grid.hidden=false;if(state)state.hidden=true;renderMore(true);
    }else if(sourceRows.length||activeFilterCount(filters)){
      setState("Không tìm thấy căn phù hợp","Điều chỉnh bộ lọc hoặc thay đổi khoảng giá, diện tích để mở rộng kết quả.","0",false);
    }else{
      setState(`Chưa có tin đăng ${type==="rent"?"cho thuê":"mua bán"}`,"Nếu có căn cần mua bán hoặc cho thuê, anh/chị có thể đăng tin miễn phí. Tin được kiểm tra trước khi công khai.","0",true);
    }
  };

  const load=async()=>{
    if(!api.configured()){
      if(count)count.textContent="Đang kết nối";
      setState("Dữ liệu giao dịch đang được cập nhật","Hệ thống đang cập nhật danh sách tin giao dịch. Vui lòng quay lại sau ít phút.","LH",false);
      return;
    }
    setLoading(true);
    try{
      sourceRows=await api.listPublic(type,filterValues());
      showRows();
    }catch(error){
      if(count)count.textContent="Chưa tải được dữ liệu";
      setState("Chưa thể tải danh sách căn hộ",error.status===0?"Vui lòng kiểm tra kết nối mạng và tải lại trang.":"Dữ liệu tạm thời chưa sẵn sàng. Vui lòng quay lại sau.","!",false);
    }finally{setLoading(false);}
  };

  const scheduleLoad=delay=>{clearTimeout(timer);timer=setTimeout(load,delay);};
  form?.addEventListener("input",event=>{
    if(event.target===phase)refreshTowers();
    syncMobileControls();
    scheduleLoad(event.target.name==="keyword"?320:60);
  });
  form?.addEventListener("change",event=>{
    if(event.target===phase)refreshTowers();
    syncMobileControls();
    if(event.target.name==="area"){showRows();return;}
    scheduleLoad(30);
  });
  form?.addEventListener("reset",()=>setTimeout(()=>{refreshTowers();syncMobileControls();load();},0));
  mobileQuery.addEventListener?.("change",()=>{if(filteredRows.length)renderMore(true);});
  applyQueryFilters();syncMobileControls();load();
})();