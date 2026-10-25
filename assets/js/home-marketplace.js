/* Lumi Hanoi homepage: current, approved marketplace listings only. */
(()=>{
  const root=document.querySelector('[data-home-listings]');
  const api=window.LumiMarketplace;
  if(!root||!api||!api.configured())return;
  const safeText=value=>String(value??'').trim();
  const make=(tag,className,text)=>{
    const node=document.createElement(tag);
    if(className)node.className=className;
    if(text!==undefined)node.textContent=text;
    return node;
  };
  const formatArea=value=>Number(value)>0?new Intl.NumberFormat('vi-VN',{maximumFractionDigits:1}).format(value)+' m²':'';
  const cards=(items,type,container)=>{
    const fragment=document.createDocumentFragment();
    items.slice(0,3).forEach(listing=>{
      const url=api.listingUrl(listing);
      const card=make('article','home-live-card');
      const visual=make('a','home-live-media');
      visual.href=url;
      visual.setAttribute('aria-label','Xem '+safeText(listing.title||'căn hộ Lumi Hà Nội'));
      const images=Array.isArray(listing.listing_images)?listing.listing_images.filter(img=>img.storage_path).sort((a,b)=>Number(a.sort_order||0)-Number(b.sort_order||0)):[];
      if(images.length){
        const img=make('img');
        img.src=api.imageUrl(images[0].storage_path);
        img.alt=safeText(images[0].alt_text||listing.title||'Căn hộ Lumi Hà Nội');
        img.loading='lazy';img.decoding='async';img.width=480;img.height=330;
        img.addEventListener('error',()=>img.remove(),{once:true});
        visual.append(img);
      }
      visual.append(make('span','home-live-pill',type==='rent'?'Cho thuê':'Mua bán'));
      const body=make('div','home-live-body');
      const heading=make('h3');
      const link=make('a','',safeText(listing.title||'Căn hộ Lumi Hà Nội'));
      link.href=url;heading.append(link);
      const place=[listing.tower,listing.unit_type,formatArea(listing.area_sqm)].filter(Boolean).join(' · ');
      body.append(make('p','home-live-location',place||'Lumi Hà Nội'),heading);
      const bottom=make('div','home-live-bottom');
      bottom.append(make('strong','home-live-price',api.formatCurrency(listing.price_vnd,type)),make('a','home-live-detail','Xem căn →'));
      bottom.querySelector('a').href=url;
      body.append(bottom);card.append(visual,body);fragment.append(card);
    });
    container.replaceChildren(fragment);
  };
  const load=async(type)=>{
    const container=root.querySelector('[data-home-grid="'+type+'"]');
    const status=root.querySelector('[data-home-status="'+type+'"]');
    const count=root.querySelector('[data-home-count="'+type+'"]');
    try{
      const result=await api.listPublicPage(type,{},1);
      if(!result||!Array.isArray(result.rows))throw new Error('invalid response');
      if(count)count.textContent=result.total+' tin đã duyệt';
      if(result.rows.length){
        cards(result.rows,type,container);
        if(status)status.hidden=true;
      }else if(status)status.textContent='Hiện chưa có tin công khai. Xem toàn bộ quỹ căn hoặc đăng tin mới.';
    }catch{
      if(status)status.textContent='Chưa tải được tin mới. Mở trang quỹ căn để thử lại.';
    }
  };
  load('rent');
  load('sale');
  const form=document.querySelector('[data-home-search]');
  form?.addEventListener('submit',event=>{
    event.preventDefault();
    const values=new FormData(form);
    const type=values.get('listing_type')==='sale'?'sale':'rent';
    const url=new URL(type==='sale'?'/mua-ban-lumi-hanoi/':'/cho-thue-lumi-hanoi/',location.origin);
    for(const key of ['tower','bedroom']){
      const value=safeText(values.get(key));
      if(value)url.searchParams.set(key,value);
    }
    window.LumiAnalytics?.track?.('homepage_marketplace_search',{listing_type:type});
    location.assign(url.pathname+url.search);
  });
})();