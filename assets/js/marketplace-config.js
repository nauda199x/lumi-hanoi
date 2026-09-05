/*
 * Public browser configuration for the Lumi Hanoi marketplace.
 * The Supabase publishable key is designed for public browser clients. Never
 * place a secret/service-role key, database password or private credential here.
 */
window.LUMI_MARKETPLACE_CONFIG = Object.freeze({
  supabaseUrl: "https://salsyqatlzapnzbcnnsr.supabase.co",
  supabasePublishableKey: "sb_publishable_OddNNu3rPBW93e51snyeeQ_4C0um6KU",
  storageBucket: "listing-images",
  maxImages: 12,
  maxImageBytes: 5 * 1024 * 1024,
  listingLifetimeDays: 45
});

/*
 * Keep the description required, but do not force sellers/landlords to write
 * filler text just to reach an arbitrary minimum length. The database applies
 * the same rule: at least one non-whitespace character, maximum 3000 chars.
 */
(function relaxMarketplaceDescriptionMinimum(){
  const apply=()=>{
    const description=document.querySelector('[data-marketplace-submit] textarea[name="description"]');
    if(description) description.minLength=1;
  };
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",apply,{once:true});
  else apply();
})();

/*
 * Marketplace filter guard.
 *
 * The listing page performs live Supabase requests whenever a filter changes.
 * Quick consecutive changes can make an older request finish after the newest
 * request and repaint the grid with stale rows. Re-checking the returned rows
 * against the current request also guarantees that a 4PN filter can never show
 * a 1PN row even if a stale/cached response reaches the browser.
 *
 * This is shared by both the sale and rental marketplace pages.
 */
(function hardenMarketplaceFilters(){
  const normalize=value=>String(value??"")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g,"")
    .replace(/đ/g,"d")
    .replace(/Đ/g,"D")
    .trim()
    .toLowerCase();

  const rowMatches=(row,filters={})=>{
    if(filters.phase&&normalize(row.phase)!==normalize(filters.phase))return false;
    if(filters.tower&&normalize(row.tower)!==normalize(filters.tower))return false;
    if(filters.bedroom&&normalize(row.unit_type)!==normalize(filters.bedroom))return false;

    const price=Number(row.price_vnd||0);
    const minPrice=Number(filters.minPrice||0);
    const maxPrice=Number(filters.maxPrice||0);
    if(minPrice&&price<minPrice)return false;
    if(maxPrice&&price>maxPrice)return false;

    if(filters.area){
      const [min,max]=String(filters.area).split("-").map(Number);
      const area=Number(row.area_sqm||0);
      if(area<Number(min||0)||(!Number.isNaN(max)&&max>0&&area>max))return false;
    }

    const keyword=normalize(filters.keyword);
    if(keyword){
      const haystack=[row.title,row.phase,row.tower,row.unit_type]
        .map(normalize)
        .join(" ");
      if(!haystack.includes(keyword))return false;
    }
    return true;
  };

  const install=()=>{
    const api=window.LumiMarketplace;
    if(api&&typeof api.listPublic==="function"&&!api.__filterGuardInstalled){
      const originalListPublic=api.listPublic.bind(api);
      const sequenceByType=new Map();
      const latestPromiseByType=new Map();

      api.listPublic=(type,filters={})=>{
        const key=String(type||"");
        const requestId=(sequenceByType.get(key)||0)+1;
        sequenceByType.set(key,requestId);
        const snapshot={...filters};

        const core=originalListPublic(type,snapshot).then(rows=>
          (Array.isArray(rows)?rows:[]).filter(row=>rowMatches(row,snapshot))
        );
        latestPromiseByType.set(key,core);

        return core.then(rows=>{
          if(requestId===sequenceByType.get(key))return rows;
          return latestPromiseByType.get(key)||rows;
        });
      };

      Object.defineProperty(api,"__filterGuardInstalled",{
        value:true,
        configurable:false,
        enumerable:false,
        writable:false
      });
    }

    if(!document.getElementById("marketplace-filter-hidden-fix")){
      const style=document.createElement("style");
      style.id="marketplace-filter-hidden-fix";
      style.textContent='[data-marketplace-list] [data-listing-grid][hidden]{display:none!important}';
      document.head.append(style);
    }

    document.querySelectorAll("[data-marketplace-list]").forEach(root=>{
      const grid=root.querySelector("[data-listing-grid]");
      const state=root.querySelector("[data-listing-state]");
      const stateTitle=root.querySelector("[data-state-title]");
      const count=root.querySelector("[data-listing-count]");
      if(!grid||!state)return;

      const syncEmptyCount=()=>{
        const title=String(stateTitle?.textContent||"");
        if(!state.hidden&&grid.hidden&&/Không tìm thấy|Chưa có tin đăng/.test(title)&&count){
          count.textContent="0 tin đăng";
        }
      };
      new MutationObserver(syncEmptyCount).observe(state,{attributes:true,attributeFilter:["hidden"]});
      syncEmptyCount();

      const quick=root.querySelector(".marketplace-quick-filters");
      const bedroom=root.querySelector('[data-listing-filters] [name="bedroom"]');
      if(quick&&bedroom&&!quick.querySelector('[data-value="4PN"]')){
        const button=document.createElement("button");
        button.type="button";
        button.className="marketplace-quick-filter";
        button.dataset.value="4PN";
        button.textContent="4PN";
        button.addEventListener("click",()=>{
          bedroom.value="4PN";
          bedroom.dispatchEvent(new Event("change",{bubbles:true}));
        });
        const shop=quick.querySelector('[data-value="Shop chân đế"]');
        quick.insertBefore(button,shop||null);
      }
    });
  };

  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
  else install();
})();
