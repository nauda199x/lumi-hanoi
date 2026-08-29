(()=>{
  const form=document.querySelector("[data-marketplace-submit]");
  if(!form||!window.LumiMarketplace)return;
  const api=window.LumiMarketplace;
  const submit=form.querySelector('[type="submit"]');
  const status=form.querySelector("[data-form-status]");
  const filesInput=form.querySelector('[name="images"]');
  const previews=form.querySelector("[data-image-previews]");
  const phase=form.querySelector('[name="phase"]');
  const tower=form.querySelector('[name="tower"]');
  const priceLabel=form.querySelector("[data-price-label]");
  const availableField=form.querySelector("[data-available-field]");
  const availableLabel=form.querySelector("[data-available-label]");
  const availableInput=form.elements.available_from;
  const legalField=form.querySelector("[data-legal-field]");
  const legalInput=form.elements.legal_status;
  const towerMap={Signature:["S1","S2","S3","S5","S6"],Prestige:["P1","P2"],Elite:["E1","E2"]};
  let previewUrls=[];

  const showStatus=(message,type="")=>{
    status.hidden=false;status.textContent=message;status.className=`form-status${type?` is-${type}`:""}`;
    status.scrollIntoView({behavior:"smooth",block:"nearest"});
  };
  const clearStatus=()=>{status.hidden=true;status.textContent="";};
  const listingType=()=>form.querySelector('[name="listing_type"]:checked')?.value||"sale";
  const refreshType=()=>{
    const rent=listingType()==="rent";
    if(priceLabel)priceLabel.textContent=rent?"Giá thuê mỗi tháng (đồng)":"Giá bán mong muốn (đồng)";
    if(availableLabel)availableLabel.textContent="Ngày có thể vào ở";
    if(availableField)availableField.hidden=!rent;
    if(availableInput)availableInput.disabled=!rent;
    if(legalField)legalField.hidden=rent;
    if(legalInput)legalInput.disabled=rent;
  };
  const refreshTowers=()=>{
    const selected=tower.value;
    const options=towerMap[phase.value]||[];
    tower.replaceChildren(new Option("Chọn tòa",""),...options.map(value=>new Option(value,value)));
    if(options.includes(selected))tower.value=selected;
  };
  const clearPreviews=()=>{previewUrls.forEach(URL.revokeObjectURL);previewUrls=[];previews.replaceChildren();};
  const validateFiles=files=>{
    const max=Number(api.config.maxImages||12),maxBytes=Number(api.config.maxImageBytes||5*1024*1024);
    if(!files.length)throw new Error("Vui lòng chọn ít nhất 1 ảnh căn hộ.");
    if(files.length>max)throw new Error(`Chỉ được tải tối đa ${max} ảnh.`);
    files.forEach(file=>{
      if(!["image/jpeg","image/png","image/webp"].includes(file.type))throw new Error(`Ảnh “${file.name}” không đúng định dạng JPG, PNG hoặc WebP.`);
      if(file.size>maxBytes)throw new Error(`Ảnh “${file.name}” vượt quá ${Math.round(maxBytes/1024/1024)} MB.`);
    });
  };
  const renderPreviews=()=>{
    clearPreviews();
    const files=[...(filesInput.files||[])];
    try{validateFiles(files);clearStatus();}catch(error){filesInput.value="";showStatus(error.message,"error");return;}
    files.forEach((file,index)=>{
      const figure=document.createElement("figure");figure.className="image-preview";
      const image=document.createElement("img");const url=URL.createObjectURL(file);previewUrls.push(url);
      image.src=url;image.alt=`Ảnh xem trước ${index+1}`;
      const label=document.createElement("span");label.textContent=index===0?"Ảnh đại diện":String(index+1);
      figure.append(image,label);previews.append(figure);
    });
  };
  const value=name=>api.cleanText(form.elements[name]?.value||"",name==="description"?3000:300);
  const numeric=name=>{
    const parsed=Number(form.elements[name]?.value||0);
    return Number.isFinite(parsed)&&parsed>0?parsed:null;
  };
  const payload=()=>{
    const unitType=value("unit_type");
    const bedroomMatch=unitType.match(/^(\d)/);
    return {
      listing_type:listingType(),poster_name:value("poster_name"),contact_phone:value("contact_phone"),
      phase:value("phase"),tower:value("tower"),unit_type:unitType,bedroom_count:bedroomMatch?Number(bedroomMatch[1]):null,area_sqm:numeric("area_sqm"),floor_label:value("floor_label")||null,
      price_vnd:numeric("price_vnd"),furnishing:value("furnishing")||null,available_from:listingType()==="rent"?(value("available_from")||null):null,legal_status:listingType()==="sale"?(value("legal_status")||null):null,
      title:value("title"),description:value("description"),contact_public:Boolean(form.elements.contact_public?.checked)
    };
  };

  form.addEventListener("change",event=>{
    if(event.target.name==="listing_type")refreshType();
    if(event.target===phase)refreshTowers();
    if(event.target===filesInput)renderPreviews();
  });
  form.addEventListener("submit",async event=>{
    event.preventDefault();clearStatus();
    if(form.elements.website?.value){showStatus("Tin của anh/chị đã được tiếp nhận.","success");return;}
    if(!form.reportValidity())return;
    if(!api.configured()){showStatus("Hệ thống dữ liệu đang được kết nối. Vui lòng quay lại sau ít phút.","error");return;}
    const files=[...(filesInput.files||[])];
    try{validateFiles(files);}catch(error){showStatus(error.message,"error");return;}
    submit.disabled=true;submit.textContent="Đang gửi tin…";
    try{
      const listing=await api.createListing(payload());
      let uploaded=0;
      for(let index=0;index<files.length;index++){
        try{
          submit.textContent=`Đang tải ảnh ${index+1}/${files.length}…`;
          const path=await api.uploadImage(listing.id,files[index],index);
          await api.addListingImage(listing.id,path,index,`${listing.title} — ảnh ${index+1}`);
          uploaded++;
        }catch(error){console.warn("Image upload failed",error);}
      }
      const imageNote=files.length&&uploaded<files.length?` Đã tải ${uploaded}/${files.length} ảnh; quản trị viên sẽ liên hệ nếu cần bổ sung.`:"";
      showStatus(`Đã nhận tin ${listing.listing_code}. Tin đang chờ quản trị viên duyệt và chưa hiển thị công khai.${imageNote}`,"success");
      form.reset();clearPreviews();refreshType();refreshTowers();
    }catch(error){
      showStatus(error.status===429?"Anh/chị gửi quá nhanh. Vui lòng chờ rồi thử lại.":`Chưa gửi được tin: ${error.message}`,"error");
    }finally{submit.disabled=false;submit.textContent="Gửi tin chờ duyệt";}
  });
  const preset=location.hash.replace(/^#/,"");
  if(preset==="cho-thue")form.querySelector('[name="listing_type"][value="rent"]').checked=true;
  if(preset==="mua-ban")form.querySelector('[name="listing_type"][value="sale"]').checked=true;
  refreshType();refreshTowers();
})();
