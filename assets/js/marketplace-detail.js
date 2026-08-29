(()=>{
  const root=document.querySelector("[data-listing-detail]");
  if(!root||!window.LumiMarketplace)return;
  const api=window.LumiMarketplace;
  const params=new URLSearchParams(location.search);
  const identifier=params.get("slug")||params.get("id")||"";
  const loading=root.querySelector("[data-detail-loading]");
  const missing=root.querySelector("[data-detail-missing]");
  const content=root.querySelector("[data-detail-content]");
  const text=(selector,value)=>root.querySelectorAll(selector).forEach(node=>node.textContent=value||"—");
  const showMissing=(title,copy)=>{loading.hidden=true;content.hidden=true;missing.hidden=false;text("[data-missing-title]",title);text("[data-missing-copy]",copy);};
  const galleryFor=listing=>{
    const gallery=root.querySelector("[data-detail-gallery]");
    const images=[...(listing.listing_images||[])].sort((a,b)=>Number(a.sort_order)-Number(b.sort_order));
    if(!images.length){const placeholder=document.createElement("div");placeholder.className="marketplace-state";placeholder.innerHTML='<span class="marketplace-state-mark">LH</span><div><h3>Tin chưa có ảnh</h3><p>Liên hệ người đăng để kiểm tra hình ảnh và hiện trạng căn trước khi giao dịch.</p></div>';gallery.replaceWith(placeholder);return;}
    const track=document.createElement("div");track.className="detail-gallery-track";
    images.forEach((item,index)=>{const figure=document.createElement("figure");const image=document.createElement("img");image.src=api.imageUrl(item.storage_path);image.alt=item.alt_text||`${listing.title} — ảnh ${index+1}`;image.loading=index?"lazy":"eager";image.decoding="async";figure.append(image);track.append(figure);});
    const counter=document.createElement("span");counter.className="detail-gallery-counter";counter.textContent=`1/${images.length}`;
    gallery.replaceChildren(track,counter);
    let ticking=false;track.addEventListener("scroll",()=>{if(ticking)return;ticking=true;requestAnimationFrame(()=>{const width=track.clientWidth||1;const index=Math.min(images.length-1,Math.max(0,Math.round(track.scrollLeft/width)));counter.textContent=`${index+1}/${images.length}`;ticking=false;});},{passive:true});
  };
  const render=listing=>{
    document.title=`${listing.title} | Lumi Hanoi`;
    text("[data-detail-code]",listing.listing_code);text("[data-detail-title]",listing.title);text("[data-detail-price]",api.formatCurrency(listing.price_vnd,listing.listing_type));
    text("[data-detail-type]",listing.listing_type==="rent"?"Cho thuê":"Mua bán");text("[data-detail-poster]",listing.poster_name||"Người đăng");text("[data-detail-phase]",listing.phase);text("[data-detail-tower]",listing.tower);text("[data-detail-unit]",listing.unit_type);text("[data-detail-area]",listing.area_sqm?`${Number(listing.area_sqm).toLocaleString("vi-VN")} m²`:"Liên hệ");text("[data-detail-floor]",listing.floor_label||"Liên hệ");text("[data-detail-furnishing]",listing.furnishing||"Liên hệ");text("[data-detail-description]",listing.description||"Người đăng chưa bổ sung mô tả.");
    if(listing.listing_type!=="rent"&&Number(listing.price_vnd)>0&&Number(listing.area_sqm)>0){text("[data-detail-price-per-sqm]",`~${(Number(listing.price_vnd)/Number(listing.area_sqm)/1e6).toLocaleString("vi-VN",{maximumFractionDigits:1})} tr/m²`);}else text("[data-detail-price-per-sqm]","");
    const phoneNumber=String(listing.contact_phone||"");root.querySelectorAll("[data-detail-phone]").forEach(phone=>{phone.textContent=phoneNumber?`☎ ${phoneNumber}`:"Liên hệ người đăng";phone.href=phoneNumber?`tel:${phoneNumber.replace(/[^+\d]/g,"")}`:"#";});
    const number=phoneNumber.replace(/\D/g,"");root.querySelectorAll("[data-detail-zalo]").forEach(zalo=>{zalo.href=number?`https://zalo.me/${number}`:"#";zalo.hidden=!number;});
    galleryFor(listing);root.dataset.listingId=listing.id;loading.hidden=true;missing.hidden=true;content.hidden=false;const mobileContact=root.querySelector("[data-detail-mobile-contact]");if(mobileContact)mobileContact.hidden=false;
  };
  const reportForm=root.querySelector("[data-report-form]");reportForm?.addEventListener("submit",async event=>{event.preventDefault();const button=reportForm.querySelector("button");const message=reportForm.querySelector("[data-report-status]");button.disabled=true;try{await api.createReport(root.dataset.listingId,reportForm.elements.reason.value,reportForm.elements.details.value);message.textContent="Cảm ơn anh/chị. Báo cáo đã được gửi cho quản trị viên.";reportForm.reset();}catch(error){message.textContent=`Chưa gửi được báo cáo: ${error.message}`;}finally{button.disabled=false;}});
  const load=async()=>{if(!identifier){showMissing("Không tìm thấy mã tin","Đường dẫn này chưa có mã tin hợp lệ.");return;}if(!api.configured()){showMissing("Hệ thống dữ liệu đang được kết nối","Vui lòng quay lại sau khi quỹ căn được kích hoạt.");return;}try{const listing=await api.getPublicListing(identifier);if(!listing)showMissing("Tin không còn hiển thị","Tin có thể đang chờ duyệt, đã hết hạn hoặc đã giao dịch.");else render(listing);}catch{showMissing("Không tải được tin đăng","Vui lòng kiểm tra kết nối và thử lại.");}};
  load();
})();
