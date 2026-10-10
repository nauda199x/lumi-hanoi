/* Canonical area groups for Lumi Hanoi apartment listings (marketplace UI).
 * Values represent SELECTABLE NFA-BASED MARKET GROUPS, not exact NFA of every
 * floorplan. Keep exact developer NFA/layout code separately when verified.
 * Groups are curated; never infer group via closest number or GFA conversion.
 */
(function(root){
  "use strict";
  const groups=Object.freeze({
    "1PN":[43,47,54],
    "2PN":[54,62,74,85,97],
    "3PN":[85,95,101,107,112,117,130,137],
    "4PN":[128,136],
    "Duplex":[115,134,143,194,200,212],
    "Penthouse":[346,368,377,402]
  });
  // Exact NFA values verified in developer brochures; for OLD draft/edit UX only.
  // Do not write converted data unless the poster/admin explicitly saves it.
  const aliases=Object.freeze({
    "1PN":{"43":[42,42.2],"47":[47.1],"54":[53.5,53.9,54.9]},
    "2PN":{"54":[53.4,53.8,54.5],"62":[62.1,62.2,63.7],
      "74":[71.3,71.4,73.6,73.9,74.2,74.3],
      "85":[81.3,81.7,82.1,84.5,85.7],"97":[96.7]},
    "3PN":{"85":[80.6,81,81.3,81.7,82.8,82.9,83,84,85.4,85.5,85.8,86],
      "95":[94.9,95.4,96.5,97.8],"101":[101.4],
      "107":[106.3,106.6,106.9,107.8,108],"112":[111.6],
      "117":[117.1,117.8,117.9,118.2,118.3],"130":[126,128.6],
      "137":[137.1]},
    "4PN":{"128":[127.5]},
    "Duplex":{"115":[115.4],"134":[134.2],"143":[142.9],
      "194":[193.2,194.4],"200":[199.9],"212":[211.7]},
    "Penthouse":{"346":[346.2],"368":[368.3],"377":[377],"402":[401.9]}
  });
  const shop="Shop chân đế";
  const numeric=x=>Number(String(x??"").trim());
  const optionsFor=unit=>groups[unit]||[];
  const normalized=(unit,raw)=>{
    const value=numeric(raw);
    if(!Number.isFinite(value)||value<=0)return "";
    const values=optionsFor(unit);
    const match=values.find(candidate=>candidate===value);
    if(match)return String(match);
    for(const [canonical,originals] of Object.entries(aliases[unit]||{})){
      if(originals.some(verified=>Math.abs(verified-value)<0.049))return canonical;
    }
    return "";
  };
  const valid=(unit,value)=>{
    if(unit===shop)return Number.isFinite(numeric(value))&&numeric(value)>=20&&numeric(value)<=1000;
    return optionsFor(unit).some(item=>String(item)===String(value));
  };
  const mount=form=>{
    if(!form?.elements?.unit_type||!form?.elements?.area_sqm)return null;
    const type=form.elements.unit_type;
    let area=form.elements.area_sqm;
    const originalId=area.id;
    const parent=area.parentNode;
    if(!parent||!root.document?.createElement)return null;
    const label=parent.querySelector("label");
    const help=parent.querySelector("[data-area-help]");
    let currentType="";
    const makeSelect=(unit)=>{
      const el=root.document.createElement("select");
      const values=optionsFor(unit);
      el.append(new Option(values.length?"Chọn diện tích thông thủy":"Chọn loại căn trước",""));
      for(const sqm of values)el.append(new Option(sqm+" m²",String(sqm)));
      el.disabled=!values.length;
      return el;
    };
    const makeInput=()=>{
      const el=root.document.createElement("input");
      el.type="number";el.min="20";el.max="1000";el.step="0.1";
      el.inputMode="decimal";el.placeholder="Diện tích thông thủy thực tế";
      return el;
    };
    const sync=(desired,force=false)=>{
      const unit=String(type.value||"");
      const changed=unit!==currentType||force;
      const keep=desired===undefined?(changed?"":area.value):desired;
      if(changed){
        const next=unit===shop?makeInput():makeSelect(unit);
        next.id=originalId;next.name="area_sqm";next.required=true;next.autocomplete="off";
        next.setAttribute("aria-label",unit===shop?"Diện tích thông thủy thực tế":"Chọn nhóm diện tích thông thủy");
        parent.replaceChild(next,area);
        area=next;
        currentType=unit;
      }
      area.value=unit===shop?(keep===undefined?"":String(keep)):normalized(unit,keep);
      if(label)label.textContent=unit===shop?"Diện tích thông thủy (m²) *":"Nhóm diện tích thông thủy (m²) *";
      if(help)help.textContent=unit===shop
        ?"Shop không có mẫu diện tích cố định; chỉ nhập diện tích thông thủy."
        :(optionsFor(unit).length
          ?"Chọn theo nhóm căn từ bản vẽ; không dùng diện tích tim tường. Nếu thiếu nhóm, liên hệ quản trị để bổ sung."
          :"Chọn loại căn trước để xem các diện tích.");
      return area;
    };
    type.addEventListener("change",()=>sync("",false));
    sync(area.value,true);
    return Object.freeze({
      sync,valid:()=>valid(type.value,area.value),
      value:()=>area.value,group:()=>normalized(type.value,area.value)
    });
  };
  root.LumiAreaPresets=Object.freeze({groups,optionsFor,normalized,valid,mount});
})(window);
