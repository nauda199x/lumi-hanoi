/* Open the correct category before jumping to a rental price anchor. */
(()=>{
  document.addEventListener("click",event=>{
    const link=event.target.closest?.(".rent-price-pills a[href^='#gia-thue-']");
    if(!link)return;
    const id=link.getAttribute("href")?.slice(1);
    if(!id||!/^[a-z0-9-]+$/.test(id))return;
    const section=document.getElementById(id);
    if(section&&section.tagName==="DETAILS")section.open=true;
  });
})();
