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

  const setState=(title,copy,mark="0",showBenefits=false)=>{
    if(stateMark)stateMark.textContent=mark;
    if(stateTitle)stateTitle.textContent=title;
    if(stateCopy)stateCopy.textContent=copy;
    if(emptyBenefits)emptyBenefits.hidden=!showBenefits;
    if(state)state.hidden=false;
    if(grid)grid.hidden=true;
  };
  const setLoading=loading=>{
    if(skeleton)skeleton.hidden=!loading;
    if(loading){if(state)state.hidden=true;if(grid)grid.hidden=true;}
  };
  const refreshTowers=()=>{
    if(!tower)return;
    const selected=tower.value;
    const options=phase?.value?towerMap[phase.value]||[]:Object.values(towerMap).flat();
    tower.replaceChildren(new Option("Tất cả tòa",""),...options.map(value=>new Option(value,value)));
    if(options.includes(selected))tower.value=selected;
  };
  const imageFor=listing=>{
    const images=[...(listing.listing_images||[])].sort((a,b)=>Number(a.sort_order)-Number(b.sort_order));
    return images[0]||null;
  };
  const el=(tag,className,text)=>{
    const node=document.createElement(tag);
    if(className)node.className=className;
    if(text!==undefined)node.textContent=text;
    return node;
  };
  const liveDetailUrl=listing=>{
    const slug=api.cleanText(listing?.slug,120);
    const route="/tin-dang-lumi-hanoi/";
    return slug?`${route}?slug=${encodeURIComponent(slug)}`:route;
  };
  const cardFor=listing=>{
    const article=el("article","listing-card");
    const media=el("a","listing-card-media");
    media.href=api.listingUrl(listing);
    media.setAttribute("aria-label",`Xem ${listing.title}`);
    const openLive=event=>{
      if(event.defaultPrevented||event.button&&event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
      event.preventDefault();
      location.assign(liveDetailUrl(listing));
    };
    media.addEventListener("click",openLive);
    const image=imageFor(listing);
    if(image){
      const img=document.createElement("img");
      img.src=api.imageUrl(image.storage_path);
      img.alt=image.alt_text||`Ảnh căn hộ ${listing.tower||"Lumi Hanoi"}`;
      img.loading="lazy";img.decoding="async";
      media.append(img);
    }else media.append(el("span","listing-card-placeholder",`${listing.unit_type||"Căn hộ"}\n${listing.tower||"Lumi Hanoi"}`));
    const badges=el("div","listing-badges");
    if(listing.is_featured)badges.append(el("span","listing-badge listing-badge--featured","Tin nổi bật"));
    if(listing.is_featured)media.append(badges);

    const body=el("div","listing-card-body");
    const price=el("div","listing-card-price");
    price.append(el("strong","",api.formatCurrency(listing.price_vnd,listing.listing_type)));
    price.append(el("span","",listing.listing_code||""));
    const meta=el("div","listing-card-meta");
    [listing.tower,listing.unit_type,listing.area_sqm?`${Number(listing.area_sqm).toLocaleString("vi-VN")} m²`:null,listing.floor_label].filter(Boolean).forEach(value=>meta.append(el("span","",value)));
    const title=el("h3");
    const link=el("a","",listing.title);
    link.href=media.href;
    link.addEventListener("click",openLive);
    title.append(link);
    body.append(price,meta,title);article.append(media,body);
    return article;
  };
  const filterValues=()=>{
    const values=Object.fromEntries(new FormData(form||document.createElement("form")).entries());
    return {keyword:values.keyword||"",phase:values.phase||"",tower:values.tower||"",bedroom:values.bedroom||"",maxPrice:values.max_price||""};
  };
  const hasFilters=values=>Object.values(values).some(value=>String(value||"").trim());
  const load=async()=>{
    if(!api.configured()){
      if(count)count.textContent="Đang kết nối";
      setState("Quỹ căn đang được kết nối","Hệ thống đang kết nối dữ liệu giao dịch. Vui lòng thử lại sau ít phút.","LH",false);
      return;
    }
    setLoading(true);
    try{
      const filters=filterValues();
      const listings=await api.listPublic(type,filters);
      grid.replaceChildren(...listings.map(cardFor));
      if(count)count.textContent=`${listings.length} tin đăng`;
      if(listings.length){
        grid.hidden=false;
        if(state)state.hidden=true;
      }else if(hasFilters(filters)){
        setState("Không tìm thấy căn phù hợp","Thử bỏ bớt điều kiện lọc hoặc quay lại sau khi có tin mới.","0",false);
      }else{
        setState(
          `Chưa có tin đăng ${type==="rent"?"cho thuê":"mua bán"}`,
          "Anh/chị có căn cần giao dịch có thể đăng miễn phí. Tin chỉ xuất hiện sau khi quản trị viên duyệt.",
          "0",
          true
        );
      }
    }catch(error){
      if(count)count.textContent="Chưa tải được dữ liệu";
      setState("Không thể tải danh sách căn",error.status===0?"Vui lòng kiểm tra kết nối mạng và thử lại.":"Dữ liệu tạm thời chưa sẵn sàng. Vui lòng thử lại sau.","!",false);
    }finally{setLoading(false);}
  };

  let timer;
  const scheduleLoad=delay=>{clearTimeout(timer);timer=setTimeout(load,delay);};
  form?.addEventListener("input",event=>{
    if(event.target===phase)refreshTowers();
    scheduleLoad(event.target.name==="keyword"?320:40);
  });
  form?.addEventListener("change",event=>{
    if(event.target===phase)refreshTowers();
    scheduleLoad(30);
  });
  form?.addEventListener("reset",()=>setTimeout(()=>{refreshTowers();load();},0));
  refreshTowers();load();
})();