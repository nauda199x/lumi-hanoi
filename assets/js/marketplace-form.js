(()=>{
  const form=document.querySelector("[data-marketplace-submit]");
  if(!form||!window.LumiMarketplace)return;
  const api=window.LumiMarketplace;
  const submitButtons=[...form.querySelectorAll('[type="submit"]')];
  const status=form.querySelector("[data-form-status]");
  const filesInput=form.querySelector('[name="images"]');
  const previews=form.querySelector("[data-image-previews]");
  const phase=form.querySelector('[name="phase"]');
  const tower=form.querySelector('[name="tower"]');
  const priceLabel=form.querySelector("[data-price-label]");
  const priceInput=form.querySelector("[data-price-input]");
  const priceHelp=form.querySelector("[data-price-help]");
  const phoneInput=form.querySelector('[name="contact_phone"]');
  const phoneHelp=form.querySelector("[data-phone-help]");
  const availableField=form.querySelector("[data-available-field]");
  const availableLabel=form.querySelector("[data-available-label]");
  const availableInput=form.elements.available_from;
  const legalField=form.querySelector("[data-legal-field]");
  const legalInput=form.elements.legal_status;
  const progressCurrent=form.querySelector("[data-progress-current]");
  const progressBar=form.querySelector("[data-progress-bar]");
  const progressSteps=[...form.querySelectorAll("[data-progress-step]")];
  const sections=[...form.querySelectorAll("[data-form-step]")];
  const draftStatus=form.querySelector("[data-draft-status]");
  const mobileSubmitBar=form.querySelector("[data-mobile-submit]");
  const towerMap={Signature:["S1","S2","S3","S5","S6"],Prestige:["P1","P2"],Elite:["E1","E2"]};
  const directImageTypes=new Set(["image/jpeg","image/png","image/webp"]);
  const iphoneImageTypes=new Set(["image/heic","image/heif"]);
  const draftKey="lumi-marketplace-draft-v2";
  const draftMaxAge=7*24*60*60*1000;
  let previewUrls=[];
  let draftTimer=0;
  let progressFrame=0;
  let isSubmitting=false;

  const setSubmitState=(label,disabled=isSubmitting)=>{
    submitButtons.forEach(button=>{button.disabled=disabled;button.textContent=label;});
  };
  const showStatus=(message,type="",scroll=true)=>{
    if(!status)return;
    status.hidden=false;
    status.textContent=message;
    status.className=`form-status${type?` is-${type}`:""}`;
    if(scroll)status.scrollIntoView({behavior:"smooth",block:"nearest"});
  };
  const clearStatus=()=>{
    if(!status)return;
    status.hidden=true;
    status.textContent="";
    status.className="form-status";
  };
  const listingType=()=>form.querySelector('[name="listing_type"]:checked')?.value||"sale";
  const formatNumber=value=>new Intl.NumberFormat("vi-VN",{maximumFractionDigits:2}).format(value);
  const parseLocalizedNumber=raw=>{
    const normalized=String(raw||"").trim().toLowerCase()
      .replace(/tỷ|ty|triệu|trieu|\/tháng|\/thang|tháng|thang|đồng|dong|vnđ|vnd|đ/g,"")
      .replace(/\s+/g,"")
      .replace(",",".");
    if(!/^\d+(?:\.\d+)?$/.test(normalized))return null;
    const parsed=Number(normalized);
    return Number.isFinite(parsed)&&parsed>0?parsed:null;
  };
  const priceAmount=()=>parseLocalizedNumber(priceInput?.value);
  const priceVnd=()=>{
    const amount=priceAmount();
    if(!amount)return null;
    return Math.round(amount*(listingType()==="rent"?1_000_000:1_000_000_000));
  };
  const updatePriceHelp=()=>{
    if(!priceInput||!priceHelp)return;
    const amount=priceAmount();
    const rent=listingType()==="rent";
    const hasValue=Boolean(priceInput.value.trim());
    priceInput.setCustomValidity(hasValue&&!amount?"Giá chưa đúng định dạng.":"");
    priceInput.setAttribute("aria-invalid",hasValue&&!amount?"true":"false");
    priceHelp.classList.toggle("field-error",hasValue&&!amount);
    if(amount){
      priceHelp.textContent=rent
        ?`Hệ thống sẽ ghi nhận ${formatNumber(amount)} triệu/tháng.`
        :`Hệ thống sẽ ghi nhận ${formatNumber(amount)} tỷ đồng.`;
    }else{
      priceHelp.textContent=rent
        ?"Nhập theo triệu đồng/tháng, ví dụ 10 hoặc 10,5."
        :"Nhập theo tỷ đồng, ví dụ 3,5 hoặc 6,8.";
    }
  };
  const updatePhoneHelp=()=>{
    if(!phoneInput||!phoneHelp)return true;
    const digits=phoneInput.value.replace(/\D/g,"");
    const hasValue=Boolean(phoneInput.value.trim());
    const valid=!hasValue||(digits.length>=9&&digits.length<=15);
    phoneInput.setCustomValidity(valid?"":"Số điện thoại cần có từ 9 đến 15 chữ số.");
    phoneInput.setAttribute("aria-invalid",valid?"false":"true");
    phoneHelp.classList.toggle("field-error",!valid);
    phoneHelp.textContent=!hasValue
      ?"Dùng số điện thoại có thể nhận cuộc gọi hoặc Zalo."
      :valid
        ?"Số liên hệ hợp lệ; khách sẽ thấy số này khi tin được duyệt."
        :"Vui lòng kiểm tra lại số điện thoại (9–15 chữ số).";
    return valid;
  };
  const refreshType=(clearPrice=false)=>{
    const rent=listingType()==="rent";
    if(priceLabel)priceLabel.textContent=rent?"Giá cho thuê (triệu/tháng) *":"Giá bán mong muốn (tỷ) *";
    if(priceInput){
      priceInput.placeholder=rent?"Ví dụ: 10 triệu/tháng":"Ví dụ: 3,5 tỷ";
      if(clearPrice)priceInput.value="";
    }
    if(availableLabel)availableLabel.textContent="Ngày có thể vào ở";
    if(availableField)availableField.hidden=!rent;
    if(availableInput)availableInput.disabled=!rent;
    if(legalField)legalField.hidden=rent;
    if(legalInput)legalInput.disabled=rent;
    updatePriceHelp();
  };
  const refreshTowers=()=>{
    if(!tower||!phase)return;
    const selected=tower.value;
    const options=towerMap[phase.value]||[];
    tower.replaceChildren(new Option("Chọn tòa",""),...options.map(value=>new Option(value,value)));
    if(options.includes(selected))tower.value=selected;
  };

  const setProgress=step=>{
    const next=Math.min(Math.max(Number(step)||1,1),4);
    if(progressCurrent)progressCurrent.textContent=`Bước ${next}/4`;
    if(progressBar)progressBar.style.width=`${next*25}%`;
    progressSteps.forEach((item,index)=>{
      const itemStep=index+1;
      item.classList.toggle("is-active",itemStep===next);
      item.classList.toggle("is-complete",itemStep<next);
      if(itemStep===next)item.setAttribute("aria-current","step");
      else item.removeAttribute("aria-current");
    });
  };
  const progressFromScroll=()=>{
    progressFrame=0;
    const anchor=Math.min(window.innerHeight*.3,240);
    let current=1;
    sections.forEach(section=>{
      if(section.getBoundingClientRect().top<=anchor)current=Number(section.dataset.formStep)||current;
    });
    setProgress(current);
  };
  const scheduleProgress=()=>{
    if(progressFrame)return;
    progressFrame=requestAnimationFrame(progressFromScroll);
  };
  progressSteps.forEach((item,index)=>{
    item.addEventListener("click",()=>{
      const target=sections[index];
      if(target)target.scrollIntoView({behavior:"smooth",block:"start"});
    });
  });
  sections.forEach(section=>section.addEventListener("focusin",()=>setProgress(section.dataset.formStep)));

  const draftElements=()=>[...form.elements].filter(element=>
    element.name&&element!==filesInput&&element.name!=="website"&&element.type!=="submit"
  );
  const saveDraft=()=>{
    draftTimer=0;
    if(isSubmitting)return;
    try{
      const values={};
      draftElements().forEach(element=>{
        if(element.type==="radio"){
          if(element.checked)values[element.name]=element.value;
        }else if(element.type==="checkbox"){
          values[element.name]=Boolean(element.checked);
        }else{
          values[element.name]=element.value;
        }
      });
      localStorage.setItem(draftKey,JSON.stringify({savedAt:Date.now(),values}));
      if(draftStatus)draftStatus.textContent="Đã lưu bản nháp";
    }catch{}
  };
  const scheduleDraft=()=>{
    clearTimeout(draftTimer);
    draftTimer=setTimeout(saveDraft,280);
  };
  const clearDraft=()=>{
    try{localStorage.removeItem(draftKey);}catch{}
    if(draftStatus)draftStatus.textContent="";
  };
  const restoreDraft=()=>{
    try{
      const raw=localStorage.getItem(draftKey);
      if(!raw)return false;
      const draft=JSON.parse(raw);
      if(!draft?.values||Date.now()-Number(draft.savedAt||0)>draftMaxAge){
        localStorage.removeItem(draftKey);
        return false;
      }
      const savedTower=draft.values.tower||"";
      draftElements().forEach(element=>{
        if(element.name==="tower")return;
        if(!(element.name in draft.values))return;
        const saved=draft.values[element.name];
        if(element.type==="radio")element.checked=saved===element.value;
        else if(element.type==="checkbox")element.checked=Boolean(saved);
        else element.value=saved??"";
      });
      refreshType(false);
      refreshTowers();
      if(savedTower&&[...tower.options].some(option=>option.value===savedTower))tower.value=savedTower;
      updatePhoneHelp();
      updatePriceHelp();
      if(draftStatus)draftStatus.textContent="Đã khôi phục bản nháp · ảnh cần chọn lại";
      return true;
    }catch{
      return false;
    }
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
  const prepareFiles=async(files,onProgress)=>{
    const maxBytes=Number(api.config.maxImageBytes||5*1024*1024);
    const prepared=[];
    for(let index=0;index<files.length;index++){
      onProgress?.(index+1,files.length);
      const file=files[index];
      const kind=fileKind(file);
      if(kind==="direct"&&file.size<=maxBytes){prepared.push(file);continue;}
      prepared.push(await convertToJpeg(file,maxBytes));
    }
    return prepared;
  };

  const clearPreviews=()=>{previewUrls.forEach(URL.revokeObjectURL);previewUrls=[];previews?.replaceChildren();};
  const renderPreviews=()=>{
    clearPreviews();
    const files=[...(filesInput?.files||[])];
    try{validateFileSelection(files);clearStatus();}catch(error){showStatus(error.message,"error",false);return;}
    files.forEach((file,index)=>{
      const figure=document.createElement("figure");figure.className="image-preview";
      const image=document.createElement("img");const url=URL.createObjectURL(file);previewUrls.push(url);
      image.src=url;image.alt=`Ảnh xem trước ${index+1}`;
      image.addEventListener("error",()=>{image.alt=`Đã chọn ảnh ${index+1}: ${file.name}`;});
      const label=document.createElement("span");label.textContent=index===0?"Ảnh đại diện":String(index+1);
      figure.append(image,label);previews?.append(figure);
    });
  };
  const fieldLabel=element=>{
    if(!element?.id)return "thông tin bắt buộc";
    return form.querySelector(`label[for="${CSS.escape(element.id)}"]`)?.textContent?.replace(/\s*\*\s*$/,"").trim()||"thông tin bắt buộc";
  };
  const validateFormFields=()=>{
    updatePriceHelp();
    updatePhoneHelp();
    const invalid=[...form.elements].find(element=>
      !element.disabled&&element!==filesInput&&typeof element.checkValidity==="function"&&!element.checkValidity()
    );
    if(!invalid)return true;
    invalid.setAttribute?.("aria-invalid","true");
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
      price_vnd:priceVnd(),furnishing:value("furnishing")||null,available_from:listingType()==="rent"?(value("available_from")||null):null,legal_status:listingType()==="sale"?(value("legal_status")||null):null,
      title:value("title"),description:value("description"),contact_public:Boolean(form.elements.contact_public?.checked)
    };
  };

  priceInput?.addEventListener("input",()=>{
    const raw=priceInput.value;
    const cleaned=raw.replace(/[^0-9,.\sA-Za-zÀ-ỹ/]/g,"");
    if(cleaned!==raw)priceInput.value=cleaned;
    updatePriceHelp();
  });
  phoneInput?.addEventListener("input",updatePhoneHelp);
  form.addEventListener("input",event=>{
    if(event.target!==priceInput&&event.target!==phoneInput)event.target?.removeAttribute?.("aria-invalid");
    scheduleDraft();
  });
  form.addEventListener("change",event=>{
    if(event.target.name==="listing_type")refreshType(true);
    if(event.target===phase)refreshTowers();
    if(event.target===filesInput)renderPreviews();
    if(event.target!==filesInput)scheduleDraft();
  });
  form.addEventListener("submit",async event=>{
    event.preventDefault();
    if(isSubmitting)return;
    clearStatus();
    if(form.elements.website?.value){showStatus("Tin của anh/chị đã được tiếp nhận.","success");return;}
    if(!validateFormFields())return;
    if(!api.configured()){showStatus("Hệ thống dữ liệu đang được kết nối. Vui lòng quay lại sau ít phút.","error");return;}
    const selectedFiles=[...(filesInput?.files||[])];
    try{validateFileSelection(selectedFiles);}catch(error){showStatus(error.message,"error");return;}

    isSubmitting=true;
    setSubmitState("Đang chuẩn bị ảnh…",true);
    try{
      const files=await prepareFiles(selectedFiles,(current,total)=>setSubmitState(`Đang tối ưu ảnh ${current}/${total}…`,true));
      setSubmitState("Đang tạo tin…",true);
      const listing=await api.createListing(payload());
      let uploaded=0;
      for(let index=0;index<files.length;index++){
        try{
          setSubmitState(`Đang tải ảnh ${index+1}/${files.length}…`,true);
          const path=await api.uploadImage(listing.id,files[index],index);
          await api.addListingImage(listing.id,path,index,`${listing.title} — ảnh ${index+1}`);
          uploaded++;
        }catch(error){console.warn("Image upload failed",error);}
      }
      const imageNote=files.length&&uploaded<files.length?` Đã tải ${uploaded}/${files.length} ảnh; quản trị viên sẽ liên hệ nếu cần bổ sung.`:"";
      clearDraft();
      showStatus(`Đã nhận tin ${listing.listing_code}. Tin đang chờ quản trị viên duyệt và chưa hiển thị công khai.${imageNote}`,"success");
      form.reset();
      clearPreviews();
      refreshType(false);
      refreshTowers();
      updatePhoneHelp();
      setProgress(1);
    }catch(error){
      showStatus(error.status===429?"Anh/chị gửi quá nhanh. Vui lòng chờ rồi thử lại.":`Chưa gửi được tin: ${error.message}`,"error");
    }finally{
      isSubmitting=false;
      setSubmitState("Gửi tin chờ duyệt",false);
    }
  });

  window.addEventListener("scroll",scheduleProgress,{passive:true});
  window.addEventListener("resize",scheduleProgress,{passive:true});
  if(mobileSubmitBar&&"IntersectionObserver" in window){
    const observer=new IntersectionObserver(entries=>{
      const visible=entries.some(entry=>entry.isIntersecting);
      mobileSubmitBar.classList.toggle("is-visible",visible);
    },{threshold:0});
    observer.observe(form);
  }else if(mobileSubmitBar){
    mobileSubmitBar.classList.add("is-visible");
  }
  if(mobileSubmitBar&&window.visualViewport){
    const updateKeyboardState=()=>{
      const keyboardOpen=window.visualViewport.height<window.innerHeight*.72;
      mobileSubmitBar.classList.toggle("is-keyboard",keyboardOpen);
    };
    window.visualViewport.addEventListener("resize",updateKeyboardState);
    updateKeyboardState();
  }

  restoreDraft();
  const preset=location.hash.replace(/^#/,"");
  const beforePreset=listingType();
  if(preset==="cho-thue")form.querySelector('[name="listing_type"][value="rent"]').checked=true;
  if(preset==="mua-ban")form.querySelector('[name="listing_type"][value="sale"]').checked=true;
  if(beforePreset!==listingType()&&priceInput)priceInput.value="";
  refreshType(false);
  refreshTowers();
  updatePhoneHelp();
  updatePriceHelp();
  setProgress(1);
  scheduleProgress();
})();