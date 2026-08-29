(()=>{
  const root=document.querySelector("[data-listing-detail]");
  if(!root||!window.LumiMarketplace)return;
  const api=window.LumiMarketplace;
  const params=new URLSearchParams(location.search);
  const identifier=params.get("slug")||params.get("id")||"";
  const loading=root.querySelector("[data-detail-loading]");
  const missing=root.querySelector("[data-detail-missing]");
  const content=root.querySelector("[data-detail-content]");
  const text=(selector,value)=>{const node=root.querySelector(selector);if(node)node.textContent=value||"—";};
  const showMissing=(title,copy)=>{
    loading.hidden=true;content.hidden=true;missing.hidden=false;
    text("[data-missing-title]",title);text("[data-missing-copy]",copy);
  };
  const galleryFor=listing=>{
    const gallery=root.querySelector("[data-detail-gallery]");
    const images=[...(listing.listing_images||[])].sort((a,b)=>Number(a.sort_order)-Number(b.sort_order));
    if(!images.length){
      const placeholder=document.createElement("div");placeholder.className="marketplace-state";
      const mark=document.createElement("span");mark.className="marketplace-state-mark";mark.textContent="LH";
      const copy=document.createElement("div");const heading=document.createElement("h3");heading.textContent="Tin chưa có ảnh";const paragraph=document.createElement("p");paragraph.textContent="Liên hệ người đăng để kiểm tra hình ảnh và hiện trạng căn trước khi giao dịch.";copy.append(heading,paragraph);placeholder.append(mark,copy);gallery.replaceWith(placeholder);return;
    }
    gallery.replaceChildren(...images.map((item,index)=>{
      const figure=document.createElement("figure");const image=document.createElement("img");image.src=api.imageUrl(item.storage_path);image.alt=item.alt_text||`${listing.title} — ảnh ${index+1}`;image.loading=index?"lazy":"eager";image.decoding="async";figure.append(image);return figure;
    }));
  };
  const render=listing=>{
    document.title=`${listing.title} | Lumi Hanoi`;
    text("[data-detail-code]",listing.listing_code);text("[data-detail-title]",listing.title);text("[data-detail-price]",api.formatCurrency(listing.price_vnd,listing.listing_type));
    text("[data-detail-type]",listing.listing_type==="rent"?"Cho thuê":"Mua bán");text("[data-detail-poster]",listing.poster_name||"Người đăng");text("[data-detail-phase]",listing.phase);text("[data-detail-tower]",listing.tower);text("[data-detail-unit]",listing.unit_type);text("[data-detail-area]",listing.area_sqm?`${Number(listing.area_sqm).toLocaleString("vi-VN")} m²`:"Liên hệ");text("[data-detail-floor]",listing.floor_label||"Liên hệ");text("[data-detail-furnishing]",listing.furnishing||"Liên hệ");text("[data-detail-description]",listing.description||"Người đăng chưa bổ sung mô tả.");
    const phone=root.querySelector("[data-detail-phone]");if(phone){phone.textContent=listing.contact_phone;phone.href=`tel:${String(listing.contact_phone||"").replace(/[^+\d]/g,"")}`;}
    const zalo=root.querySelector("[data-detail-zalo]");if(zalo){const number=String(listing.contact_phone||"").replace(/\D/g,"");zalo.href=number?`https://zalo.me/${number}`:"#";zalo.hidden=!number;}
    galleryFor(listing);root.dataset.listingId=listing.id;loading.hidden=true;missing.hidden=true;content.hidden=false;
  };
  const reportForm=root.querySelector("[data-report-form]");
  reportForm?.addEventListener("submit",async event=>{
    event.preventDefault();const button=reportForm.querySelector("button");const message=reportForm.querySelector("[data-report-status]");button.disabled=true;
    try{await api.createReport(root.dataset.listingId,reportForm.elements.reason.value,reportForm.elements.details.value);message.textContent="Cảm ơn anh/chị. Báo cáo đã được gửi cho quản trị viên.";reportForm.reset();}
    catch(error){message.textContent=`Chưa gửi được báo cáo: ${error.message}`;}
    finally{button.disabled=false;}
  });
  const load=async()=>{
    if(!identifier){showMissing("Không tìm thấy mã tin","Đường dẫn này chưa có mã tin hợp lệ.");return;}
    if(!api.configured()){showMissing("Hệ thống dữ liệu đang được kết nối","Vui lòng quay lại sau khi quỹ căn được kích hoạt.");return;}
    try{const listing=await api.getPublicListing(identifier);if(!listing)showMissing("Tin không còn hiển thị","Tin có thể đang chờ duyệt, đã hết hạn hoặc đã giao dịch.");else render(listing);}
    catch{showMissing("Không tải được tin đăng","Vui lòng kiểm tra kết nối và thử lại.");}
  };
  load();
})();
