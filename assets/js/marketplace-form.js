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
  const directImageTypes=new Set(["image/jpeg","image/png","image/webp"]);
  const iphoneImageTypes=new Set(["image/heic","image/heif"]);
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

  const fileKind=file=>{
    const type=String(file.type||"").toLowerCase();
    const name=String(file.name||"").toLowerCase();
    if(directImageTypes.has(type)||/\.(jpe?g|png|webp)$/.test(name))return "direct";
    if(iphoneImageTypes.has(type)||/\.(heic|heif)$/.test(name))return "iphone";
    return "";
  };
  const validateFileSelection=files=>{
    const max=Number(api.config.maxImages||12);
    if(!files.length)throw new Error("Vui lòng chọn ít nhất 1 ảnh căn hộ.");
    if(files.length>max)throw new Error(`Chỉ được tải tối đa ${max} ảnh.`);
    files.forEach(file=>{
      if(!fileKind(file))throw new Error(`Ảnh “${file.name}” chưa được hỗ trợ. Vui lòng dùng JPG, PNG, WebP, HEIC hoặc HEIF.`);
    });
  };
  const blobFromCanvas=(canvas,quality)=>new Promise((resolve,reject)=>{
    canvas.toBlob(blob=>blob?resolve(blob):reject(new Error("Không thể xử lý ảnh trên thiết bị này.")),"image/jpeg",quality);
  });
  const loadImage=file=>new Promise((resolve,reject)=>{
    const url=URL.createObjectURL(file);
    const image=new Image();
    image.onload=()=>resolve({image,url});
    image.onerror=()=>{URL.revokeObjectURL(url);reject(new Error(`Không đọc được ảnh “${file.name}”. Hãy thử chọn ảnh khác hoặc lưu ảnh dưới dạng JPG.`));};
    image.src=url;
  });
  const convertToJpeg=async(file,maxBytes)=>{
    const loaded=await loadImage(file);
    const image=loaded.image;
    try{
      const sourceWidth=image.naturalWidth||image.width;
      const sourceHeight=image.naturalHeight||image.height;
      if(!sourceWidth||!sourceHeight)throw new Error(`Không đọc được kích thước ảnh “${file.name}”.`);
      let maxDimension=2200;
      let quality=.88;
      for(let attempt=0;attempt<5;attempt++){
        const scale=Math.min(1,maxDimension/Math.max(sourceWidth,sourceHeight));
        const width=Math.max(1,Math.round(sourceWidth*scale));
        const height=Math.max(1,Math.round(sourceHeight*scale));
        const canvas=document.createElement("canvas");
        canvas.width=width;canvas.height=height;
        const context=canvas.getContext("2d");
        if(!context)throw new Error("Trình duyệt không hỗ trợ tối ưu ảnh.");
        context.fillStyle="#fff";context.fillRect(0,0,width,height);
        context.drawImage(image,0,0,width,height);
        const blob=await blobFromCanvas(canvas,quality);
        if(blob.size<=maxBytes||attempt===4){
          if(blob.size>maxBytes)throw new Error(`Ảnh “${file.name}” vẫn quá lớn sau khi tối ưu. Hãy chọn ảnh nhỏ hơn.`);
          const base=(file.name||"anh-can-ho").replace(/\.[^.]+$/,"").slice(0,80)||"anh-can-ho";
          return new File([blob],`${base}.jpg`,{type:"image/jpeg",lastModified:Date.now()});
        }
        maxDimension=Math.max(1200,Math.round(maxDimension*.82));
        quality=Math.max(.68,quality-.06);
      }
      throw new Error(`Không thể tối ưu ảnh “${file.name}”.`);
    }finally{
      URL.revokeObjectURL(loaded.url);
    }
  };
  const prepareFiles=async files=>{
    const maxBytes=Number(api.config.maxImageBytes||5*1024*1024);
    const prepared=[];
    for(const file of files){
      const kind=fileKind(file);
      if(kind==="direct"&&file.size<=maxBytes){prepared.push(file);continue;}
      prepared.push(await convertToJpeg(file,maxBytes));
    }
    return prepared;
  };

  const clearPreviews=()=>{previewUrls.forEach(URL.revokeObjectURL);previewUrls=[];previews.replaceChildren();};
  const renderPreviews=()=>{
    clearPreviews();
    const files=[...(filesInput.files||[])];
    try{validateFileSelection(files);clearStatus();}catch(error){showStatus(error.message,"error");return;}
    files.forEach((file,index)=>{
      const figure=document.createElement("figure");figure.className="image-preview";
      const image=document.createElement("img");const url=URL.createObjectURL(file);previewUrls.push(url);
      image.src=url;image.alt=`Ảnh xem trước ${index+1}`;
      image.addEventListener("error",()=>{image.alt=`Đã chọn ảnh ${index+1}: ${file.name}`;});
      const label=document.createElement("span");label.textContent=index===0?"Ảnh đại diện":String(index+1);
      figure.append(image,label);previews.append(figure);
    });
  };
  const fieldLabel=element=>{
    if(!element?.id)return "thông tin bắt buộc";
    return form.querySelector(`label[for="${CSS.escape(element.id)}"]`)?.textContent?.replace(/\s*\*\s*$/,"").trim()||"thông tin bắt buộc";
  };
  const validateFormFields=()=>{
    const invalid=[...form.elements].find(element=>!element.disabled&&element!==filesInput&&typeof element.checkValidity==="function"&&!element.checkValidity());
    if(!invalid)return true;
    showStatus(`Vui lòng kiểm tra lại mục “${fieldLabel(invalid)}”.`,"error");
    try{invalid.focus({preventScroll:true});}catch{}
    invalid.scrollIntoView({behavior:"smooth",block:"center"});
    return false;
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
    if(!validateFormFields())return;
    if(!api.configured()){showStatus("Hệ thống dữ liệu đang được kết nối. Vui lòng quay lại sau ít phút.","error");return;}
    const selectedFiles=[...(filesInput.files||[])];
    try{validateFileSelection(selectedFiles);}catch(error){showStatus(error.message,"error");return;}
    submit.disabled=true;submit.textContent="Đang tối ưu ảnh…";
    try{
      const files=await prepareFiles(selectedFiles);
      submit.textContent="Đang gửi tin…";
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
      try{await api.notifyListingEmail(listing.id);}catch(error){console.warn("Listing email notification failed",error);}
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