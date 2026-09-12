(()=>{
  if(location.pathname.startsWith('/admin/'))return;

  if(!document.querySelector('style[data-customer-journey]')){
    const style=document.createElement('style');
    style.dataset.customerJourney='true';
    style.textContent=`
      .customer-lookup{border-block:1px solid var(--line,#d7d0c3);background:var(--paper,#fbf9f3)}
      .customer-lookup-inner{display:grid;grid-template-columns:220px minmax(0,1fr);gap:32px;align-items:center;padding-block:18px}
      .customer-lookup-intro span{display:block;margin-bottom:4px;color:var(--bronze-dark,#705335);font-size:.68rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase}
      .customer-lookup-intro strong{display:block;font-family:Iowan Old Style,Baskerville,Georgia,serif;font-size:1.18rem;font-weight:500;line-height:1.3}
      .customer-lookup-groups{display:grid;grid-template-columns:1fr 1.5fr .85fr;gap:14px;min-width:0}.customer-lookup-group{min-width:0}
      .customer-lookup-group>small{display:block;margin-bottom:7px;color:var(--muted,#64645e);font-size:.66rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
      .customer-lookup-group nav{display:flex;gap:6px;overflow-x:auto;padding-bottom:2px;scrollbar-width:none}.customer-lookup-group nav::-webkit-scrollbar{display:none}
      .customer-lookup-group a{display:inline-flex;min-height:34px;align-items:center;justify-content:center;flex:0 0 auto;padding:0 10px;border:1px solid var(--line,#d7d0c3);border-radius:999px;background:#fff;color:var(--ink,#171916);font-size:.77rem;font-weight:750;text-decoration:none}
      .customer-lookup-group a:hover,.customer-lookup-group a:focus-visible{border-color:var(--ink,#171916);background:var(--ink,#171916);color:#fff}.customer-lookup-market a:first-child{border-color:var(--night,#171a18);background:var(--night,#171a18);color:#fff}
      .price-quick-answer{margin:0 0 24px;padding:26px;border:1px solid var(--line,#d7d0c3);border-radius:18px;background:var(--paper,#fbf9f3)}
      .price-quick-head{display:flex;align-items:end;justify-content:space-between;gap:28px;margin-bottom:20px}.price-quick-head h2{margin:.15rem 0 .45rem;max-width:18ch;font-size:clamp(2rem,4vw,3rem)}.price-quick-head p:last-child{max-width:650px;margin:0;color:var(--muted,#64645e);line-height:1.65}
      .price-quick-jumps{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:8px}.price-quick-jumps a{padding:8px 11px;border:1px solid var(--line,#d7d0c3);border-radius:999px;font-size:.75rem;font-weight:750;text-decoration:none}
      .price-quick-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.price-quick-card{display:flex;min-width:0;flex-direction:column;padding:18px;border:1px solid var(--line,#d7d0c3);border-radius:14px;background:#fff}
      .price-quick-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-bottom:12px;border-bottom:1px solid var(--line,#d7d0c3)}.price-quick-card-head strong{font:500 1.7rem/1 Iowan Old Style,Baskerville,Georgia,serif}.price-quick-card-head span{padding:5px 8px;border-radius:999px;background:var(--ivory,#f2eee5);color:var(--muted,#64645e);font-size:.7rem;font-weight:800}
      .price-quick-line{display:grid;gap:3px;padding:13px 0;border-bottom:1px solid rgba(112,83,53,.13)}.price-quick-line small{color:var(--muted,#64645e);font-size:.73rem}.price-quick-line b{font-size:1rem;line-height:1.35}.price-quick-line em{color:var(--bronze-dark,#705335);font-size:.75rem;font-style:normal;font-weight:750}.price-quick-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:auto;padding-top:14px}.price-quick-actions a{display:flex;min-height:40px;align-items:center;justify-content:center;padding:0 9px;border:1px solid var(--line,#d7d0c3);border-radius:8px;font-size:.76rem;font-weight:800;text-align:center;text-decoration:none}.price-quick-actions a:first-child{border-color:var(--night,#171a18);background:var(--night,#171a18);color:#fff}
      .price-page .sale-history-card{border-color:var(--line,#d7d0c3);background:var(--paper,#fbf9f3);box-shadow:none}.price-page .sale-history-line{color:var(--bronze-dark,#705335)}
      @media(max-width:1050px){.customer-lookup-inner{grid-template-columns:1fr;gap:12px}.customer-lookup-groups{grid-template-columns:1fr 1.45fr .85fr}.price-quick-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
      @media(max-width:760px){.customer-lookup-inner{padding-block:14px}.customer-lookup-intro{display:flex;align-items:baseline;gap:8px}.customer-lookup-intro span{margin:0;flex:0 0 auto}.customer-lookup-intro strong{overflow:hidden;font-size:1rem;text-overflow:ellipsis;white-space:nowrap}.customer-lookup-groups{display:block}.customer-lookup-group{margin-top:9px}.customer-lookup-group:first-child{margin-top:0}.customer-lookup-group nav{margin-inline:-12px;padding-inline:12px}.price-quick-answer{padding:18px 14px;border-radius:14px}.price-quick-head{display:block}.price-quick-jumps{justify-content:flex-start;margin-top:12px}.price-quick-grid{grid-template-columns:1fr}.price-quick-card{padding:15px}.price-quick-line{grid-template-columns:minmax(0,1fr) auto;align-items:end;column-gap:10px}.price-quick-line small{grid-column:1/-1}.price-quick-line em{text-align:right}}
      @media(max-width:420px){.price-quick-actions{grid-template-columns:1fr}}
    `;
    document.head.append(style);
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

    const unitLinks=[['1PN','/can-ho-1-phong-ngu-lumi-hanoi/'],['2PN','/can-ho-2-phong-ngu-lumi-hanoi/'],['3PN','/can-ho-3-phong-ngu-lumi-hanoi/'],['4PN','/can-ho-4-phong-ngu-lumi-hanoi/'],['Duplex','/duplex-penthouse-lumi-hanoi/']];
    const towerLinks=[['S1','/mat-bang-lumi-hanoi/lumi-signature/s1/'],['S2','/mat-bang-lumi-hanoi/lumi-signature/s2/'],['S3','/mat-bang-lumi-hanoi/lumi-signature/s3/'],['S5','/mat-bang-lumi-hanoi/lumi-signature/s5/'],['S6','/mat-bang-lumi-hanoi/lumi-signature/s6/'],['P1','/mat-bang-lumi-hanoi/lumi-prestige/p1/'],['P2','/mat-bang-lumi-hanoi/lumi-prestige/p2/'],['E1','/mat-bang-lumi-hanoi/lumi-elite/e1/'],['E2','/mat-bang-lumi-hanoi/lumi-elite/e2/']];
    const renderLinks=items=>items.map(([label,href])=>`<a href="${href}">${label}</a>`).join('');
    lookup.innerHTML=`<div class="container customer-lookup-inner"><div class="customer-lookup-intro"><span>Tra cứu nhanh</span><strong>Mặt bằng → Layout → Căn đang giao dịch</strong></div><div class="customer-lookup-groups"><div class="customer-lookup-group"><small>Loại căn</small><nav aria-label="Chọn loại căn">${renderLinks(unitLinks)}</nav></div><div class="customer-lookup-group"><small>Tòa</small><nav aria-label="Chọn tòa">${renderLinks(towerLinks)}</nav></div><div class="customer-lookup-group customer-lookup-market"><small>Giao dịch</small><nav aria-label="Giao dịch Lumi Hanoi"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/gia-can-ho-lumi-hanoi/">Bảng giá</a></nav></div></div></div>`;

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
      const rows=card=>new Map([...card.querySelectorAll('tbody tr')].map(row=>{const cells=[...row.children].map(cell=>cell.textContent.trim());return [cells[0],cells];}));
      const saleRows=rows(saleCard);
      const rentRows=rows(rentCard);
      const types=['1PN','2PN','3PN','4PN'].filter(type=>{const sale=saleRows.get(type);const rent=rentRows.get(type);return Number(sale?.[1]||0)>0||Number(rent?.[1]||0)>0;});
      if(types.length){
        const section=document.createElement('section');
        section.className='price-quick-answer';
        section.dataset.priceQuickAnswer='true';
        const rentLinks={'1PN':'/cho-thue-can-ho-1-phong-ngu-lumi-hanoi/','2PN':'/cho-thue-can-ho-2-phong-ngu-lumi-hanoi/','3PN':'/cho-thue-can-ho-3-phong-ngu-lumi-hanoi/','4PN':'/cho-thue-can-ho-4-phong-ngu-lumi-hanoi/'};
        const typeCards=types.map(type=>{
          const sale=saleRows.get(type)||[]; const rent=rentRows.get(type)||[];
          const saleRange=sale[2]&&sale[2]!=='—'?sale[2]:'Chưa đủ dữ liệu'; const saleAvg=sale[3]&&sale[3]!=='—'?sale[3]:'—';
          const rentRange=rent[2]&&rent[2]!=='—'?rent[2]:'Chưa đủ dữ liệu'; const rentAvg=rent[3]&&rent[3]!=='—'?rent[3]:'—';
          return `<article class="price-quick-card"><div class="price-quick-card-head"><strong>${type}</strong><span>${Number(sale[1]||0)+Number(rent[1]||0)} tin</span></div><div class="price-quick-line"><small>Giá bán đang rao</small><b>${saleRange}</b><em>TB ${saleAvg}</em></div><div class="price-quick-line"><small>Giá thuê đang rao</small><b>${rentRange}</b><em>TB ${rentAvg}</em></div><div class="price-quick-actions"><a href="/mua-ban-lumi-hanoi/">Xem căn bán</a><a href="${rentLinks[type]||'/cho-thue-lumi-hanoi/'}">Xem căn thuê</a></div></article>`;
        }).join('');
        section.innerHTML=`<div class="price-quick-head"><div><p class="eyebrow">Giá nhanh theo nhu cầu</p><h2>Muốn mua hoặc thuê căn nào?</h2><p>Xem ngay khoảng giá rao hiện có theo loại căn. Số liệu lấy trực tiếp từ quỹ tin đã duyệt trên website.</p></div><div class="price-quick-jumps"><a href="#gia-ban-chi-tiet">Bảng giá bán chi tiết ↓</a><a href="#gia-thue-chi-tiet">Bảng giá thuê chi tiết ↓</a></div></div><div class="price-quick-grid">${typeCards}</div>`;
        const history=document.querySelector('.sale-history-card');
        if(history)history.insertAdjacentElement('beforebegin',section); else saleCard.insertAdjacentElement('beforebegin',section);
      }
    }
  }
})();
