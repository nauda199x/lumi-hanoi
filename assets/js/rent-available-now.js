(()=>{
  const form=document.querySelector("[data-marketplace-submit]");
  const availableField=form?.querySelector("[data-available-field]");
  const availableInput=form?.elements?.available_from;
  if(!form||!availableField||!availableInput||availableField.querySelector("[data-available-now]"))return;

  const option=document.createElement("label");
  option.className="available-now-option";
  option.htmlFor="available-now";
  option.style.cssText="display:flex;align-items:center;gap:8px;width:max-content;max-width:100%;margin-top:9px;font-size:13px;font-weight:650;line-height:1.35;color:#415048;cursor:pointer;user-select:none";

  const checkbox=document.createElement("input");
  checkbox.id="available-now";
  checkbox.name="available_now";
  checkbox.type="checkbox";
  checkbox.dataset.availableNow="";
  checkbox.style.cssText="width:16px;height:16px;min-height:16px;flex:0 0 16px;margin:0;padding:0;accent-color:#17352c;cursor:pointer";

  const text=document.createElement("span");
  text.textContent="Có thể vào ở ngay";
  option.append(checkbox,text);
  availableInput.insertAdjacentElement("afterend",option);

  const listingType=()=>form.querySelector('[name="listing_type"]:checked')?.value||"sale";
  const today=()=>{
    const now=new Date();
    return `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")}`;
  };
  const emitInput=()=>availableInput.dispatchEvent(new Event("input",{bubbles:true}));

  const sync=({restore=false}={})=>{
    const rent=listingType()==="rent";
    if(!rent){
      availableInput.disabled=true;
      return;
    }
    if(checkbox.checked){
      if(!restore&&!checkbox.dataset.previousDate)checkbox.dataset.previousDate=availableInput.value||"";
      availableInput.value=today();
      availableInput.disabled=true;
    }else{
      availableInput.disabled=false;
      if(restore&&checkbox.dataset.previousDate!==undefined){
        availableInput.value=checkbox.dataset.previousDate;
        delete checkbox.dataset.previousDate;
      }
    }
  };

  checkbox.addEventListener("change",()=>{
    if(checkbox.checked){
      checkbox.dataset.previousDate=availableInput.value||"";
      sync();
    }else{
      sync({restore:true});
    }
    emitInput();
  });

  form.querySelectorAll('[name="listing_type"]').forEach(input=>{
    input.addEventListener("change",()=>queueMicrotask(()=>sync()));
  });

  queueMicrotask(()=>sync());
})();
