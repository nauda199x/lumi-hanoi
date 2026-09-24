(()=>{
  const root=document.querySelector("[data-listing-manage]");
  if(!root||!window.LumiMarketplace)return;
  const api=window.LumiMarketplace;
  const loading=root.querySelector("[data-manage-loading]");
  const errorBox=root.querySelector("[data-manage-error]");
  const errorText=root.querySelector("[data-manage-error-text]");
  const content=root.querySelector("[data-manage-content]");
  const form=root.querySelector("[data-manage-form]");
  const statusLine=root.querySelector("[data-manage-status]");
  const statusBadge=root.querySelector("[data-manage-status-badge]");
  const codeEl=root.querySelector("[data-manage-code]");
  const phase=form?.elements.phase;
  const tower=form?.elements.tower;
  const type=form?.elements.listing_type;
  const price=form?.elements.price_display;
  const priceLabel=root.querySelector("[data-manage-price-label]");
  const images=root.querySelector("[data-manage-images]");
  const viewPublic=root.querySelector("[data-manage-view-public]");
  const doneButton=root.querySelector("[data-manage-done]");
  const actionButtons=[...root.querySelectorAll("[data-manage-action], [data-manage-save]")];
  const towerMap={Signature:["S1","S2","S3","S5","S6"],Prestige:["P1","P2"],Elite:["E1","E2"]};
  let listing=null;
  let token="";

  const statusNames={
    pending:"Chờ duyệt",
    approved:"Đang hiển thị",
    rejected:"Đã từ chối",
    expired:"Đã ẩn / hết hạn",
    sold:"Đã bán",
    rented:"Đã cho thuê"
  };

  const parseToken=()=>{
    const raw=location.hash.replace(/^#/,"");
    if(!raw)return "";
    try{
      const params=new URLSearchParams(raw);
      return params.get("token")||(/^[A-Za-z0-9_-]{43,90}$/.test(raw)?raw:"");
    }catch{return "";}
  };

  const setBusy=busy=>{
    actionButtons.forEach(button=>{button.disabled=busy;});
    if(form){
      [...form.elements].forEach(el=>{
        if(el.matches("input,select,textarea")&&el.name)el.disabled=busy;
      });
    }
  };

  const setMessage=(message,type="")=>{
    if(!statusLine)return;
    statusLine.hidden=!message;
    statusLine.className=`manage-message${type?` is-${type}`:""}`;
    statusLine.textContent=message||"";
  };

  const showError=message=>{
    loading.hidden=true;
    content.hidden=true;
    errorBox.hidden=false;
    errorText.textContent=message;
  };

  const refreshPriceUi=()=>{
    const rent=type?.value==="rent";
    if(priceLabel)priceLabel.textContent=rent?"Giá thuê (triệu/tháng)":"Giá bán (tỷ đồng)";
    if(price){
      price.step=rent?"0.1":"0.01";
      price.min=rent?"1":"0.1";
    }
    if(doneButton)doneButton.textContent=rent?"Đánh dấu đã cho thuê":"Đánh dấu đã bán";
  };

  const refreshTowers=(selected="")=>{
    if(!tower||!phase)return;
    const options=towerMap[phase.value]||[];
    tower.replaceChildren(new Option("Chọn tòa",""));
    options.forEach(value=>tower.add(new Option(value,value)));
    if(options.includes(selected))tower.value=selected;
  };

  const formatDate=value=>{
    if(!value)return "—";
    const date=new Date(value);
    return Number.isNaN(date.getTime())?"—":new Intl.DateTimeFormat("vi-VN",{day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit"}).format(date);
  };

  const renderImages=rows=>{
    if(!images)return;
    images.replaceChildren();
    const sorted=[...(rows||[])].sort((a,b)=>Number(a.sort_order||0)-Number(b.sort_order||0));
    if(!sorted.length){
      const empty=document.createElement("p");
      empty.className="manage-images-empty";
      empty.textContent="Tin này chưa có ảnh.";
      images.append(empty);
      return;
    }
    sorted.forEach((item,index)=>{
      const img=document.createElement("img");
      img.src=api.imageUrl(item.storage_path);
      img.alt=item.alt_text||`Ảnh tin đăng ${index+1}`;
      img.loading="lazy";
      images.append(img);
    });
  };

  const remember=()=>{
    try{
      const key="lumi_marketplace_manage_links_v1";
      const current=JSON.parse(localStorage.getItem(key)||"[]");
      const items=Array.isArray(current)?current:[];
      const url=location.href;
      const entry={id:listing?.id||"",code:listing?.listing_code||"",url,created_at:new Date().toISOString()};
      localStorage.setItem(key,JSON.stringify([entry,...items.filter(item=>item?.id!==entry.id)].slice(0,20)));
    }catch{}
  };

  const fill=next=>{
    listing=next;
    codeEl.textContent=listing.listing_code||"Tin đăng";
    statusBadge.textContent=statusNames[listing.status]||listing.status||"Không rõ";
    statusBadge.dataset.status=listing.status||"";
    form.elements.listing_type.value=listing.listing_type||"sale";
    form.elements.title.value=listing.title||"";
    form.elements.description.value=listing.description||"";
    form.elements.phase.value=listing.phase||"";
    refreshTowers(listing.tower||"");
    form.elements.unit_type.value=listing.unit_type||"";
    form.elements.area_sqm.value=listing.area_sqm??"";
    form.elements.floor_label.value=listing.floor_label||"";
    form.elements.furnishing.value=listing.furnishing||"";
    form.elements.available_from.value=listing.available_from||"";
    form.elements.legal_status.value=listing.legal_status||"";
    form.elements.poster_name.value=listing.poster_name||"";
    form.elements.contact_phone.value=listing.contact_phone||"";
    refreshPriceUi();
    const divider=listing.listing_type==="rent"?1_000_000:1_000_000_000;
    price.value=listing.price_vnd?String(Math.round(Number(listing.price_vnd)/divider*100)/100):"";
    root.querySelector("[data-manage-updated]").textContent=`Cập nhật gần nhất: ${formatDate(listing.updated_at)}`;
    root.querySelector("[data-manage-created]").textContent=`Đăng ngày: ${formatDate(listing.created_at)}`;
    renderImages(listing.listing_images);
    if(listing.status==="approved"){
      viewPublic.hidden=false;
      viewPublic.href=api.listingUrl(listing);
    }else{
      viewPublic.hidden=true;
      viewPublic.removeAttribute("href");
    }
    remember();
  };

  const load=async()=>{
    token=parseToken();
    if(!token){showError("Link quản lý tin chưa đầy đủ. Hãy mở đúng link đã được cấp sau khi đăng tin.");return;}
    if(!api.configured()){showError("Hệ thống dữ liệu đang tạm thời chưa kết nối.");return;}
    try{
      const result=await api.manageListing("get",token);
      if(!result?.listing)throw new Error("Không tìm thấy tin.");
      fill(result.listing);
      loading.hidden=true;
      errorBox.hidden=true;
      content.hidden=false;
    }catch(error){
      showError(error?.message||"Không mở được tin từ link này.");
    }
  };

  phase?.addEventListener("change",()=>refreshTowers());
  type?.addEventListener("change",refreshPriceUi);

  form?.addEventListener("submit",async event=>{
    event.preventDefault();
    setMessage("");
    const fd=new FormData(form);
    const listingType=String(fd.get("listing_type")||"sale");
    const priceValue=Number(fd.get("price_display"));
    if(!Number.isFinite(priceValue)||priceValue<=0){setMessage("Vui lòng kiểm tra lại mức giá.","error");return;}
    const patch={
      listing_type:listingType,
      title:String(fd.get("title")||"").trim(),
      description:String(fd.get("description")||"").trim(),
      phase:String(fd.get("phase")||""),
      tower:String(fd.get("tower")||""),
      unit_type:String(fd.get("unit_type")||""),
      area_sqm:Number(fd.get("area_sqm")),
      floor_label:String(fd.get("floor_label")||""),
      furnishing:String(fd.get("furnishing")||""),
      available_from:String(fd.get("available_from")||""),
      legal_status:String(fd.get("legal_status")||""),
      poster_name:String(fd.get("poster_name")||"").trim(),
      contact_phone:String(fd.get("contact_phone")||"").trim(),
      price_vnd:Math.round(priceValue*(listingType==="rent"?1_000_000:1_000_000_000))
    };
    setBusy(true);
    setMessage("Đang lưu thay đổi…");
    try{
      const result=await api.manageListing("update",token,{patch});
      fill(result.listing);
      setMessage(result.message||"Đã lưu. Tin đang chờ quản trị viên duyệt lại.","success");
      statusLine?.scrollIntoView({behavior:"smooth",block:"nearest"});
    }catch(error){
      setMessage(error?.message||"Chưa lưu được thay đổi.","error");
    }finally{setBusy(false);}
  });

  root.querySelector("[data-manage-copy]")?.addEventListener("click",async event=>{
    const button=event.currentTarget;
    try{
      await navigator.clipboard.writeText(location.href);
      button.textContent="Đã sao chép";
    }catch{
      const input=root.querySelector("[data-manage-link]");
      input.value=location.href;
      input.hidden=false;
      input.focus();
      input.select();
      document.execCommand("copy");
      input.hidden=true;
      button.textContent="Đã sao chép";
    }
    window.setTimeout(()=>{button.textContent="Sao chép link quản lý";},1600);
  });

  root.querySelectorAll("[data-manage-action]").forEach(button=>{
    button.addEventListener("click",async()=>{
      const action=button.dataset.manageAction;
      const message=action==="hide"
        ?"Ẩn tin này khỏi website? Anh/chị vẫn có thể mở lại link quản lý sau."
        :(listing?.listing_type==="rent"?"Đánh dấu căn này đã cho thuê?":"Đánh dấu căn này đã bán?");
      if(!window.confirm(message))return;
      setBusy(true);
      setMessage("Đang cập nhật trạng thái…");
      try{
        const result=await api.manageListing(action,token);
        fill(result.listing);
        setMessage(action==="hide"?"Đã ẩn tin.":"Đã cập nhật trạng thái giao dịch.","success");
      }catch(error){
        setMessage(error?.message||"Chưa cập nhật được trạng thái.","error");
      }finally{setBusy(false);}
    });
  });

  load();
})();
