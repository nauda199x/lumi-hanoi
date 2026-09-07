(()=>{
  const root=document.querySelector('[data-marketplace-admin]');
  if(!root||!window.LumiMarketplace)return;
  const api=window.LumiMarketplace;
  const $=selector=>root.querySelector(selector);
  const loginPanel=$('[data-admin-login]'),loginForm=$('[data-admin-login-form]'),loginStatus=$('[data-admin-login-status]');
  const dashboard=$('[data-admin-dashboard]'),filters=$('[data-admin-filters]'),list=$('[data-admin-list]');
  const dialog=$('[data-admin-dialog]'),editForm=$('[data-admin-edit-form]'),confirmDialog=$('[data-admin-confirm]');
  const tableWrap=$('[data-admin-table-wrap]'),empty=$('[data-admin-empty]'),pagination=$('[data-admin-pagination]');
  const selectPage=$('[data-admin-select-page]'),bulk=$('[data-admin-bulk]');
  const preferenceKey='lumi_admin_view_v2';
  const phases={Signature:['S1','S2','S3','S5','S6'],Prestige:['P1','P2'],Elite:['E1','E2']};
  const statuses={pending:'Chờ duyệt',approved:'Đang hiển thị',rejected:'Từ chối',expired:'Đã ẩn / hết hạn',sold:'Đã bán',rented:'Đã cho thuê'};
  const reportLabels={already_done:'Căn đã giao dịch',wrong_info:'Thông tin chưa đúng',cannot_contact:'Không liên hệ được',other:'Phản ánh khác'};
  let rows=[],page=1,pageSize=20,total=0,selected=new Set(),operationErrors=new Map(),loading=false,busy=false,loggedIn=false;
  let requestId=0,controller=null,statsController=null,statsId=0,searchTimer=null,editing=null,editRequestId=0,saving=false,refreshTimer=null,confirmPending=false;
  const el=(tag,className,text)=>{const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;};
  const button=(text,onClick,className='btn')=>{const node=el('button',className,text);node.type='button';node.addEventListener('click',onClick);return node;};
  const show=(node,message,error=false)=>{node.hidden=!message;node.textContent=message||'';node.className=`form-status${error?' is-error':''}`;};
  const status=(message,error=false)=>show($('[data-admin-status]'),message,error);
  const date=(value,withYear=false)=>{if(!value||!Number.isFinite(new Date(value).getTime()))return 'Chưa có';return new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit',...(withYear?{year:'numeric'}:{}),timeZone:'Asia/Ho_Chi_Minh'}).format(new Date(value));};
  const currentStatus=row=>row.status==='approved'&&row.expires_at&&new Date(row.expires_at)<=new Date()?'expired':row.status;
  const pill=(label,key)=>el('span',`status-pill status-${key}`,label);
  const getFilters=()=>Object.fromEntries(new FormData(filters).entries());
  const saveView=()=>{try{sessionStorage.setItem(preferenceKey,JSON.stringify({filters:getFilters(),page,pageSize}));}catch{}};
  const updateTowers=(form,keep='',allowAll=false)=>{
    const phase=form.elements.phase.value;
    const options=phases[phase]||Object.values(phases).flat();
    form.elements.tower.replaceChildren();
    if(allowAll){const option=el('option','','Tất cả tòa');option.value='';form.elements.tower.append(option);}
    options.forEach(value=>form.elements.tower.append(el('option','',value)));
    if(options.includes(keep))form.elements.tower.value=keep;
  };
  const restoreView=()=>{try{
    const saved=JSON.parse(sessionStorage.getItem(preferenceKey)||'null');if(!saved)return;
    Object.entries(saved.filters||{}).forEach(([key,value])=>{if(filters.elements[key]&&typeof value==='string')filters.elements[key].value=value;});
    updateTowers(filters,saved.filters?.tower,true);
    page=Math.max(1,Math.min(100000,Math.floor(Number(saved.page)||1)));
    pageSize=[20,50,100].includes(Number(saved.pageSize))?Number(saved.pageSize):20;
    $('[data-admin-page-size]').value=String(pageSize);
  }catch{}};
  const updateSelection=()=>{
    const count=selected.size;
    bulk.hidden=!count;$('[data-admin-selected]').textContent=`Đã chọn ${count} tin`;
    selectPage.checked=!!rows.length&&count===rows.length;
    selectPage.indeterminate=count>0&&count<rows.length;
    selectPage.disabled=loading||busy||!rows.length;
    list.querySelectorAll('[data-row-id]').forEach(tr=>{
      const checked=selected.has(tr.dataset.rowId);tr.classList.toggle('is-selected',checked);
      const input=tr.querySelector('input[type=checkbox]');if(input)input.checked=checked;
    });
    bulk.querySelectorAll('button').forEach(node=>node.disabled=busy||loading);
  };
  const clearSelection=()=>{selected.clear();updateSelection();};
  const lockRows=()=>{
    tableWrap.setAttribute('aria-busy',String(loading||busy));
    list.querySelectorAll('button,input').forEach(node=>node.disabled=loading||busy);
    pagination.querySelectorAll('button').forEach(node=>node.disabled=loading||busy||node.dataset.unavailable==='true');
    updateSelection();
  };
  const setBusy=value=>{
    busy=value;
    dashboard.querySelectorAll('button,input,select').forEach(node=>node.disabled=value);
    lockRows();
  };
  const ask=({title,message,codes=[],danger=false,submit='Xác nhận'})=>{
    if(confirmPending)return Promise.resolve(false);confirmPending=true;
    $('[data-confirm-title]').textContent=title;$('[data-confirm-message]').textContent=message;
    $('[data-confirm-codes]').textContent=codes.slice(0,8).join(' · ')+(codes.length>8?` · và ${codes.length-8} tin khác`:'');
    const submitButton=$('[data-confirm-submit]');submitButton.textContent=submit;submitButton.className=`btn ${danger?'btn-danger':'btn-primary'}`;
    confirmDialog.returnValue='';confirmDialog.showModal();
    return new Promise(resolve=>confirmDialog.addEventListener('close',()=>{confirmPending=false;resolve(confirmDialog.returnValue==='confirm');},{once:true}));
  };
  const syncSeo=async reason=>{
    try{await api.requestSeoSync(reason);}catch{if(loggedIn)status(`${$('[data-admin-status]').textContent} Chưa gửi được yêu cầu cập nhật trang công khai; hệ thống sẽ thử qua lịch đồng bộ tự động.`,true);}
  };
  const refreshStats=async()=>{
    const id=++statsId;statsController?.abort();statsController=new AbortController();
    try{
      const counts=await api.adminCounts({signal:statsController.signal});
      if(id!==statsId||!loggedIn)return;
      Object.entries(counts).forEach(([key,value])=>{const node=$(`[data-kpi="${key}"]`);if(node)node.textContent=new Intl.NumberFormat('vi-VN').format(value);});
      $('[data-admin-updated]').textContent=`Cập nhật ${new Intl.DateTimeFormat('vi-VN',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Ho_Chi_Minh'}).format(new Date())} · Tổng quan toàn bộ tin đăng`;
    }catch(error){if(error.name!=='AbortError'&&id===statsId&&loggedIn){root.querySelectorAll('[data-kpi]').forEach(node=>node.textContent='—');$('[data-admin-updated]').textContent='Chưa tải được số liệu tổng quan. Bấm Làm mới để thử lại.';}}
  };
  const showEmpty=(title,description,retry=false)=>{
    empty.replaceChildren(el('strong','',title),el('p','',description));
    empty.append(button(retry?'Thử lại':'Xóa bộ lọc',()=>retry?load(true):resetFilters(),'btn'));
    empty.hidden=false;
  };
  const renderPagination=()=>{
    pagination.replaceChildren();const pages=Math.max(1,Math.ceil(total/pageSize));
    pagination.append(el('span','muted',`Trang ${page} / ${pages}`));
    const controls=el('div','admin-page-buttons');
    const goButton=(label,target,unavailable=false)=>{
      const node=button(label,()=>{if(loading||busy)return;page=target;clearSelection();load();},'btn btn-small');
      node.dataset.unavailable=String(unavailable);node.disabled=unavailable;
      if(target===page&&!unavailable){node.setAttribute('aria-current','page');node.setAttribute('aria-label',`Trang ${target}, trang hiện tại`);}
      return node;
    };
    controls.append(goButton('Trước',page-1,page<=1));
    const choices=[...new Set([1,page-1,page,page+1,pages])].filter(number=>number>=1&&number<=pages).sort((a,b)=>a-b);
    let previous=0;choices.forEach(number=>{if(previous&&number-previous>1)controls.append(el('span','muted','…'));controls.append(goButton(String(number),number));previous=number;});
    controls.append(goButton('Sau',page+1,page>=pages));pagination.append(controls);
  };
  const perform=async(items,action)=>{
    if(busy||loading||!items.length)return;
    const count=items.length;
    const labels={approve:['Duyệt / gia hạn tin',`Công khai ${count} tin và đặt thời hạn mới ${Number(api.config.listingLifetimeDays||45)} ngày kể từ hôm nay.`, 'Duyệt / gia hạn'],hide:['Ẩn tin đăng',`Ẩn ${count} tin khỏi danh sách công khai. Có thể duyệt lại khi cần.`, 'Ẩn tin'],reject:['Từ chối tin đăng',`Chuyển ${count} tin sang trạng thái từ chối.`, 'Từ chối'],done:['Đánh dấu đã giao dịch',`${count} tin sẽ được chuyển sang Đã bán hoặc Đã cho thuê theo loại giao dịch và ngừng hiển thị.`, 'Đã giao dịch'],feature:['Ghim tin',`Ưu tiên ${count} tin đang hiển thị.`, 'Ghim tin'],unfeature:['Bỏ ghim tin',`Bỏ ưu tiên ${count} tin đã chọn.`, 'Bỏ ghim']};
    const [title,message,submit]=labels[action];
    if(!await ask({title,message,submit,codes:items.map(row=>row.listing_code)}))return;
    if(busy||loading||!loggedIn)return;
    setBusy(true);status(`Đang xử lý 0/${count} tin…`);
    let changed=false;
    try{
      const result=await api.applyAdminAction(items,action,{onProgress:progress=>status(`Đang xử lý ${progress.done}/${progress.total} tin…`)});
      changed=result.success.length>0;operationErrors=new Map(result.failed.map(item=>[item.id,item.message]));clearSelection();
      await load(true);
      if(result.failed.length){
        const details=result.failed.slice(0,4).map(item=>`${item.code||'Tin đăng'}: ${item.message}`).join(' ');
        status(`Đã xử lý ${result.success.length}/${count} tin. ${result.failed.length} tin chưa thay đổi. ${details}${result.failed.length>4?' Kiểm tra lại các tin còn lại trước khi thử tiếp.':''}`,true);
      }else status(`Đã xử lý ${count} tin thành công.`);
    }catch(error){status(error.message,true);}finally{setBusy(false);if(changed)void syncSeo('admin_bulk_'+action);}
  };
  const deleteAndReload=async row=>{
    if(busy||loading)return;
    setBusy(true);status('Đang kiểm tra tin cần xóa…');
    let changed=false;
    try{
      const full=await api.getAdminListing(row.id);
      if(full.updated_at!==row.updated_at){status('Tin vừa thay đổi. Danh sách đã được tải lại; hãy kiểm tra trước khi xóa.',true);await load(true);return;}
      status('');
      if(!await ask({title:'Xóa vĩnh viễn tin đăng?',message:`Tin ${full.listing_code} và ${full.listing_images?.length||0} ảnh đính kèm sẽ bị xóa. Không thể hoàn tác.`,codes:[full.title],danger:true,submit:'Xóa vĩnh viễn'}))return;
      status('Đang xóa tin…');await api.deleteListing(full);changed=true;clearSelection();await load(true);status(`Đã xóa tin ${full.listing_code}.`);
    }catch(error){status(`Không xóa được tin: ${error.message}`,true);}finally{setBusy(false);if(changed)void syncSeo('listing_deleted');}
  };
  const itemFor=row=>{
    const tr=el('tr');tr.dataset.rowId=row.id;
    const checkCell=el('td','select-cell'),check=el('input');check.type='checkbox';check.setAttribute('aria-label',`Chọn tin ${row.listing_code}`);
    check.addEventListener('change',()=>{if(loading||busy)return;check.checked?selected.add(row.id):selected.delete(row.id);updateSelection();});checkCell.append(check);
    const propertyCell=el('td'),property=el('div','admin-property');
    const cover=row.listing_images?.[0];
    if(cover){const img=el('img','admin-thumb');img.src=api.imageUrl(cover.storage_path);img.alt='';img.width=66;img.height=58;img.loading='lazy';img.decoding='async';img.addEventListener('error',()=>{img.replaceWith(el('span','admin-thumb admin-thumb-placeholder',row.tower));},{once:true});property.append(img);}
    else property.append(el('span','admin-thumb admin-thumb-placeholder',row.tower));
    const copy=el('div');copy.append(button(row.title,()=>openEdit(row),'admin-title'),el('div','admin-meta',`${row.listing_type==='rent'?'Cho thuê':'Mua bán'} · ${row.phase} · ${row.tower} · ${row.unit_type}`),el('div','admin-code',row.listing_code));property.append(copy);propertyCell.append(property);
    const priceCell=el('td');priceCell.append(el('strong','admin-price',api.formatCurrency(row.price_vnd,row.listing_type)),el('span','admin-meta',`${Number(row.area_sqm).toLocaleString('vi-VN')} m²`));
    const contactCell=el('td');contactCell.append(el('span','admin-person',row.poster_name));
    const phone=el('a','admin-phone',row.contact_phone);phone.href=`tel:${String(row.contact_phone||'').replace(/[^+0-9]/g,'')}`;contactCell.append(phone);
    const state=currentStatus(row),stateCell=el('td'),stack=el('div','admin-status-stack');stack.append(pill(statuses[state]||state,state));
    if(row.is_featured)stack.append(pill('Đang ghim','featured'));
    if(row.open_reports?.length)stack.append(pill('Có báo cáo','reported'));
    if(operationErrors.has(row.id))stack.append(el('span','admin-operation-error',`Chưa xử lý: ${operationErrors.get(row.id)}`));
    if(state==='approved'&&row.expires_at&&new Date(row.expires_at)-Date.now()<=7*86400000)stack.append(pill('Sắp hết hạn','expiring'));
    stateCell.append(stack);
    const timeCell=el('td'),time=el('div','admin-date',date(row.created_at,true));time.title='Ngày đăng';time.append(el('span','',`Hạn: ${row.expires_at?date(row.expires_at,true):'Chưa đặt'}`));timeCell.append(time);
    const actionCell=el('td'),actions=el('div','admin-row-actions');actions.append(button('Xem / sửa',()=>openEdit(row),'btn btn-small'));
    if(state==='pending')actions.append(button('Duyệt',()=>perform([row],'approve'),'btn btn-small btn-primary'));
    const menu=el('details','admin-menu'),summary=el('summary','','⋯');summary.setAttribute('aria-label',`Thao tác tin ${row.listing_code}`);
    summary.addEventListener('click',event=>{if(busy||loading){event.preventDefault();return;}root.querySelectorAll('.admin-menu[open]').forEach(other=>{if(other!==menu)other.open=false;});});
    const panel=el('div','admin-menu-panel');
    const menuAction=(text,action,danger=false)=>{const node=button(text,()=>{menu.open=false;perform([row],action);},danger?'danger-text':'');panel.append(node);};
    if(state==='approved'){const link=el('a','','Mở tin công khai ↗');link.href=api.listingUrl(row);link.target='_blank';link.rel='noopener';panel.append(link);menuAction('Gia hạn tin','approve');menuAction(row.is_featured?'Bỏ ghim':'Ghim tin',row.is_featured?'unfeature':'feature');menuAction(row.listing_type==='rent'?'Đã cho thuê':'Đã bán','done');menuAction('Ẩn tin','hide');}
    else if(state!=='pending')menuAction('Duyệt / hiển thị lại','approve');
    if(state==='pending')menuAction('Từ chối','reject');
    panel.append(button('Xóa vĩnh viễn',()=>{menu.open=false;deleteAndReload(row);},'danger-text'));
    menu.append(summary,panel);actions.append(menu);actionCell.append(actions);tr.append(checkCell,propertyCell,priceCell,contactCell,stateCell,timeCell,actionCell);return tr;
  };
  const render=()=>{
    list.replaceChildren(...rows.map(itemFor));tableWrap.hidden=!rows.length;empty.hidden=!!rows.length;
    if(!rows.length)showEmpty('Không có tin phù hợp','Thử thay đổi trạng thái hoặc xóa bộ lọc để xem các tin khác.');
    const first=total?(page-1)*pageSize+1:0,last=Math.min(page*pageSize,total);
    $('[data-admin-result-count]').textContent=total?`${first}–${last} / ${total.toLocaleString('vi-VN')} tin đăng`:'0 tin đăng';
    const values=getFilters();const active=Object.entries(values).filter(([key,value])=>value&&key!=='sort');
    $('[data-admin-filter-summary]').textContent=active.length?`Đang áp dụng ${active.length} điều kiện lọc`:'Toàn bộ tin mua bán và cho thuê';
    root.querySelectorAll('[data-queue]').forEach(node=>node.setAttribute('aria-pressed',String(node.dataset.queue===values.status)));
    renderPagination();lockRows();saveView();
  };
  const load=async(withStats=false)=>{
    if(!loggedIn)return false;
    clearTimeout(searchTimer);const id=++requestId;controller?.abort();controller=new AbortController();loading=true;lockRows();
    $('[data-admin-result-count]').textContent='Đang tải tin…';
    if(withStats)void refreshStats();
    try{
      let result=await api.listAdminPage(getFilters(),page,{pageSize,signal:controller.signal});
      if(id!==requestId||!loggedIn)return false;
      const max=Math.max(1,Math.ceil(result.total/pageSize));
      if(page>max){page=max;result=await api.listAdminPage(getFilters(),page,{pageSize,signal:controller.signal});}
      if(id!==requestId||!loggedIn)return false;
      rows=Array.isArray(result.rows)?result.rows:[];total=result.total;selected=new Set([...selected].filter(value=>rows.some(row=>row.id===value)));
      loading=false;render();return true;
    }catch(error){
      if(id!==requestId||error.name==='AbortError'||!loggedIn)return false;
      loading=false;rows=[];selected.clear();list.replaceChildren();tableWrap.hidden=true;pagination.replaceChildren();
      $('[data-admin-result-count]').textContent='Chưa tải được danh sách';
      showEmpty('Không tải được tin đăng',error.message,true);lockRows();
      if(error.status===401)status('Phiên quản trị hết hạn. Vui lòng đăng xuất và đăng nhập lại.',true);
      return false;
    }
  };
  const changeFilters=(delay=0)=>{
    if(busy)return;clearTimeout(searchTimer);controller?.abort();requestId++;page=1;clearSelection();loading=true;lockRows();
    searchTimer=setTimeout(()=>load(),delay);
  };
  const resetFilters=()=>{if(busy)return;filters.reset();updateTowers(filters,'',true);changeFilters();};
  const renderReports=row=>{
    const node=$('[data-dialog-reports]');node.replaceChildren();const reports=row.listing_reports||[];node.hidden=!reports.length;if(!reports.length)return;
    const open=reports.filter(report=>!report.resolved_at);node.append(el('h3','',`${open.length} báo cáo chưa xử lý`));
    reports.forEach(report=>{const item=el('div','admin-report');item.append(el('strong','',reportLabels[report.reason]||'Phản ánh khác'));if(report.details)item.append(el('p','',report.details));item.append(el('small','',`${date(report.created_at,true)} · ${report.resolved_at?'Đã xử lý':'Chưa xử lý'}`));node.append(item);});
    if(open.length)node.append(button('Đánh dấu đã xử lý',async()=>{
      if(saving)return;
      if(!await ask({title:'Đã xử lý các phản ánh?',message:`Đánh dấu ${open.length} báo cáo đang xem là đã xử lý. Trạng thái tin đăng được giữ nguyên.`,submit:'Đã xử lý'}))return;
      saving=true;setEditBusy(true);
      try{const count=await api.resolveAdminReports(row.id,open.map(report=>report.id));open.forEach(report=>report.resolved_at=new Date().toISOString());renderReports(row);show($('[data-dialog-status]'),`Đã xử lý ${count} báo cáo.`);void refreshStats();void load();}
      catch(error){show($('[data-dialog-status]'),error.message,true);}finally{saving=false;setEditBusy(false);}
    },'btn btn-small'));
  };
  const setEditBusy=value=>dialog.querySelectorAll('input,select,textarea,button').forEach(node=>node.disabled=value);
  const openEdit=async row=>{
    if(busy||loading)return;const id=++editRequestId;editing=null;editForm.reset();$('[data-dialog-content]').hidden=true;
    $('[data-dialog-code]').textContent=row.listing_code;show($('[data-dialog-status]'),'Đang tải đầy đủ nội dung tin…');dialog.showModal();
    try{
      const full=await api.getAdminListing(row.id);if(id!==editRequestId||!dialog.open||!loggedIn)return;
      editing=full;
      ['id','title','phase','unit_type','area_sqm','floor_label','furnishing','poster_name','contact_phone','description'].forEach(key=>editForm.elements[key].value=full[key]||'');
      updateTowers(editForm,full.tower);editForm.elements.price.value=String(Number(full.price_vnd)/(full.listing_type==='rent'?1e6:1e9));
      editForm.elements.price.min=full.listing_type==='rent'?'1':'0.001';editForm.elements.price.step=full.listing_type==='rent'?'0.001':'0.000001';
      $('[data-price-label]').textContent=full.listing_type==='rent'?'Giá thuê (triệu / tháng)':'Giá bán (tỷ đồng)';updatePricePreview();
      const meta=$('[data-dialog-meta]');meta.replaceChildren(pill(statuses[currentStatus(full)],currentStatus(full)),el('span','',`Đăng ${date(full.created_at,true)}`),el('span','',`Cập nhật ${date(full.updated_at,true)}`));
      const images=$('[data-dialog-images]');images.replaceChildren();
      (full.listing_images||[]).forEach((image,index)=>{const link=el('a');link.href=api.imageUrl(image.storage_path);link.target='_blank';link.rel='noopener';link.setAttribute('aria-label',`Mở ảnh gốc ${index+1}`);const img=el('img');img.src=link.href;img.alt=image.alt_text||`Ảnh tin đăng ${index+1}`;img.loading='lazy';img.width=145;img.height=108;link.append(img);images.append(link);});
      if(!full.listing_images?.length)images.append(el('span','muted','Tin chưa có ảnh đính kèm.'));
      renderReports(full);$('[data-dialog-content]').hidden=false;show($('[data-dialog-status]'),'');
    }catch(error){if(id===editRequestId&&dialog.open)show($('[data-dialog-status]'),error.message,true);}
  };
  const updatePricePreview=()=>{if(editing)$('[data-price-preview]').textContent=api.formatCurrency(Math.round(Number(editForm.elements.price.value)*(editing.listing_type==='rent'?1e6:1e9)),editing.listing_type);};
  editForm.addEventListener('submit',async event=>{
    event.preventDefault();if(saving||!editing)return;
    const fields=editForm.elements;
    const patch={title:api.cleanText(fields.title.value,180),price_vnd:Math.round(Number(fields.price.value)*(editing.listing_type==='rent'?1e6:1e9)),phase:fields.phase.value,tower:fields.tower.value,unit_type:fields.unit_type.value,bedroom_count:/^[1-4]PN$/.test(fields.unit_type.value)?Number(fields.unit_type.value[0]):null,area_sqm:Number(fields.area_sqm.value),floor_label:fields.floor_label.value||null,furnishing:api.cleanText(fields.furnishing.value,80)||null,poster_name:api.cleanText(fields.poster_name.value,120),contact_phone:api.cleanText(fields.contact_phone.value,30),description:api.cleanText(fields.description.value,3000)};
    if(!patch.description||patch.title.length<10||patch.poster_name.length<2||patch.contact_phone.length<8||!Number.isSafeInteger(patch.price_vnd)||patch.price_vnd<1e6||!phases[patch.phase]?.includes(patch.tower)){show($('[data-dialog-status]'),'Kiểm tra lại tiêu đề, giá, tòa, người đăng, điện thoại và mô tả.',true);return;}
    saving=true;setEditBusy(true);show($('[data-dialog-status]'),'Đang lưu chỉnh sửa…');let saved=false;
    try{await api.updateListing(editing.id,patch,editing.updated_at);saved=true;saving=false;dialog.close();await load(true);status('Đã lưu nội dung tin đăng.');}
    catch(error){show($('[data-dialog-status]'),`${error.message} Nội dung đang nhập vẫn được giữ trong cửa sổ này.`,true);}
    finally{saving=false;setEditBusy(false);if(saved)void syncSeo('listing_updated');}
  });
  editForm.elements.phase.addEventListener('change',()=>updateTowers(editForm));
  editForm.elements.price.addEventListener('input',updatePricePreview);
  dialog.querySelectorAll('[data-dialog-close]').forEach(node=>node.addEventListener('click',()=>{if(!saving)dialog.close();}));
  dialog.addEventListener('cancel',event=>{if(saving)event.preventDefault();});
  dialog.addEventListener('close',()=>{editRequestId++;editing=null;});
  filters.addEventListener('submit',event=>{event.preventDefault();changeFilters();});
  filters.elements.keyword.addEventListener('input',()=>changeFilters(350));
  filters.addEventListener('change',event=>{if(event.target.name==='phase')updateTowers(filters,'',true);if(event.target.name!=='keyword')changeFilters();});
  root.querySelectorAll('[data-queue]').forEach(node=>node.addEventListener('click',()=>{if(busy)return;filters.elements.status.value=node.dataset.queue;changeFilters();}));
  $('[data-admin-page-size]').addEventListener('change',event=>{pageSize=Number(event.target.value);changeFilters();});
  $('[data-admin-reset]').addEventListener('click',resetFilters);
  $('[data-admin-refresh]').addEventListener('click',()=>{if(busy)return;clearSelection();operationErrors.clear();status('');load(true);});
  $('[data-admin-clear-selection]').addEventListener('click',clearSelection);
  selectPage.addEventListener('change',()=>{if(loading||busy)return;selected=selectPage.checked?new Set(rows.map(row=>row.id)):new Set();updateSelection();});
  root.querySelectorAll('[data-bulk-action]').forEach(node=>node.addEventListener('click',()=>perform(rows.filter(row=>selected.has(row.id)),node.dataset.bulkAction)));
  document.addEventListener('click',event=>{if(!event.target.closest('.admin-menu'))root.querySelectorAll('.admin-menu[open]').forEach(menu=>menu.open=false);});
  document.addEventListener('keydown',event=>{if(event.key==='Escape')root.querySelectorAll('.admin-menu[open]').forEach(menu=>menu.open=false);});
  const enterDashboard=async()=>{
    loggedIn=true;loginPanel.hidden=true;dashboard.hidden=false;status('');await load(true);
    clearInterval(refreshTimer);refreshTimer=setInterval(()=>{if(loggedIn&&!document.hidden&&!busy&&!loading&&!dialog.open&&!confirmDialog.open)void refreshStats();},120000);
  };
  loginForm.addEventListener('submit',async event=>{
    event.preventDefault();const submit=loginForm.querySelector('button');submit.disabled=true;show(loginStatus,'Đang đăng nhập…');
    try{await api.signIn(loginForm.elements.email.value,loginForm.elements.password.value);loginForm.reset();show(loginStatus,'');await enterDashboard();}
    catch(error){show(loginStatus,error.status===400?'Email hoặc mật khẩu không đúng.':error.message,true);}finally{submit.disabled=false;}
  });
  $('[data-admin-logout]').addEventListener('click',async()=>{
    if(busy||saving)return;loggedIn=false;requestId++;statsId++;editRequestId++;controller?.abort();statsController?.abort();clearInterval(refreshTimer);clearTimeout(searchTimer);
    dialog.close();confirmDialog.close();rows=[];selected.clear();list.replaceChildren();$('[data-dialog-content]').hidden=true;editForm.reset();$('[data-dialog-images]').replaceChildren();$('[data-dialog-reports]').replaceChildren();dashboard.hidden=true;loginPanel.hidden=false;show(loginStatus,'');
    try{sessionStorage.removeItem(preferenceKey);}catch{}filters.reset();page=1;pageSize=20;$('[data-admin-page-size]').value='20';await api.signOut();loginForm.elements.email.focus();
  });
  const boot=async()=>{
    if(!api.configured()){show(loginStatus,'Hệ thống dữ liệu chưa được kết nối.',true);return;}
    restoreView();
    try{if(await api.requireAdmin())await enterDashboard();}catch{show(loginStatus,'Chưa kiểm tra được phiên đăng nhập. Vui lòng thử đăng nhập lại.',true);}
  };
  void boot();
})();
