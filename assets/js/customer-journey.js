(()=>{
  if(location.pathname.startsWith('/admin/'))return;

  const cssHref='/assets/css/customer-journey.css?v=20260912a';
  if(!document.querySelector('link[data-customer-journey]')){
    const link=document.createElement('link');
    link.rel='stylesheet';
    link.href=cssHref;
    link.dataset.customerJourney='true';
    document.head.append(link);
  }

  const path=location.pathname;
  const nav=document.querySelector('[data-nav-links]');
  const menuButton=document.querySelector('[data-nav-toggle]');

  const makeLink=(href,label,className='')=>{
    const link=document.createElement('a');
    link.href=href;
    link.textContent=label;
    if(className)link.className=className;
    return link;
  };

  // Keep one predictable information architecture across old editorial pages,
  // floor-plan pages and marketplace pages without rewriting every static file.
  if(nav){
    const topLink=href=>[...nav.children].find(item=>item.matches?.(`a[href="${href}"]`));
    const dropdown=label=>[...nav.querySelectorAll(':scope > .nav-dropdown')].find(item=>item.querySelector(':scope > summary')?.textContent.trim()===label);
    const ensureTopLink=(href,label)=>{
      let link=topLink(href);
      if(!link){
        link=makeLink(href,label);
        nav.append(link);
      }
      link.textContent=label;
      return link;
    };

    const overview=ensureTopLink('/tong-quan-lumi-hanoi/','Tổng quan');
    const floor=ensureTopLink('/mat-bang-lumi-hanoi/','Mặt bằng');
    const amenities=ensureTopLink('/tien-ich-lumi-hanoi/','Tiện ích');
    const progress=ensureTopLink('/tien-do-lumi-hanoi/','Tiến độ');
    const news=ensureTopLink('/tin-tuc/','Tin tức');
    const directCta=nav.querySelector(':scope > .nav-direct-cta');
    const transaction=dropdown('Giao dịch');
    const phases=dropdown('Phân khu');

    if(transaction){
      transaction.classList.add('nav-market');
      const menu=transaction.querySelector('.nav-dropdown-menu');
      if(menu){
        const sale=menu.querySelector('a[href="/mua-ban-lumi-hanoi/"]')||makeLink('/mua-ban-lumi-hanoi/','Mua bán');
        const rent=menu.querySelector('a[href="/cho-thue-lumi-hanoi/"]')||makeLink('/cho-thue-lumi-hanoi/','Cho thuê');
        const price=menu.querySelector('a[href="/gia-can-ho-lumi-hanoi/"]')||makeLink('/gia-can-ho-lumi-hanoi/','Bảng giá');
        const post=menu.querySelector('a[href="/dang-tin-lumi-hanoi/"]')||makeLink('/dang-tin-lumi-hanoi/','Đăng tin');
        [sale,rent,price,post].forEach(item=>menu.append(item));
      }
    }

    // Reorder existing nodes rather than rebuilding them, preserving menu event handlers.
    [overview,directCta,transaction,floor,amenities,phases,progress,news].filter(Boolean).forEach(item=>nav.append(item));

    nav.querySelectorAll('a[aria-current="page"]').forEach(item=>item.removeAttribute('aria-current'));
    nav.querySelectorAll('a[href]').forEach(link=>{
      try{
        const target=new URL(link.href,location.origin).pathname;
        if(target==='/'?path==='/':path===target)link.setAttribute('aria-current','page');
      }catch{}
    });
    if(path.startsWith('/mat-bang-lumi-hanoi/'))floor.setAttribute('aria-current','page');
    if(path.startsWith('/tin-tuc/'))news.setAttribute('aria-current','page');

    nav.addEventListener('click',event=>{
      if(!event.target.closest('a[href]'))return;
      if(nav.getAttribute('data-open')==='true'&&menuButton)menuButton.click();
    });
  }

  const planExperience=
    path.startsWith('/mat-bang-lumi-hanoi/')||
    /^\/can-ho-[1-4]-phong-ngu-lumi-hanoi\/$/.test(path)||
    path==='/duplex-penthouse-lumi-hanoi/'||
    path.startsWith('/layout-can-ho-lumi-');

  if(planExperience&&!document.querySelector('[data-customer-lookup]')){
    const main=document.querySelector('main');
    const breadcrumb=main?.querySelector('.breadcrumb');
    const hero=[...main?.children||[]].find(node=>node.tagName==='HEADER'&&node!==document.querySelector('.site-header'))||main?.querySelector('.article-hero,.layout-library-hero,.floor-hub-hero');
    const lookup=document.createElement('section');
    lookup.className='customer-lookup';
    lookup.dataset.customerLookup='true';
    lookup.setAttribute('aria-label','Tra cứu nhanh Lumi Hanoi');

    const unitLinks=[
      ['1PN','/can-ho-1-phong-ngu-lumi-hanoi/'],
      ['2PN','/can-ho-2-phong-ngu-lumi-hanoi/'],
      ['3PN','/can-ho-3-phong-ngu-lumi-hanoi/'],
      ['4PN','/can-ho-4-phong-ngu-lumi-hanoi/'],
      ['Duplex','/duplex-penthouse-lumi-hanoi/']
    ];
    const towerLinks=[
      ['S1','/mat-bang-lumi-hanoi/lumi-signature/s1/'],['S2','/mat-bang-lumi-hanoi/lumi-signature/s2/'],['S3','/mat-bang-lumi-hanoi/lumi-signature/s3/'],['S5','/mat-bang-lumi-hanoi/lumi-signature/s5/'],['S6','/mat-bang-lumi-hanoi/lumi-signature/s6/'],
      ['P1','/mat-bang-lumi-hanoi/lumi-prestige/p1/'],['P2','/mat-bang-lumi-hanoi/lumi-prestige/p2/'],['E1','/mat-bang-lumi-hanoi/lumi-elite/e1/'],['E2','/mat-bang-lumi-hanoi/lumi-elite/e2/']
    ];
    const renderLinks=items=>items.map(([label,href])=>`<a href="${href}">${label}</a>`).join('');
    lookup.innerHTML=`
      <div class="container customer-lookup-inner">
        <div class="customer-lookup-intro">
          <span>Tra cứu nhanh</span>
          <strong>Mặt bằng → Layout → Căn đang giao dịch</strong>
        </div>
        <div class="customer-lookup-groups">
          <div class="customer-lookup-group"><small>Loại căn</small><nav aria-label="Chọn loại căn">${renderLinks(unitLinks)}</nav></div>
          <div class="customer-lookup-group"><small>Tòa</small><nav aria-label="Chọn tòa">${renderLinks(towerLinks)}</nav></div>
          <div class="customer-lookup-group customer-lookup-market"><small>Giao dịch</small><nav aria-label="Giao dịch Lumi Hanoi"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/gia-can-ho-lumi-hanoi/">Bảng giá</a></nav></div>
        </div>
      </div>`;

    if(hero)hero.insertAdjacentElement('afterend',lookup);
    else if(breadcrumb)breadcrumb.insertAdjacentElement('afterend',lookup);
    else main?.prepend(lookup);

    lookup.addEventListener('click',event=>{
      const link=event.target.closest('a[href]');
      if(!link)return;
      window.LumiAnalytics?.track?.('quick_lookup_click',{destination:new URL(link.href,location.origin).pathname});
    });
  }

  if(document.body.classList.contains('price-page')&&!document.querySelector('[data-price-quick-answer]')){
    const cards=[...document.querySelectorAll('.market-table-card')];
    const saleCard=cards.find(card=>card.querySelector('h3')?.textContent.includes('Giá rao bán theo loại căn'));
    const rentCard=cards.find(card=>card.querySelector('h3')?.textContent.includes('Giá rao thuê theo loại căn'));
    if(saleCard&&rentCard){
      saleCard.id='gia-ban-chi-tiet';
      rentCard.id='gia-thue-chi-tiet';
      const rows=card=>new Map([...card.querySelectorAll('tbody tr')].map(row=>{
        const cells=[...row.children].map(cell=>cell.textContent.trim());
        return [cells[0],cells];
      }));
      const saleRows=rows(saleCard);
      const rentRows=rows(rentCard);
      const types=['1PN','2PN','3PN','4PN'].filter(type=>{
        const sale=saleRows.get(type); const rent=rentRows.get(type);
        return Number(sale?.[1]||0)>0||Number(rent?.[1]||0)>0;
      });
      if(types.length){
        const section=document.createElement('section');
        section.className='price-quick-answer';
        section.dataset.priceQuickAnswer='true';
        const rentLinks={
          '1PN':'/cho-thue-can-ho-1-phong-ngu-lumi-hanoi/',
          '2PN':'/cho-thue-can-ho-2-phong-ngu-lumi-hanoi/',
          '3PN':'/cho-thue-can-ho-3-phong-ngu-lumi-hanoi/',
          '4PN':'/cho-thue-can-ho-4-phong-ngu-lumi-hanoi/'
        };
        const typeCards=types.map(type=>{
          const sale=saleRows.get(type)||[];
          const rent=rentRows.get(type)||[];
          const saleRange=sale[2]&&sale[2]!=='—'?sale[2]:'Chưa đủ dữ liệu';
          const saleAvg=sale[3]&&sale[3]!=='—'?sale[3]:'—';
          const rentRange=rent[2]&&rent[2]!=='—'?rent[2]:'Chưa đủ dữ liệu';
          const rentAvg=rent[3]&&rent[3]!=='—'?rent[3]:'—';
          return `<article class="price-quick-card">
            <div class="price-quick-card-head"><strong>${type}</strong><span>${Number(sale[1]||0)+Number(rent[1]||0)} tin</span></div>
            <div class="price-quick-line"><small>Giá bán đang rao</small><b>${saleRange}</b><em>TB ${saleAvg}</em></div>
            <div class="price-quick-line"><small>Giá thuê đang rao</small><b>${rentRange}</b><em>TB ${rentAvg}</em></div>
            <div class="price-quick-actions"><a href="/mua-ban-lumi-hanoi/">Xem căn bán</a><a href="${rentLinks[type]||'/cho-thue-lumi-hanoi/'}">Xem căn thuê</a></div>
          </article>`;
        }).join('');
        section.innerHTML=`<div class="price-quick-head"><div><p class="eyebrow">Giá nhanh theo nhu cầu</p><h2>Muốn mua hoặc thuê căn nào?</h2><p>Xem ngay khoảng giá rao hiện có theo loại căn. Số liệu lấy trực tiếp từ quỹ tin đã duyệt trên website.</p></div><div class="price-quick-jumps"><a href="#gia-ban-chi-tiet">Bảng giá bán chi tiết ↓</a><a href="#gia-thue-chi-tiet">Bảng giá thuê chi tiết ↓</a></div></div><div class="price-quick-grid">${typeCards}</div>`;
        const history=document.querySelector('.sale-history-card');
        if(history)history.insertAdjacentElement('beforebegin',section);
        else saleCard.insertAdjacentElement('beforebegin',section);
      }
    }
  }
})();
