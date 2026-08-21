(()=>{
  const button=document.querySelector('[data-nav-toggle]');
  const nav=document.querySelector('[data-nav-links]');
  if(button&&nav){
    button.addEventListener('click',()=>{
      const open=nav.getAttribute('data-open')==='true';
      nav.setAttribute('data-open',String(!open));
      button.setAttribute('aria-expanded',String(!open));
    });
    nav.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>{
      nav.setAttribute('data-open','false');
      button.setAttribute('aria-expanded','false');
    }));
    document.addEventListener('keydown',event=>{
      if(event.key==='Escape'){
        nav.setAttribute('data-open','false');
        button.setAttribute('aria-expanded','false');
        button.focus();
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
    let opener; let zoom=1;
    const fit=()=>{zoom=1;image.style.width='';image.style.height='';image.classList.add('is-fit');stage.scrollTo(0,0);};
    const setZoom=next=>{zoom=Math.min(4,Math.max(.5,next));image.classList.remove('is-fit');image.style.width=`${image.naturalWidth*zoom}px`;image.style.height='auto';};
    const closeDialog=()=>dialog.close();
    lightboxLinks.forEach(link=>link.addEventListener('click',event=>{
      event.preventDefault(); opener=link; image.src=link.href;
      image.alt=link.dataset.lightboxAlt||link.querySelector('img')?.alt||'';
      caption.textContent=link.dataset.lightboxCaption||''; caption.hidden=!caption.textContent;
      fit(); dialog.showModal(); close.focus();
    }));
    dialog.querySelector('[data-zoom-in]').addEventListener('click',()=>setZoom(zoom+.25));
    dialog.querySelector('[data-zoom-out]').addEventListener('click',()=>setZoom(zoom-.25));
    dialog.querySelector('[data-zoom-fit]').addEventListener('click',fit);
    close.addEventListener('click',closeDialog);
    dialog.addEventListener('click',event=>{if(event.target===dialog)closeDialog();});
    dialog.addEventListener('close',()=>{image.removeAttribute('src');fit();opener?.focus();});
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
