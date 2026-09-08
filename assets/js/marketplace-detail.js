(()=>{
  const root=document.querySelector("[data-listing-detail]");
  if(!root||!window.LumiMarketplace||!window.LumiListingDetail)return;
  const api=window.LumiMarketplace,params=new URLSearchParams(location.search);
  const identifier=params.get("slug")||params.get("id")||"";
  const loading=root.querySelector("[data-detail-loading]"),missing=root.querySelector("[data-detail-missing]"),content=root.querySelector("[data-detail-content]");
  const showMissing=(title,copy)=>{loading.hidden=true;content.hidden=true;missing.hidden=false;missing.querySelector("[data-missing-title]").textContent=title;missing.querySelector("[data-missing-copy]").textContent=copy;};
  const showViewCount=count=>{
    const value=Math.max(0,Math.floor(Number(count)||0)),meta=root.querySelector(".ld-meta");
    if(!meta)return;
    let node=meta.querySelector("[data-detail-views]");
    if(!node){node=document.createElement("span");node.setAttribute("data-detail-views","");meta.append(node);}
    node.hidden=value<1;
    if(value>=1){node.textContent=`${new Intl.NumberFormat("vi-VN").format(value)} lượt xem`;node.setAttribute("aria-label",`${value} lượt xem tin`);}
  };
  const recordView=async()=>{
    const id=root.dataset.listingId||"",config=window.LUMI_MARKETPLACE_CONFIG||{};
    const base=String(config.supabaseUrl||"").replace(/\/$/,""),key=String(config.supabasePublishableKey||config.supabaseAnonKey||"");
    if(!id||!base||!key||base.includes("YOUR_PROJECT"))return;
    try{
      const response=await fetch(`${base}/rest/v1/rpc/record_listing_view`,{method:"POST",headers:{apikey:key,"Content-Type":"application/json"},body:JSON.stringify({target_listing_id:id})});
      if(!response.ok)return;
      showViewCount(await response.json());
    }catch{}
  };
  const load=async()=>{
    if(!identifier){showMissing("Không tìm thấy mã tin","Đường dẫn này chưa có mã tin hợp lệ.");return;}
    if(!api.configured()){showMissing("Dữ liệu giao dịch đang được cập nhật","Vui lòng quay lại sau khi hệ thống hoàn tất cập nhật.");return;}
    try{
      const listing=await api.getPublicListing(identifier);
      if(!listing){showMissing("Tin không còn hiển thị","Tin có thể đang chờ duyệt, đã hết hạn hoặc đã giao dịch.");return;}
      window.LumiListingDetail.hydrate(root,listing);
      loading.hidden=true;missing.hidden=true;
      recordView();
    }catch{showMissing("Chưa thể tải tin đăng","Vui lòng kiểm tra kết nối và tải lại trang.");}
  };
  load();
})();
