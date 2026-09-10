(()=>{
  "use strict";
  const PREFIX="lumi-saved-listing:";
  const root=document.querySelector("[data-saved-listings]");if(!root)return;
  const storage=(()=>{try{return window.localStorage}catch{return null}})();
  const el=(tag,className,text)=>{const node=document.createElement(tag);if(className)node.className=className;if(text!=null)node.textContent=text;return node;};
  const read=()=>{if(!storage)return[];const rows=[];for(let i=0;i<storage.length;i++){const key=storage.key(i);if(!key?.startsWith(PREFIX))continue;const raw=storage.getItem(key),slug=key.slice(PREFIX.length);if(!raw)continue;try{const parsed=JSON.parse(raw);if(parsed&&typeof parsed==="object")rows.push({...parsed,_key:key,_legacy:false});else rows.push({slug,_key:key,_legacy:true});}catch{rows.push({slug,_key:key,_legacy:true});}}return rows.sort((a,b)=>String(b.saved_at||"").localeCompare(String(a.saved_at||"")));};
  const button=(label,handler)=>{const node=el("button","mp-conversion-link",label);node.type="button";node.addEventListener("click",handler);return node;};
  const render=()=>{
    root.replaceChildren();const rows=read();
    document.querySelectorAll("[data-saved-total]").forEach(node=>node.textContent=String(rows.length));
    if(!rows.length){const empty=el("div","saved-listing-empty");empty.append(el("strong","","Chưa có tin nào được lưu"),el("p","","Khi xem một căn, bấm “Lưu tin” để giữ lại trên chính trình duyệt này."));const actions=el("div","saved-listing-actions");const sale=el("a","mp-conversion-link mp-conversion-link--primary","Xem căn đang bán");sale.href="/mua-ban-lumi-hanoi/";const rent=el("a","mp-conversion-link","Xem căn cho thuê");rent.href="/cho-thue-lumi-hanoi/";actions.append(sale,rent);empty.append(actions);root.append(empty);return;}
    const grid=el("div","saved-listings-grid");
    rows.forEach(item=>{const card=el("article","saved-listing-card");const title=el("h2","",item.title||"Tin đã lưu");card.append(title);const meta=el("div","saved-listing-meta");[item.type,item.tower?`Tòa ${item.tower}`:"",item.unit,item.price].filter(Boolean).forEach(value=>meta.append(el("span","",value)));if(meta.childNodes.length)card.append(meta);if(item._legacy){card.append(el("p","saved-legacy-note","Tin này được lưu từ phiên bản cũ. Mở lại trang chi tiết rồi bấm Lưu tin để đồng bộ đầy đủ thông tin."));}
      const actions=el("div","saved-listing-actions");if(item.url){const open=el("a","mp-conversion-link mp-conversion-link--primary","Mở tin");open.href=item.url;open.dataset.conversionAction="open_saved_listing";actions.append(open);}const remove=button("Bỏ lưu",()=>{try{storage?.removeItem(item._key);}catch{}window.dispatchEvent(new CustomEvent("lumi:saved-listings-changed"));render();});remove.dataset.conversionAction="remove_saved_listing";actions.append(remove);card.append(actions);grid.append(card);});root.append(grid);
  };
  window.addEventListener("storage",render);window.addEventListener("lumi:saved-listings-changed",render);render();
})();
