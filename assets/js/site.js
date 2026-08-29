(()=>{
  // Load the final responsive cascade after the legacy/site stylesheet on every page.
  // Keeping this in site.js avoids touching dozens of static HTML files while the
  // CSS remains a normal local asset that browsers can cache.
  if(!document.querySelector('link[data-responsive-v9]')){
    const responsiveStyles=document.createElement('link');
    responsiveStyles.rel='stylesheet';
    responsiveStyles.href='/assets/css/responsive-v9.css?v=20260824';
    responsiveStyles.dataset.responsiveV9='true';
    document.head.append(responsiveStyles);
  }

  const button=document.querySelector('[data-nav-toggle]');
  const nav=document.querySelector('[data-nav-links]');
  if(button&&nav){
    const makeDropdown=(label,links,rightAligned=false)=>{
      const details=document.createElement('details');
      details.className='nav-dropdown';
      const summary=document.createElement('summary');
      summary.textContent=label;
      const menu=document.createElement('div');
      menu.className=`nav-dropdown-menu${rightAligned?' nav-dropdown-menu--right':''}`;
      details.append(summary,menu);
      links[0].before(details);
      links.forEach(link=>menu.append(link));
      return details;
    };
    const dropdownByLabel=label=>[...nav.querySelectorAll('.nav-dropdown')].find(item=>item.querySelector('summary')?.textContent.trim()===label);
    const topLevelLink=href=>[...nav.children].find(item=>item.matches?.(`a[href="${href}"]`));
    if(!dropdownByLabel('Phân khu')){
      const phaseLinks=['/lumi-signature/','/lumi-prestige/','/lumi-elite/'].map(topLevelLink).filter(Boolean);
      if(phaseLinks.length===3)makeDropdown('Phân khu',phaseLinks);
    }
    if(!dropdownByLabel('Giao dịch')){
      const transactionLink=topLevelLink('/mua-ban-lumi-hanoi/');
      if(transactionLink){
        transactionLink.textContent='Mua bán';
        const rentLink=document.createElement('a');
        rentLink.href='/cho-thue-lumi-hanoi/';
        rentLink.textContent='Cho thuê';
        if(location.pathname==='/mua-ban-lumi-hanoi/')transactionLink.setAttribute('aria-current','page');
        if(location.pathname==='/cho-thue-lumi-hanoi/')rentLink.setAttribute('aria-current','page');
        transactionLink.after(rentLink);
        makeDropdown('Giao dịch',[transactionLink,rentLink]);
      }
    }
    const transactionDropdown=[...nav.querySelectorAll('.nav-dropdown')].find(item=>item.querySelector('summary')?.textContent.trim()==='Giao dịch');
    if(transactionDropdown&&!transactionDropdown.querySelector('a[href="/dang-tin-lumi-hanoi/"]')){
      const submitLink=document.createElement('a');
      submitLink.href='/dang-tin-lumi-hanoi/';
      submitLink.textContent='Đăng tin';
      if(location.pathname==='/dang-tin-lumi-hanoi/')submitLink.setAttribute('aria-current','page');
      transactionDropdown.querySelector('.nav-dropdown-menu')?.append(submitLink);
    }
    const overviewLink=topLevelLink('/tong-quan-lumi-hanoi/');
    if(transactionDropdown&&overviewLink){
      overviewLink.after(transactionDropdown);
      transactionDropdown.querySelector('.nav-dropdown-menu')?.classList.remove('nav-dropdown-menu--right');
    }
    const dropdowns=[...nav.querySelectorAll('.nav-dropdown')];
    dropdowns.forEach(dropdown=>dropdown.addEventListener('toggle',()=>{
      if(dropdown.open)dropdowns.filter(item=>item!==dropdown).forEach(item=>{item.open=false;});
    }));
    document.addEventListener('click',event=>{
      if(!nav.contains(event.target))dropdowns.forEach(item=>{item.open=false;});
    });
    button.addEventListener('click',()=>{
      const open=nav.getAttribute('data-open')==='true';
      nav.setAttribute('data-open',String(!open));
      button.setAttribute('aria-expanded',String(!open));
    });
    nav.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>{
      dropdowns.forEach(item=>{item.open=false;});
      nav.setAttribute('data-open','false');
      button.setAttribute('aria-expanded','false');
    }));
    document.addEventListener('keydown',event=>{
      if(event.key==='Escape'){
        dropdowns.forEach(item=>{item.open=false;});
        nav.setAttribute('data-open','false');
        button.setAttribute('aria-expanded','false');
        if(getComputedStyle(button).display!=='none')button.focus();
      }
    });
  }
  document.querySelectorAll('[data-year]').forEach(el=>{el.textContent=new Date().getFullYear();});

  const reveals=[...document.querySelectorAll('[data-reveal]')];
  if(reveals.length&&'IntersectionObserver' in window&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
    document.documentElement.classList.add('reveal-ready');
    const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('is-visible');observer.unobserve(entry.target);}}),{rootMargin:'0px 0px -8%'});
    reveals.forEach(element=>observer.observe(element));
  }

  const lightboxLinks=[...document.querySelectorAll('[data-lightbox]')];
  if(lightboxLinks.length){
    const dialog=document.createElement('dialog');
    dialog.className='lightbox';
    dialog.setAttribute('aria-label','Xem bản vẽ kích thước lớn');
    dialog.innerHTML='<div class="lightbox-toolbar" aria-label="Điều khiển bản vẽ"><button type="button" data-zoom-out aria-label="Thu nhỏ">Zoom −</button><button type="button" data-zoom-in aria-label="Phóng to">Zoom +</button><button type="button" data-zoom-fit>Fit / Reset</button><button class="lightbox-close" type="button" aria-label="Đóng bản vẽ">Close ×</button></div><div class="lightbox-stage"><img alt=""></div><p class="lightbox-caption"></p>';
    document.body.append(dialog);
    const stage=dialog.querySelector('.lightbox-stage');
    const image=dialog.querySelector('img');
    const caption=dialog.querySelector('.lightbox-caption');
    const close=dialog.querySelector('.lightbox-close');
    const zoomControls=[...dialog.querySelectorAll('[data-zoom-in],[data-zoom-out],[data-zoom-fit]')];
    let opener; let zoom=1; let fittedWidth=0; let fittedHeight=0;
    const sizeToFit=()=>{
      if(!image.naturalWidth||!image.naturalHeight)return;
      const availableWidth=stage.clientWidth;
      const availableHeight=stage.clientHeight;
      const fitScale=Math.min(availableWidth/image.naturalWidth,availableHeight/image.naturalHeight,1);
      fittedWidth=Math.round(image.naturalWidth*fitScale);
      fittedHeight=Math.round(image.naturalHeight*fitScale);
    };
    const renderZoom=()=>{
      if(!fittedWidth||!fittedHeight)return;
      const zoomed=zoom>1;
      stage.classList.toggle('is-zoomed',zoomed);
      image.classList.toggle('is-fit',!zoomed);
      image.style.width=`${Math.round(fittedWidth*zoom)}px`;
      image.style.height=`${Math.round(fittedHeight*zoom)}px`;
      if(!zoomed)stage.scrollTo(0,0);
    };
    const fit=()=>{zoom=1;sizeToFit();renderZoom();};
    const setZoom=next=>{if(!fittedWidth)return;zoom=Math.min(4,Math.max(1,next));renderZoom();};
    const closeDialog=()=>dialog.close();
    zoomControls.forEach(control=>{control.disabled=true;});
    image.addEventListener('load',()=>{fit();zoomControls.forEach(control=>{control.disabled=false;});});
    lightboxLinks.forEach(link=>link.addEventListener('click',event=>{
      event.preventDefault(); opener=link;
      image.alt=link.dataset.lightboxAlt||link.querySelector('img')?.alt||'';
      caption.textContent=link.dataset.lightboxCaption||''; caption.hidden=!caption.textContent;
      zoom=1; fittedWidth=0; fittedHeight=0; stage.classList.remove('is-zoomed'); image.classList.add('is-fit');
      zoomControls.forEach(control=>{control.disabled=true;});
      dialog.showModal(); image.src=link.href; close.focus();
    }));
    dialog.querySelector('[data-zoom-in]').addEventListener('click',()=>setZoom(zoom+.25));
    dialog.querySelector('[data-zoom-out]').addEventListener('click',()=>setZoom(zoom-.25));
    dialog.querySelector('[data-zoom-fit]').addEventListener('click',fit);
    close.addEventListener('click',closeDialog);
    dialog.addEventListener('click',event=>{if(event.target===dialog)closeDialog();});
    dialog.addEventListener('close',()=>{image.removeAttribute('src');zoom=1;fittedWidth=0;fittedHeight=0;stage.classList.remove('is-zoomed');opener?.focus();});
  }

  const layoutFilters=[...document.querySelectorAll('[data-layout-filter]')];
  const layoutCards=[...document.querySelectorAll('[data-layout-card]')];
  const layoutCount=document.querySelector('[data-layout-count]');
  if(layoutFilters.length&&layoutCards.length){
    const active={bedrooms:'all',size:'all'};
    const apply=()=>{
      let shown=0;
      layoutCards.forEach(card=>{
        const visible=(active.bedrooms==='all'||card.dataset.bedrooms===active.bedrooms)&&(active.size==='all'||card.dataset.size===active.size);
        card.hidden=!visible;
        if(visible)shown++;
      });
      if(layoutCount)layoutCount.textContent=`Hiển thị ${shown} / ${layoutCards.length} layout`;
    };
    layoutFilters.forEach(button=>button.addEventListener('click',()=>{
      const group=button.dataset.layoutFilter;
      active[group]=button.dataset.value;
      layoutFilters.filter(item=>item.dataset.layoutFilter===group).forEach(item=>item.setAttribute('aria-pressed',String(item===button)));
      apply();
    }));
    apply();
  }
})();
if(document.querySelector('.tower-floor-index')||document.querySelector('[data-floor-plan-app]')){const floorPickerScript=document.createElement('script');floorPickerScript.src='/assets/js/floor-plan-mobile.js';document.head.append(floorPickerScript)}
