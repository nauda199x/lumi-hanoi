(()=>{
  const TRACK_SELECTOR=".detail-gallery-track";
  const bound=new WeakSet();
  let overlay=null;
  let stage=null;
  let lightboxImage=null;
  let countNode=null;
  let zoomNode=null;
  let prevButton=null;
  let nextButton=null;
  let closeButton=null;
  let zoomInButton=null;
  let zoomOutButton=null;
  let resetButton=null;
  let activeImages=[];
  let activeIndex=0;
  let lastFocus=null;
  let scale=1;
  let translateX=0;
  let translateY=0;
  let pointerStart=null;
  let dragStart=null;
  let pinchStart=null;
  const pointers=new Map();

  const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
  const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);

  const ensureLightbox=()=>{
    if(overlay)return;
    overlay=document.createElement("div");
    overlay.className="detail-lightbox";
    overlay.hidden=true;
    overlay.setAttribute("role","dialog");
    overlay.setAttribute("aria-modal","true");
    overlay.setAttribute("aria-label","Xem ảnh căn hộ toàn màn hình");
    overlay.innerHTML=`
      <div class="detail-lightbox-toolbar">
        <div class="detail-lightbox-status">
          <span data-lightbox-count>1/1</span>
          <span data-lightbox-zoom>100%</span>
        </div>
        <div class="detail-lightbox-tools" aria-label="Điều khiển phóng to ảnh">
          <button type="button" data-lightbox-zoom-out aria-label="Thu nhỏ ảnh">−</button>
          <button type="button" data-lightbox-reset aria-label="Đưa ảnh về kích thước ban đầu">100%</button>
          <button type="button" data-lightbox-zoom-in aria-label="Phóng to ảnh">+</button>
          <button type="button" class="detail-lightbox-close" data-lightbox-close aria-label="Đóng ảnh">×</button>
        </div>
      </div>
      <div class="detail-lightbox-stage" data-lightbox-stage>
        <button type="button" class="detail-lightbox-nav detail-lightbox-nav--prev" data-lightbox-prev aria-label="Ảnh trước">‹</button>
        <img data-lightbox-image alt="">
        <button type="button" class="detail-lightbox-nav detail-lightbox-nav--next" data-lightbox-next aria-label="Ảnh tiếp theo">›</button>
      </div>
      <p class="detail-lightbox-hint">Chạm 2 lần hoặc dùng 2 ngón tay để phóng to · Kéo ảnh khi đã phóng to</p>
    `;
    document.body.append(overlay);
    stage=overlay.querySelector("[data-lightbox-stage]");
    lightboxImage=overlay.querySelector("[data-lightbox-image]");
    countNode=overlay.querySelector("[data-lightbox-count]");
    zoomNode=overlay.querySelector("[data-lightbox-zoom]");
    prevButton=overlay.querySelector("[data-lightbox-prev]");
    nextButton=overlay.querySelector("[data-lightbox-next]");
    closeButton=overlay.querySelector("[data-lightbox-close]");
    zoomInButton=overlay.querySelector("[data-lightbox-zoom-in]");
    zoomOutButton=overlay.querySelector("[data-lightbox-zoom-out]");
    resetButton=overlay.querySelector("[data-lightbox-reset]");

    const applyTransform=(animate=false)=>{
      if(!lightboxImage)return;
      lightboxImage.classList.toggle("is-animating",animate);
      lightboxImage.style.transform=`translate3d(${translateX}px,${translateY}px,0) scale(${scale})`;
      stage.classList.toggle("is-zoomed",scale>1.01);
      zoomNode.textContent=`${Math.round(scale*100)}%`;
      zoomOutButton.disabled=scale<=1.01;
      zoomInButton.disabled=scale>=3.99;
      if(animate)setTimeout(()=>lightboxImage?.classList.remove("is-animating"),180);
    };

    const resetTransform=(animate=false)=>{
      scale=1;
      translateX=0;
      translateY=0;
      applyTransform(animate);
    };

    const setScale=(nextScale,animate=true)=>{
      const target=clamp(nextScale,1,4);
      if(target===1){
        resetTransform(animate);
        return;
      }
      scale=target;
      translateX=clamp(translateX,-stage.clientWidth*(scale-1)/2,stage.clientWidth*(scale-1)/2);
      translateY=clamp(translateY,-stage.clientHeight*(scale-1)/2,stage.clientHeight*(scale-1)/2);
      applyTransform(animate);
    };

    const render=()=>{
      const source=activeImages[activeIndex];
      if(!source)return;
      lightboxImage.src=source.currentSrc||source.src;
      lightboxImage.alt=source.alt||`Ảnh căn hộ ${activeIndex+1}`;
      countNode.textContent=`${activeIndex+1}/${activeImages.length}`;
      prevButton.disabled=activeIndex===0;
      nextButton.disabled=activeIndex===activeImages.length-1;
      resetTransform(false);
    };

    const go=direction=>{
      const target=activeIndex+direction;
      if(target<0||target>=activeImages.length)return;
      activeIndex=target;
      render();
    };

    const close=()=>{
      if(!overlay||overlay.hidden)return;
      overlay.hidden=true;
      document.body.classList.remove("detail-lightbox-open");
      pointers.clear();
      lastFocus?.focus?.({preventScroll:true});
    };

    const open=(images,index,opener)=>{
      activeImages=images;
      activeIndex=clamp(index,0,Math.max(0,images.length-1));
      lastFocus=opener||document.activeElement;
      render();
      overlay.hidden=false;
      document.body.classList.add("detail-lightbox-open");
      closeButton.focus({preventScroll:true});
    };

    overlay._lumiOpen=open;

    closeButton.addEventListener("click",close);
    prevButton.addEventListener("click",()=>go(-1));
    nextButton.addEventListener("click",()=>go(1));
    zoomInButton.addEventListener("click",()=>setScale(scale+.5));
    zoomOutButton.addEventListener("click",()=>setScale(scale-.5));
    resetButton.addEventListener("click",()=>resetTransform(true));
    overlay.addEventListener("click",event=>{if(event.target===overlay)close();});

    stage.addEventListener("dblclick",event=>{
      if(event.target!==lightboxImage)return;
      setScale(scale>1.01?1:2.5,true);
    });

    stage.addEventListener("wheel",event=>{
      if(!event.ctrlKey&&!event.metaKey)return;
      event.preventDefault();
      setScale(scale+(event.deltaY<0?.25:-.25),false);
    },{passive:false});

    stage.addEventListener("pointerdown",event=>{
      if(event.target.closest("button"))return;
      stage.setPointerCapture?.(event.pointerId);
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size===1){
        pointerStart={x:event.clientX,y:event.clientY,time:Date.now()};
        dragStart={x:event.clientX,y:event.clientY,translateX,translateY};
      }else if(pointers.size===2){
        const [a,b]=[...pointers.values()];
        pinchStart={distance:distance(a,b),scale};
      }
    });

    stage.addEventListener("pointermove",event=>{
      if(!pointers.has(event.pointerId))return;
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size===2&&pinchStart){
        event.preventDefault();
        const [a,b]=[...pointers.values()];
        const ratio=distance(a,b)/(pinchStart.distance||1);
        scale=clamp(pinchStart.scale*ratio,1,4);
        if(scale<=1.01){scale=1;translateX=0;translateY=0;}
        applyTransform(false);
        return;
      }
      if(pointers.size===1&&scale>1.01&&dragStart){
        event.preventDefault();
        translateX=dragStart.translateX+(event.clientX-dragStart.x);
        translateY=dragStart.translateY+(event.clientY-dragStart.y);
        const maxX=stage.clientWidth*(scale-1)/2;
        const maxY=stage.clientHeight*(scale-1)/2;
        translateX=clamp(translateX,-maxX,maxX);
        translateY=clamp(translateY,-maxY,maxY);
        applyTransform(false);
      }
    });

    const finishPointer=event=>{
      const end={x:event.clientX,y:event.clientY,time:Date.now()};
      pointers.delete(event.pointerId);
      if(pointers.size<2)pinchStart=null;
      if(!pointers.size){
        if(scale<=1.01&&pointerStart){
          const dx=end.x-pointerStart.x;
          const dy=end.y-pointerStart.y;
          const elapsed=end.time-pointerStart.time;
          if(elapsed<500&&Math.abs(dx)>60&&Math.abs(dx)>Math.abs(dy)*1.25)go(dx<0?1:-1);
        }
        pointerStart=null;
        dragStart=null;
      }else if(pointers.size===1){
        const [remaining]=[...pointers.values()];
        dragStart={x:remaining.x,y:remaining.y,translateX,translateY};
      }
    };
    stage.addEventListener("pointerup",finishPointer);
    stage.addEventListener("pointercancel",finishPointer);

    document.addEventListener("keydown",event=>{
      if(!overlay||overlay.hidden)return;
      if(event.key==="Escape"){event.preventDefault();close();}
      else if(event.key==="ArrowLeft"){event.preventDefault();go(-1);}
      else if(event.key==="ArrowRight"){event.preventDefault();go(1);}
      else if(event.key==="+"||event.key==="="){event.preventDefault();setScale(scale+.5);}
      else if(event.key==="-"){event.preventDefault();setScale(scale-.5);}
      else if(event.key==="0"){event.preventDefault();resetTransform(true);}
    });
  };

  const bindTrack=track=>{
    if(bound.has(track))return;
    const images=[...track.querySelectorAll("img")];
    if(!images.length)return;
    bound.add(track);
    ensureLightbox();
    let lastScroll=0;
    track.addEventListener("scroll",()=>{lastScroll=Date.now();},{passive:true});
    images.forEach((image,index)=>{
      image.classList.add("detail-gallery-zoomable");
      image.setAttribute("role","button");
      image.setAttribute("tabindex","0");
      image.setAttribute("aria-label",`${image.alt||`Ảnh ${index+1}`} — mở toàn màn hình`);
      const open=()=>{
        if(Date.now()-lastScroll<160)return;
        overlay._lumiOpen(images,index,image);
      };
      image.addEventListener("click",open);
      image.addEventListener("keydown",event=>{
        if(event.key==="Enter"||event.key===" "){
          event.preventDefault();
          open();
        }
      });
    });
  };

  const scan=()=>document.querySelectorAll(TRACK_SELECTOR).forEach(bindTrack);
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",scan,{once:true});else scan();
  const observer=new MutationObserver(scan);
  observer.observe(document.documentElement,{subtree:true,childList:true});
})();