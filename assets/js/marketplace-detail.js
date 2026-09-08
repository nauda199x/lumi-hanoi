(()=>{
  const root=document.querySelector("[data-listing-detail]");
  if(!root||!window.LumiMarketplace||!window.LumiListingDetail)return;
  const api=window.LumiMarketplace,params=new URLSearchParams(location.search);
  const identifier=params.get("slug")||params.get("id")||"";
  const loading=root.querySelector("[data-detail-loading]"),missing=root.querySelector("[data-detail-missing]"),content=root.querySelector("[data-detail-content]");
  const showMissing=(title,copy)=>{loading.hidden=true;content.hidden=true;missing.hidden=false;missing.querySelector("[data-missing-title]").textContent=title;missing.querySelector("[data-missing-copy]").textContent=copy;};
  const load=async()=>{
    if(!identifier){showMissing("Không tìm thấy mã tin","Đường dẫn này chưa có mã tin hợp lệ.");return;}
    if(!api.configured()){showMissing("Dữ liệu giao dịch đang được cập nhật","Vui lòng quay lại sau khi hệ thống hoàn tất cập nhật.");return;}
    try{
      const listing=await api.getPublicListing(identifier);
      if(!listing){showMissing("Tin không còn hiển thị","Tin có thể đang chờ duyệt, đã hết hạn hoặc đã giao dịch.");return;}
      window.LumiListingDetail.hydrate(root,listing);
      loading.hidden=true;missing.hidden=true;
    }catch{showMissing("Chưa thể tải tin đăng","Vui lòng kiểm tra kết nối và tải lại trang.");}
  };
  load();
})();
