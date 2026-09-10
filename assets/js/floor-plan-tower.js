(()=>{
  const app=document.querySelector('[data-floor-plan-app]');
  if(!app)return;

  const tower=String(app.dataset.tower||'').trim().toUpperCase();
  const primaryPlan=app.querySelector('[data-primary-floor-plan]');
  const primaryAnchor=primaryPlan?.id||'';
  const phaseName={signature:'Signature',prestige:'Prestige',elite:'Elite'};
  const phaseOrder=['signature','prestige','elite'];
  const towerOrder=['S1','S2','S3','S5','S6','P1','P2','E1','E2'];
  const esc=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const track=(eventName,params={})=>{try{window.LumiAnalytics?.track?.(eventName,{tower,...params})}catch{}};

  const injectExplorerStyles=()=>{
    if(document.querySelector('link[data-floor-explorer-css]'))return;
    const link=document.createElement('link');
    link.rel='stylesheet';
    link.href='/assets/css/floor-plan-explorer.css?v=20260910-1';
    link.dataset.floorExplorerCss='true';
    document.head.append(link);
  };
  injectExplorerStyles();

  const planFloors=label=>{
    const normalized=String(label||'').replace(/^Tầng\s*/i,'').replace(/[–—]/g,'-');
    const floors=new Set();
    normalized.split(',').map(part=>part.trim()).filter(Boolean).forEach(part=>{
      const range=part.match(/^(\d+)\s*-\s*(\d+)$/);
      if(range){
        const start=Number(range[1]),end=Number(range[2]);
        if(Number.isFinite(start)&&Number.isFinite(end)&&end-start<=60){
          for(let n=Math.min(start,end);n<=Math.max(start,end);n++)floors.add(n);
        }
        return;
      }
      const value=Number(part.match(/\d+/)?.[0]);
      if(Number.isFinite(value))floors.add(value);
    });
    return floors;
  };

  const bindLightbox=()=>{
    const links=[...app.querySelectorAll('[data-lightbox]')];
    if(!links.length)return;
    let dialog=document.querySelector('dialog[data-dynamic-floor-lightbox]');
    if(!dialog){
      dialog=document.createElement('dialog');
      dialog.className='lightbox';
      dialog.dataset.dynamicFloorLightbox='true';
      dialog.setAttribute('aria-label','Xem bản vẽ kích thước lớn');
      dialog.innerHTML='<div class="lightbox-toolbar"><button type="button" data-zoom-out>Zoom −</button><button type="button" data-zoom-in>Zoom +</button><button type="button" data-zoom-fit>Fit / Reset</button><button type="button" class="lightbox-close">Close ×</button></div><div class="lightbox-stage"><img alt=""></div><p class="lightbox-caption"></p>';
      document.body.append(dialog);
      const stage=dialog.querySelector('.lightbox-stage');
      const img=dialog.querySelector('img');
      const caption=dialog.querySelector('.lightbox-caption');
      const close=dialog.querySelector('.lightbox-close');
      let zoom=1,fw=0,fh=0,opener=null;
      const fitSize=()=>{
        if(!img.naturalWidth||!img.naturalHeight)return;
        const scale=Math.min(stage.clientWidth/img.naturalWidth,stage.clientHeight/img.naturalHeight,1);
        fw=Math.round(img.naturalWidth*scale);fh=Math.round(img.naturalHeight*scale);
      };
      const render=()=>{
        if(!fw||!fh)return;
        const z=zoom>1;
        stage.classList.toggle('is-zoomed',z);
        img.classList.toggle('is-fit',!z);
        img.style.width=`${Math.round(fw*zoom)}px`;
        img.style.height=`${Math.round(fh*zoom)}px`;
        if(!z)stage.scrollTo(0,0);
      };
      const fit=()=>{zoom=1;fitSize();render()};
      img.addEventListener('load',fit);
      dialog.querySelector('[data-zoom-in]').addEventListener('click',()=>{zoom=Math.min(4,zoom+.25);render()});
      dialog.querySelector('[data-zoom-out]').addEventListener('click',()=>{zoom=Math.max(1,zoom-.25);render()});
      dialog.querySelector('[data-zoom-fit]').addEventListener('click',fit);
      close.addEventListener('click',()=>dialog.close());
      dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close()});
      dialog.addEventListener('close',()=>{img.removeAttribute('src');zoom=1;fw=fh=0;opener?.focus()});
      dialog._open=link=>{
        opener=link;
        img.alt=link.dataset.lightboxAlt||link.querySelector('img')?.alt||'';
        caption.textContent=link.dataset.lightboxCaption||'';
        caption.hidden=!caption.textContent;
        dialog.showModal();
        img.src=link.href;
        close.focus();
        track('floor_plan_open_large',{floor_group:link.closest('.floor-plan-section')?.dataset.floorLabel||''});
      };
    }
    links.forEach(link=>{
      if(link.dataset.dynamicLightboxBound)return;
      link.dataset.dynamicLightboxBound='true';
      link.addEventListener('click',e=>{e.preventDefault();dialog._open(link)});
    });
  };

  fetch('/assets/data/floor-plans.json',{cache:'no-cache'})
    .then(r=>{if(!r.ok)throw new Error('manifest');return r.json()})
    .then(data=>{
      const item=data.towers&&data.towers[tower];
      if(!item)throw new Error('tower');
      const phase=phaseName[item.phase]||item.phase;
      const towerUrl=t=>{
        const target=data.towers?.[t];
        if(!target)return '/mat-bang-lumi-hanoi/';
        return `/mat-bang-lumi-hanoi/lumi-${target.phase}/${t.toLowerCase()}/`;
      };

      const towerGroups=phaseOrder.map(phaseKey=>{
        const towers=towerOrder.filter(code=>data.towers?.[code]?.phase===phaseKey);
        return `<div class="floor-explorer-phase"><span>${esc(phaseName[phaseKey]||phaseKey)}</span><div>${towers.map(code=>`<a href="${towerUrl(code)}"${code===tower?' aria-current="page"':''}>${esc(code)}</a>`).join('')}</div></div>`;
      }).join('');

      const explorer=document.createElement('section');
      explorer.className='floor-explorer';
      explorer.setAttribute('aria-label',`Tra cứu nhanh mặt bằng tòa ${tower}`);
      explorer.innerHTML=`
        <div class="floor-explorer-top">
          <div>
            <p class="eyebrow">Tra cứu nhanh · 9 tòa</p>
            <h2>Chọn tòa và tầng cần xem</h2>
            <p>Nhập số tầng thực tế, hệ thống sẽ mở đúng nhóm bản vẽ thay vì phải tự dò danh sách.</p>
          </div>
          <a class="floor-explorer-all" href="/mat-bang-lumi-hanoi/">Toàn bộ mặt bằng →</a>
        </div>
        <div class="floor-explorer-towers" aria-label="Chọn tòa Lumi Hanoi">${towerGroups}</div>
        <form class="floor-explorer-lookup" data-floor-lookup>
          <label for="floor-number-${esc(tower.toLowerCase())}">Tôi cần xem tầng</label>
          <div class="floor-explorer-lookup-row">
            <input id="floor-number-${esc(tower.toLowerCase())}" name="floor" type="number" inputmode="numeric" min="1" max="60" placeholder="VD: 27" aria-describedby="floor-lookup-result-${esc(tower.toLowerCase())}">
            <button type="submit">Tìm mặt bằng</button>
          </div>
          <p id="floor-lookup-result-${esc(tower.toLowerCase())}" class="floor-lookup-result" data-floor-lookup-result aria-live="polite">Đang xem tòa ${esc(tower)} · ${esc(phase)}</p>
        </form>`;

      const nav=item.plans.map(p=>`<a href="#${esc(p.anchor)}" data-floor-target="${esc(p.anchor)}">${esc(p.label)}</a>`).join('');
      const plans=item.plans.filter(p=>p.anchor!==primaryAnchor).map((p,index)=>{
        const src=p.asset||`https://drive.google.com/thumbnail?id=${encodeURIComponent(p.driveId)}&sz=w2400`;
        return `<section class="floor-plan-section" id="${esc(p.anchor)}" data-tower="${esc(tower)}" data-floor-label="${esc(p.label)}" data-plan-index="${index}"><div class="plan-section-head"><div><p class="eyebrow">${esc(phase)} · ${esc(tower)}</p><h2>${esc(tower)} — ${esc(p.label)}</h2></div></div><figure class="figure floor-plan-figure"><a href="${esc(src)}" data-lightbox data-lightbox-alt="Mặt bằng tòa ${esc(tower)} Lumi Hanoi — ${esc(p.label)}" data-lightbox-caption="Tòa ${esc(tower)} — ${esc(p.label)}"><img class="figure-image floor-plan-image" src="${esc(src)}" width="${esc(p.width||2400)}" height="${esc(p.height||3200)}" alt="Mặt bằng tòa ${esc(tower)} Lumi Hanoi — ${esc(p.label)}" loading="lazy" decoding="async"></a><figcaption class="figure-caption">Mặt bằng ${esc(tower)} — ${esc(p.label)}.</figcaption></figure></section>`;
      }).join('');

      app.innerHTML=`<nav class="floor-plan-index tower-floor-index sticky-floor-index" aria-label="Chọn nhóm tầng tòa ${esc(tower)}"><strong>Nhóm tầng</strong>${nav}</nav><div class="floor-viewer-status" data-floor-viewer-status><div><span>Đang xem</span><strong></strong></div><div class="floor-viewer-actions"><button type="button" data-floor-prev aria-label="Nhóm tầng trước">← Trước</button><button type="button" data-floor-next aria-label="Nhóm tầng sau">Sau →</button></div></div>${plans}`;
      app.prepend(explorer);

      if(primaryPlan){
        const primaryMeta=item.plans.find(p=>p.anchor===primaryAnchor);
        if(primaryMeta){
          primaryPlan.dataset.floorLabel=primaryMeta.label;
          primaryPlan.dataset.planIndex=String(item.plans.findIndex(p=>p.anchor===primaryAnchor));
        }
        primaryPlan.querySelectorAll('[data-lightbox]').forEach(link=>{link.dataset.dynamicLightboxBound='true';});
        app.querySelector('.floor-viewer-status')?.insertAdjacentElement('afterend',primaryPlan);
      }

      const sectionNodes=[...app.querySelectorAll('.floor-plan-section')];
      const sections=item.plans.map(plan=>sectionNodes.find(node=>node.id===plan.anchor)).filter(Boolean);
      const navLinks=[...app.querySelectorAll('[data-floor-target]')];
      const status=app.querySelector('[data-floor-viewer-status] strong');
      const prev=app.querySelector('[data-floor-prev]');
      const next=app.querySelector('[data-floor-next]');
      const lookup=app.querySelector('[data-floor-lookup]');
      const lookupResult=app.querySelector('[data-floor-lookup-result]');

      const activate=(anchor,{scroll=false,replaceHash=false,source='selector'}={})=>{
        const section=sections.find(node=>node.id===anchor)||sections[0];
        if(!section)return;
        sections.forEach(node=>node.classList.toggle('is-active',node===section));
        navLinks.forEach(link=>link.classList.toggle('is-current',link.dataset.floorTarget===section.id));
        const label=section.dataset.floorLabel||section.querySelector('h2')?.textContent||'';
        if(status)status.textContent=`${tower} · ${label}`;
        const index=sections.indexOf(section);
        if(prev)prev.disabled=index<=0;
        if(next)next.disabled=index>=sections.length-1;
        if(replaceHash&&history.replaceState)history.replaceState(null,'',`#${section.id}`);
        else if(!replaceHash&&location.hash!==`#${section.id}`&&history.pushState)history.pushState(null,'',`#${section.id}`);
        if(scroll)app.querySelector('.floor-viewer-status')?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
        track('floor_plan_select',{floor_group:label,source});
      };

      navLinks.forEach(link=>link.addEventListener('click',event=>{
        event.preventDefault();
        activate(link.dataset.floorTarget,{scroll:true,source:'group_selector'});
      }));
      prev?.addEventListener('click',()=>{
        const current=sections.findIndex(node=>node.classList.contains('is-active'));
        if(current>0)activate(sections[current-1].id,{scroll:true,source:'previous'});
      });
      next?.addEventListener('click',()=>{
        const current=sections.findIndex(node=>node.classList.contains('is-active'));
        if(current>=0&&current<sections.length-1)activate(sections[current+1].id,{scroll:true,source:'next'});
      });

      app.querySelectorAll('.floor-explorer-towers a').forEach(link=>link.addEventListener('click',()=>{
        track('floor_plan_tower_switch',{target_tower:link.textContent.trim()});
      }));

      lookup?.addEventListener('submit',event=>{
        event.preventDefault();
        const value=Number(new FormData(lookup).get('floor'));
        if(!Number.isFinite(value)||value<1){
          lookupResult.textContent='Anh nhập số tầng cần xem, ví dụ 27.';
          return;
        }
        const match=item.plans.find(plan=>planFloors(plan.label).has(value));
        if(!match){
          lookupResult.textContent=`Chưa có nhóm bản vẽ xác thực cho tầng ${value} của ${tower}. Hãy chọn thủ công trong danh sách nhóm tầng.`;
          track('floor_plan_floor_lookup',{floor:value,matched:false});
          return;
        }
        lookupResult.innerHTML=`Tầng <strong>${esc(value)}</strong> thuộc nhóm <strong>${esc(match.label)}</strong>.`;
        activate(match.anchor,{scroll:true,source:'floor_lookup'});
        track('floor_plan_floor_lookup',{floor:value,matched:true,floor_group:match.label});
      });

      const hashAnchor=location.hash.replace(/^#/,'');
      const initial=item.plans.some(p=>p.anchor===hashAnchor)?hashAnchor:item.plans[0]?.anchor;
      activate(initial,{replaceHash:!hashAnchor,source:'initial'});
      window.addEventListener('hashchange',()=>{
        const anchor=location.hash.replace(/^#/,'');
        if(item.plans.some(p=>p.anchor===anchor))activate(anchor,{source:'hash'});
      });
      bindLightbox();
    })
    .catch(()=>{
      const message='Không tải được thư viện mặt bằng lúc này. Vui lòng quay lại trang tổng hợp mặt bằng.';
      if(app.querySelector('[data-floor-plan-static-index]')){
        const notice=document.createElement('p');notice.className='notice';notice.textContent=message;app.append(notice);
      }else app.innerHTML=`<p class="notice">${message}</p>`;
    });
})();

if(document.querySelector('[data-floor-plan-app]'))import('/assets/js/floor-plan-marketplace.js?v=20260909-bridge1');
