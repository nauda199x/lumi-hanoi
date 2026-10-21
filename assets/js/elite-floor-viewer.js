(()=>{
  // Enhance existing Elite HTML in place: preserve every original drawing and SEO heading.
  const article=document.querySelector('.tower-lookup-main');
  const sections=[...article?.querySelectorAll('section.floor-plan-section[data-tower]')||[]];
  if(!article||sections.length<2)return;
  const tower=String(sections[0].dataset.tower||'').toUpperCase();
  if(!/^E[12]$/.test(tower))return;
  const nav=article.querySelector('.tower-floor-index');
  const css=document.createElement('link');
  css.rel='stylesheet';css.href='/assets/css/floor-plan-explorer.css?v=20261021-ux1';document.head.append(css);
  const toolbar=document.createElement('div');
  toolbar.className='floor-viewer-status elite-floor-chooser';
  toolbar.setAttribute('aria-label',`Chọn nhóm mặt bằng ${tower}`);
  const options=sections.map(section=>{
    const name=section.querySelector('h2')?.textContent?.replace(new RegExp('^'+tower+'\\s*[—–-]\\s*'), '')||section.id;
    return {id:section.id,name};
  });
  const label=document.createElement('label');label.className='floor-viewer-jump';
  const caption=document.createElement('span');caption.textContent=`Mặt bằng ${tower} · Chọn nhóm tầng`;
  const select=document.createElement('select');select.setAttribute('aria-label',`Chọn nhóm tầng tòa ${tower}`);
  options.forEach(({id,name})=>{const option=document.createElement('option');option.value=id;option.textContent=name;select.add(option);});
  label.append(caption,select);
  const buttons=document.createElement('div');buttons.className='floor-viewer-actions';
  const makeButton=(text,desc)=>{const button=document.createElement('button');button.type='button';button.textContent=text;button.setAttribute('aria-label',desc);return button;};
  const big=makeButton('⤢ Xem lớn','Phóng to bản vẽ đang chọn');
  const prev=makeButton('← Trước','Nhóm tầng trước');
  const next=makeButton('Sau →','Nhóm tầng tiếp theo');
  buttons.append(big,prev,next);toolbar.append(label,buttons);
  sections[0].insertAdjacentElement('beforebegin',toolbar);
  const activate=(anchor,{scroll=false,updateHash=true}={})=>{
    const index=Math.max(0,sections.findIndex(section=>section.id===anchor));
    sections.forEach((section,i)=>section.classList.toggle('is-active',i===index));
    select.value=sections[index].id;prev.disabled=index===0;next.disabled=index===sections.length-1;
    nav?.querySelectorAll('a[href^="#"]').forEach(a=>{
      const selected=a.getAttribute('href')===`#${sections[index].id}`;
      if(selected)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');
    });
    if(updateHash&&history.replaceState)history.replaceState(null,'',`#${sections[index].id}`);
    if(scroll)toolbar.scrollIntoView({block:'start',behavior:'auto'});
    window.LumiAnalytics?.track?.('floor_plan_select',{tower,floor_group:options[index].name,source:'elite_viewer'});
  };
  select.addEventListener('change',()=>activate(select.value,{scroll:true}));
  prev.addEventListener('click',()=>{const i=sections.findIndex(s=>s.classList.contains('is-active'));if(i>0)activate(sections[i-1].id);});
  next.addEventListener('click',()=>{const i=sections.findIndex(s=>s.classList.contains('is-active'));if(i<sections.length-1)activate(sections[i+1].id);});
  big.addEventListener('click',()=>sections.find(s=>s.classList.contains('is-active'))?.querySelector('a[data-lightbox]')?.click());
  nav?.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',event=>{
    const target=a.getAttribute('href').slice(1);
    if(!sections.some(section=>section.id===target))return;
    event.preventDefault();activate(target,{scroll:true});
  }));
  window.addEventListener('hashchange',()=>{
    const anchor=decodeURIComponent(location.hash.slice(1));
    if(sections.some(section=>section.id===anchor))activate(anchor,{updateHash:false});
  });
  const initial=decodeURIComponent(location.hash.slice(1));
  activate(initial,{updateHash:false});
  // Fallback: without this class all static sections remain visible if enhancement fails.
  article.classList.add('elite-floor-ready');
})();