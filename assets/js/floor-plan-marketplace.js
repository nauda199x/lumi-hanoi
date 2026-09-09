(()=>{
  const app=document.querySelector('[data-floor-plan-app]');
  if(!app)return;
  const tower=String(app.dataset.tower||'').trim().toUpperCase();
  if(!/^(S1|S2|S3|S5|S6|P1|P2|E1|E2)$/.test(tower))return;
  if(document.querySelector('[data-floor-marketplace-bridge]'))return;

  const esc=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const transactionUrl=type=>`/${type==='rent'?'cho-thue-lumi-hanoi':'mua-ban-lumi-hanoi'}/#tower=${encodeURIComponent(tower)}`;

  const installStyles=()=>{
    if(document.querySelector('[data-floor-marketplace-styles]'))return;
    const style=document.createElement('style');
    style.dataset.floorMarketplaceStyles='true';
    style.textContent=`
.tower-marketplace-bridge{margin:clamp(2.4rem,5vw,4rem) 0;padding:clamp(1.25rem,3vw,2rem);border:1px solid var(--line,#d8d1c5);border-radius:24px;background:linear-gradient(145deg,#fff 0%,#f7f4ed 100%);box-shadow:0 16px 44px rgba(25,29,25,.07)}
.tower-marketplace-bridge-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1.5rem;margin-bottom:1.3rem}.tower-marketplace-bridge-head h2{margin:.25rem 0 .55rem;font-size:clamp(1.7rem,3vw,2.35rem)}.tower-marketplace-bridge-head p:not(.eyebrow){max-width:66ch;margin:0;color:var(--muted,#68635c);line-height:1.65}.tower-marketplace-live{display:inline-flex;align-items:center;gap:.5rem;flex:0 0 auto;padding:.48rem .7rem;border:1px solid rgba(29,94,61,.18);border-radius:999px;background:rgba(29,94,61,.07);color:#245f3f;font-size:.72rem;font-weight:800;white-space:nowrap}.tower-marketplace-live i{width:.48rem;height:.48rem;border-radius:50%;background:#2d7a4d;box-shadow:0 0 0 4px rgba(45,122,77,.12)}
.tower-marketplace-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}.tower-marketplace-panel{min-width:0;padding:1rem;border:1px solid var(--line,#d8d1c5);border-radius:18px;background:#fff}.tower-marketplace-panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;padding-bottom:.85rem;border-bottom:1px solid #ece7de}.tower-marketplace-panel-head h3{margin:.15rem 0 0;font-size:1.12rem}.tower-marketplace-label{display:block;color:var(--muted,#68635c);font-size:.68rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}.tower-marketplace-panel-head>strong{padding:.34rem .55rem;border-radius:999px;background:#f2efe8;font-size:.72rem;white-space:nowrap}.tower-marketplace-panel-head>strong.is-empty{font-weight:700;color:var(--muted,#68635c)}
.tower-marketplace-items{display:grid;gap:.15rem;padding:.55rem 0}.tower-marketplace-item{display:grid;grid-template-columns:76px minmax(0,1fr);gap:.75rem;align-items:center;padding:.55rem;border-radius:12px;color:inherit;text-decoration:none;transition:background .18s ease,transform .18s ease}.tower-marketplace-item:hover,.tower-marketplace-item:focus-visible{background:#f5f2ec;transform:translateY(-1px)}.tower-marketplace-item-media{display:flex;width:76px;aspect-ratio:4/3;align-items:center;justify-content:center;overflow:hidden;border-radius:9px;background:#efede7;color:var(--muted,#68635c);font-size:.72rem;font-weight:800}.tower-marketplace-item-media img{width:100%;height:100%;object-fit:cover}.tower-marketplace-item-copy{display:flex;min-width:0;flex-direction:column;gap:.28rem}.tower-marketplace-item-copy strong{display:-webkit-box;overflow:hidden;font-size:.88rem;line-height:1.35;-webkit-box-orient:vertical;-webkit-line-clamp:2}.tower-marketplace-item-copy>span{overflow:hidden;color:var(--muted,#68635c);font-size:.74rem;line-height:1.35;text-overflow:ellipsis;white-space:nowrap}.tower-marketplace-all{display:flex;min-height:44px;align-items:center;justify-content:space-between;gap:.75rem;margin-top:.2rem;padding:.68rem .8rem;border-radius:10px;background:#1f241f;color:#fff;font-size:.82rem;font-weight:800;text-decoration:none}.tower-marketplace-all:hover,.tower-marketplace-all:focus-visible{background:#303730;color:#fff}.tower-marketplace-note{margin:.9rem 0 0;color:var(--muted,#68635c);font-size:.72rem;line-height:1.5}
.tower-marketplace-loading{display:grid;gap:.55rem;padding:.45rem}.tower-marketplace-loading span{display:block;height:48px;border-radius:10px;background:linear-gradient(90deg,#f1eee8 25%,#faf8f2 50%,#f1eee8 75%);background-size:200% 100%;animation:tower-marketplace-shimmer 1.25s infinite linear}.tower-marketplace-empty{display:flex;min-height:170px;flex-direction:column;align-items:center;justify-content:center;gap:.3rem;padding:1rem;text-align:center}.tower-marketplace-empty strong{font-size:.86rem}.tower-marketplace-empty span{max-width:32ch;color:var(--muted,#68635c);font-size:.76rem;line-height:1.5}@keyframes tower-marketplace-shimmer{to{background-position:-200% 0}}
@media(max-width:760px){.tower-marketplace-bridge{margin:2rem 0;padding:1rem;border-radius:18px}.tower-marketplace-bridge-head{display:block}.tower-marketplace-live{margin-top:.85rem}.tower-marketplace-grid{grid-template-columns:1fr}.tower-marketplace-panel{padding:.85rem}.tower-marketplace-item{grid-template-columns:84px minmax(0,1fr)}.tower-marketplace-item-media{width:84px}.tower-marketplace-all{min-height:48px}.tower-marketplace-empty{min-height:120px}}
@media(prefers-reduced-motion:reduce){.tower-marketplace-item{transition:none}.tower-marketplace-loading span{animation:none}}`;
    document.head.append(style);
  };

  const loadScript=(src,ready)=>new Promise((resolve,reject)=>{
    if(ready())return resolve();
    const existing=document.querySelector(`script[src="${src}"]`);
    const done=()=>ready()?resolve():reject(new Error(`Không khởi tạo được ${src}`));
    if(existing){
      existing.addEventListener('load',done,{once:true});
      existing.addEventListener('error',reject,{once:true});
      window.setTimeout(()=>{if(ready())resolve()},0);
      return;
    }
    const script=document.createElement('script');
    script.src=src;
    script.defer=true;
    script.addEventListener('load',done,{once:true});
    script.addEventListener('error',reject,{once:true});
    document.head.append(script);
  });

  const createBridge=()=>{
    installStyles();
    const section=document.createElement('section');
    section.className='tower-marketplace-bridge';
    section.dataset.floorMarketplaceBridge='true';
    section.setAttribute('aria-labelledby',`tower-marketplace-${tower.toLowerCase()}`);
    section.innerHTML=`
      <div class="tower-marketplace-bridge-head">
        <div>
          <p class="eyebrow">Quỹ căn thực tế · ${esc(tower)}</p>
          <h2 id="tower-marketplace-${esc(tower.toLowerCase())}">Căn ${esc(tower)} đang giao dịch</h2>
          <p>Đã chọn được vị trí trên mặt bằng? So sánh ngay căn ${esc(tower)} đang bán và cho thuê theo giá, diện tích, loại căn và tầng thực tế.</p>
        </div>
        <span class="tower-marketplace-live"><i aria-hidden="true"></i>Dữ liệu marketplace</span>
      </div>
      <div class="tower-marketplace-grid">
        <article class="tower-marketplace-panel" data-floor-inventory="sale">
          <div class="tower-marketplace-panel-head"><div><span class="tower-marketplace-label">Mua bán</span><h3>Căn ${esc(tower)} đang bán</h3></div><strong data-floor-inventory-count>Đang tải…</strong></div>
          <div class="tower-marketplace-items" data-floor-inventory-items aria-live="polite"><div class="tower-marketplace-loading"><span></span><span></span><span></span></div></div>
          <a class="tower-marketplace-all" href="${transactionUrl('sale')}">Xem toàn bộ căn ${esc(tower)} đang bán <span aria-hidden="true">→</span></a>
        </article>
        <article class="tower-marketplace-panel" data-floor-inventory="rent">
          <div class="tower-marketplace-panel-head"><div><span class="tower-marketplace-label">Cho thuê</span><h3>Căn ${esc(tower)} đang cho thuê</h3></div><strong data-floor-inventory-count>Đang tải…</strong></div>
          <div class="tower-marketplace-items" data-floor-inventory-items aria-live="polite"><div class="tower-marketplace-loading"><span></span><span></span><span></span></div></div>
          <a class="tower-marketplace-all" href="${transactionUrl('rent')}">Xem toàn bộ căn ${esc(tower)} đang cho thuê <span aria-hidden="true">→</span></a>
        </article>
      </div>
      <p class="tower-marketplace-note">Tin được lấy từ quỹ căn đã duyệt trên Lumi Hanoi. Giá và tình trạng có thể thay đổi theo người đăng.</p>`;
    app.insertAdjacentElement('afterend',section);
    return section;
  };

  const renderInventory=(panel,result,type,api)=>{
    const count=panel.querySelector('[data-floor-inventory-count]');
    const items=panel.querySelector('[data-floor-inventory-items]');
    const rows=Array.isArray(result?.rows)?result.rows:[];
    const total=Number(result?.total||0);
    count.textContent=total?`${total} tin`:'Chưa có tin';
    count.classList.toggle('is-empty',!total);
    if(!rows.length){
      items.innerHTML=`<div class="tower-marketplace-empty"><strong>Chưa có căn ${esc(tower)} phù hợp.</strong><span>Quỹ căn mới sẽ tự xuất hiện tại đây sau khi được duyệt.</span></div>`;
      return;
    }
    items.replaceChildren();
    rows.slice(0,3).forEach(listing=>{
      const link=document.createElement('a');
      link.className='tower-marketplace-item';
      link.href=api.listingUrl(listing);
      const images=[...(listing.listing_images||[])].sort((a,b)=>Number(a.sort_order||0)-Number(b.sort_order||0));
      const first=images[0];
      const media=document.createElement('span');
      media.className='tower-marketplace-item-media';
      if(first?.storage_path){
        const img=document.createElement('img');
        img.src=api.imageUrl(first.storage_path);
        img.alt=first.alt_text||`Ảnh ${listing.title||`căn ${tower}`}`;
        img.loading='lazy';
        img.decoding='async';
        media.append(img);
      }else{
        media.textContent=listing.unit_type||tower;
        media.classList.add('is-placeholder');
      }
      const copy=document.createElement('span');
      copy.className='tower-marketplace-item-copy';
      const title=document.createElement('strong');
      title.textContent=listing.title||`Căn ${tower} Lumi Hanoi`;
      const facts=document.createElement('span');
      facts.textContent=[
        api.formatCurrency(listing.price_vnd,type),
        Number(listing.area_sqm)>0?`${Number(listing.area_sqm).toLocaleString('vi-VN',{maximumFractionDigits:1})} m²`:'',
        listing.unit_type||'',
        listing.floor_label?`Tầng ${listing.floor_label}`:''
      ].filter(Boolean).join(' · ');
      copy.append(title,facts);
      link.append(media,copy);
      items.append(link);
    });
  };

  const section=createBridge();
  const hydrate=async()=>{
    try{
      await loadScript('/assets/js/marketplace-config.js',()=>Boolean(window.LUMI_MARKETPLACE_CONFIG));
      await loadScript('/assets/js/marketplace-api.js',()=>Boolean(window.LumiMarketplace?.listPublicPage));
      const api=window.LumiMarketplace;
      const panels=[...section.querySelectorAll('[data-floor-inventory]')];
      await Promise.all(panels.map(async panel=>{
        const type=panel.dataset.floorInventory==='rent'?'rent':'sale';
        try{
          const result=await api.listPublicPage(type,{tower,sort:'newest'},1);
          renderInventory(panel,result,type,api);
        }catch{
          panel.querySelector('[data-floor-inventory-count]').textContent='Xem quỹ căn';
          panel.querySelector('[data-floor-inventory-items]').innerHTML='<div class="tower-marketplace-empty"><strong>Dữ liệu đang được cập nhật.</strong><span>Bấm “Xem toàn bộ” để mở marketplace.</span></div>';
        }
      }));
    }catch{
      section.querySelectorAll('[data-floor-inventory]').forEach(panel=>{
        panel.querySelector('[data-floor-inventory-count]').textContent='Xem quỹ căn';
        panel.querySelector('[data-floor-inventory-items]').innerHTML='<div class="tower-marketplace-empty"><strong>Dữ liệu đang được cập nhật.</strong><span>Bấm “Xem toàn bộ” để mở marketplace.</span></div>';
      });
    }
  };

  if('requestIdleCallback'in window)window.requestIdleCallback(hydrate,{timeout:1200});
  else window.setTimeout(hydrate,180);
})();
