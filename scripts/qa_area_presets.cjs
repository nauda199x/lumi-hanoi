const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const path=require("node:path");

const src=fs.readFileSync(path.join(__dirname,"../assets/js/lumi-area-presets.js"),"utf8");
function fixture(){
  const types=[];
  const field={label:{textContent:""},help:{textContent:""},element:null};
  field.querySelector=selector=>selector==="label"?field.label:selector==="[data-area-help]"?field.help:null;
  const form={elements:{}};
  const makeElement=(tag)=>{
    const obj={tagName:tag.toUpperCase(),value:"",id:"",name:"",required:false,
      disabled:false,children:[],parentNode:field,attributes:{},listeners:{},
      setAttribute(name,value){this.attributes[name]=value;},
      addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);},
      append(...items){this.children.push(...items);}
    };
    return obj;
  };
  const area=makeElement("select");area.id="area";area.name="area_sqm";
  field.element=area;
  field.replaceChild=(next,old)=>{
    assert.equal(old,field.element);
    field.element=next;form.elements.area_sqm=next;
  };
  form.elements.area_sqm=area;
  const unit=makeElement("select");unit.value="";form.elements.unit_type=unit;
  const browser={document:{createElement:makeElement}};
  const context={window:browser,Option:class{constructor(text,value){this.textContent=text;this.value=value;}}};
  vm.runInNewContext(src,context);
  const controller=browser.LumiAreaPresets.mount(form);
  const change=(type)=>{
    unit.value=type;
    unit.listeners.change.forEach(fn=>fn({target:unit}));
  };
  return {api:browser.LumiAreaPresets,controller,form,field,change};
}

test("2PN chooser displays only groups from curated NFA layouts",()=>{
  const {form,field,change,controller}=fixture();
  assert.equal(form.elements.area_sqm.disabled,true);
  change("2PN");
  assert.deepEqual(Array.from(form.elements.area_sqm.children).slice(1).map(x=>x.value),["54","62","74","85","97"]);
  assert.match(field.label.textContent,/Nhóm diện tích thông thủy/);
  assert.match(field.help.textContent,/không dùng diện tích tim tường/);
  assert.equal(controller.valid(),false);
  form.elements.area_sqm.value="74";
  assert.equal(controller.valid(),true);
  change("3PN");
  assert.equal(controller.valid(),false); // selection must not survive unit change
  assert.deepEqual(Array.from(form.elements.area_sqm.children).slice(1).map(x=>x.value),["85","95","101","107","112","117","130","137"]);
});
test("old verified NFA maps to user-selected groups but arbitrary GFA does not",()=>{
  const {api,controller,change,form}=fixture();
  change("2PN");
  controller.sync("62.2");
  assert.equal(form.elements.area_sqm.value,"62");
  controller.sync("71.3");
  assert.equal(form.elements.area_sqm.value,"74");
  controller.sync("58.8"); // 2PN tim tường (GFA), must NOT silently assign group 54
  assert.equal(controller.valid(),false);
  assert.equal(api.normalized("3PN","118.3"),"117");
  assert.equal(api.normalized("1PN","53.9"),"54");
  assert.equal(api.normalized("2PN","96.7"),"97");
  assert.equal(api.normalized("2PN","130"),"");
});
test("shop is the only type allowed to enter a free-form area",()=>{
  const {change,form,controller}=fixture();
  change("Shop chân đế");
  assert.equal(form.elements.area_sqm.tagName,"INPUT");
  form.elements.area_sqm.value="74.5";
  assert.equal(controller.valid(),true);
  change("1PN");
  assert.equal(form.elements.area_sqm.tagName,"SELECT");
  assert.equal(controller.valid(),false);
});
test("sale, rent and both editing screens share presets instead of text inputs",()=>{
  const htmls=["dang-tin-lumi-hanoi/index.html","quan-ly-tin-lumi-hanoi/index.html","admin/index.html"];
  for(const filename of htmls){
    const html=fs.readFileSync(filename,"utf8");
    assert.match(html,/<select id="(?:area|manage-area|edit-area)" name="area_sqm" required>/);
    assert.match(html,/lumi-area-presets\.js/);
    assert.doesNotMatch(html,/<input[^>]+name="area_sqm"/);
  }
  for(const filename of ["assets/js/marketplace-form.js","assets/js/listing-manage.js","assets/js/marketplace-admin.js"]){
    const code=fs.readFileSync(filename,"utf8");
    assert.match(code,/LumiAreaPresets\?\.mount\?\./);
    assert.match(code,/areaBinding\?\.sync|areaBinding\.sync/);
    assert.match(code,/areaBinding\.valid/);
  }
});
