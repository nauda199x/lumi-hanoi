(()=>{
  const root=document.querySelector("[data-marketplace-admin]");
  if(!root||!window.LumiMarketplace)return;
  const api=window.LumiMarketplace;
  const loginPanel=root.querySelector("[data-admin-login]");
  const loginForm=root.querySelector("[data-admin-login-form]");
  const loginStatus=root.querySelector("[data-admin-login-status]");
  const dashboard=root.querySelector("[data-admin-dashboard]");
  const list=root.querySelector("[data-admin-list]");
  const filters=root.querySelector("[data-admin-filters]");
  const dialog=root.querySelector("[data-admin-dialog]");
  const editForm=dialog?.querySelector("[data-admin-edit-form]");
  const dashboardStatus=root.querySelector("[data-admin-status]");
  let rows=[];

  const statusLabels={pending:"Chờ duyệt",approved:"Đang hiển thị",rejected:"Từ chối",expired:"Hết hạn",sold:"Đã bán",rented:"Đã thuê"};
  const el=(tag,className,text)=>{const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node;};
  const showDashboardStatus=(message,error=false)=>{dashboardStatus.hidden=!message;dashboardStatus.textContent=message||"";dashboardStatus.className=`form-status${error?" is-error":""}`;};
  const coverFor=row=>[...(row.listing_images||[])].sort((a,b)=>Number(a.sort_order)-Number(b.sort_order))[0];
  const effectiveStatus=row=>row.status==="approved"&&row.expires_at&&new Date(row.expires_at)<=new Date()?"expired":row.status;
  const statusPill=row=>{const status=effectiveStatus(row);return el("span",`status-pill status-${status}`,statusLabels[status]||status);};
  const action=(label,className,onClick)=>{const button=el("button",`admin-action ${className||""}`,label);button.type="button";button.addEventListener("click",onClick);return button;};
  const expiresAt=()=>new Date(Date.now()+Number(api.config.listingLifetimeDays||45)*86400000).toISOString();
  const triggerSeoSync=async reason=>{
    try{
      const result=await api.requestSeoSync(reason);
      return result?.dispatched
        ?" SEO đang được đồng bộ ngay sang URL tĩnh và sitemap."
        :" SEO sẽ được đồng bộ tự động trong vài phút.";
    }catch{
      return " SEO sẽ được đồng bộ tự động trong vài phút.";
    }
  };
  const patchAndReload=async(id,patch,message)=>{
    showDashboardStatus("Đang cập nhật…");
    try{
      await api.updateListing(id,patch);
      const syncMessage=await triggerSeoSync("listing_updated");
      showDashboardStatus(`${message}${syncMessage}`);
      await load();
    }
    catch(error){showDashboardStatus(`Không cập nhật được: ${error.message}`,true);}
  };
  const deleteAndReload=async(row,button)=>{
    const code=row.listing_code||"này";
    const imageCount=row.listing_images?.length||0;
    const warning=`Xóa vĩnh viễn tin ${code}?${imageCount?` ${imageCount} ảnh đính kèm cũng sẽ bị xóa.`:""} Hành động này không thể hoàn tác.`;
    if(!confirm(warning))return;
    button.disabled=true;
    showDashboardStatus(`Đang xóa tin ${code}…`);
    try{
      const result=await api.deleteListing(row);
      rows=rows.filter(item=>item.id!==row.id);
      render();
      const syncMessage=await triggerSeoSync("listing_deleted");
      showDashboardStatus(`Đã xóa vĩnh viễn tin ${code}${result.deletedImageCount?` và ${result.deletedImageCount} ảnh`:""}.${syncMessage}`);
    }catch(error){
      button.disabled=false;
      showDashboardStatus(`Không xóa được tin: ${error.message}`,true);
    }
  };

  const itemFor=row=>{
    const currentStatus=effectiveStatus(row);
    const article=el("article","admin-item");
    const cover=coverFor(row);
    if(cover){const image=el("img","admin-thumb");image.src=api.imageUrl(cover.storage_path);image.alt="";article.append(image);}
    else article.append(el("div","admin-thumb listing-card-placeholder",row.tower||"LH"));
    const copy=el("div","admin-item-copy");
    const heading=el("h3","",row.title);const meta=el("div","admin-meta");
    meta.append(statusPill(row));
    [row.listing_code,row.listing_type==="rent"?"Cho thuê":"Mua bán",row.phase,row.tower,row.unit_type,api.formatCurrency(row.price_vnd,row.listing_type),`${row.poster_name} · ${row.contact_phone}`].filter(Boolean).forEach(value=>meta.append(el("span","",value)));
    if(row.is_featured)meta.append(el("span","listing-badge listing-badge--featured","Nổi bật"));
    if(row.listing_reports?.length)meta.append(el("span","",`${row.listing_reports.length} báo cáo`));
    copy.append(heading,meta);article.append(copy);
    const actions=el("div","admin-item-actions");
    actions.append(action("Xem / sửa","",()=>openEdit(row)));
    if(currentStatus!=="approved")actions.append(action(currentStatus==="expired"?"Gia hạn 45 ngày":"Duyệt","admin-action--approve",()=>patchAndReload(row.id,{status:"approved",approved_at:row.approved_at||new Date().toISOString(),expires_at:expiresAt()},currentStatus==="expired"?"Tin đã được gia hạn và hiển thị lại.":"Tin đã được duyệt và công khai.")));
    if(row.status!=="rejected")actions.append(action("Từ chối","admin-action--reject",()=>{if(confirm(`Từ chối tin ${row.listing_code}?`))patchAndReload(row.id,{status:"rejected"},"Tin đã bị từ chối.");}));
    if(currentStatus==="approved")actions.append(action(row.is_featured?"Bỏ ghim":"Ghim đầu", "admin-action--feature",()=>patchAndReload(row.id,{is_featured:!row.is_featured,sort_priority:row.is_featured?0:100},row.is_featured?"Đã bỏ ghim tin.":"Tin đã được ghim ưu tiên.")));
    if(currentStatus==="approved")actions.append(action(row.listing_type==="rent"?"Đã thuê":"Đã bán","",()=>patchAndReload(row.id,{status:row.listing_type==="rent"?"rented":"sold"},"Đã cập nhật trạng thái giao dịch.")));
    if(currentStatus==="approved"){const preview=el("a","admin-action","Mở tin");preview.href=`/tin-dang-lumi-hanoi/?slug=${encodeURIComponent(row.slug)}`;preview.target="_blank";preview.rel="noopener";actions.append(preview);}
    const deleteButton=action("Xóa vĩnh viễn","admin-action--delete",()=>deleteAndReload(row,deleteButton));
    deleteButton.setAttribute("aria-label",`Xóa vĩnh viễn tin ${row.listing_code||row.title}`);
    actions.append(deleteButton);
    article.append(actions);return article;
  };
  const filtered=()=>{
    const values=Object.fromEntries(new FormData(filters).entries());const keyword=String(values.keyword||"").toLocaleLowerCase("vi");
    return rows.filter(row=>(!values.status||effectiveStatus(row)===values.status)&&(!values.type||row.listing_type===values.type)&&(!keyword||[row.title,row.listing_code,row.tower,row.poster_name,row.contact_phone].some(value=>String(value||"").toLocaleLowerCase("vi").includes(keyword))));
  };
  const render=()=>{
    const items=filtered();list.replaceChildren(...items.map(itemFor));
    if(!items.length)list.append(el("div","marketplace-state", "Không có tin phù hợp với bộ lọc."));
    const counts={pending:0,approved:0,done:0,reports:0};
    rows.forEach(row=>{const status=effectiveStatus(row);if(status==="pending")counts.pending++;if(status==="approved")counts.approved++;if(["sold","rented","expired"].includes(status))counts.done++;counts.reports+=row.listing_reports?.length||0;});
    Object.entries(counts).forEach(([key,value])=>{const target=root.querySelector(`[data-kpi="${key}"]`);if(target)target.textContent=value;});
  };
  const openEdit=row=>{
    editForm.elements.id.value=row.id;editForm.elements.title.value=row.title||"";editForm.elements.price_vnd.value=row.price_vnd||"";editForm.elements.phase.value=row.phase||"";editForm.elements.tower.value=row.tower||"";editForm.elements.unit_type.value=row.unit_type||"";editForm.elements.area_sqm.value=row.area_sqm||"";editForm.elements.floor_label.value=row.floor_label||"";editForm.elements.poster_name.value=row.poster_name||"";editForm.elements.contact_phone.value=row.contact_phone||"";editForm.elements.description.value=row.description||"";
    dialog.querySelector("[data-dialog-code]").textContent=row.listing_code||"Tin đăng";
    const reports=dialog.querySelector("[data-dialog-reports]");reports.replaceChildren();
    (row.listing_reports||[]).forEach(report=>{const item=el("p","notice");item.textContent=`Báo cáo: ${report.reason}${report.details?` — ${report.details}`:""}`;reports.append(item);});
    dialog.showModal();
  };
  editForm?.addEventListener("submit",async event=>{
    event.preventDefault();const id=editForm.elements.id.value;
    const patch={title:api.cleanText(editForm.elements.title.value,180),price_vnd:Number(editForm.elements.price_vnd.value),phase:api.cleanText(editForm.elements.phase.value,30),tower:api.cleanText(editForm.elements.tower.value,10),unit_type:api.cleanText(editForm.elements.unit_type.value,30),area_sqm:Number(editForm.elements.area_sqm.value),floor_label:api.cleanText(editForm.elements.floor_label.value,30)||null,poster_name:api.cleanText(editForm.elements.poster_name.value,120),contact_phone:api.cleanText(editForm.elements.contact_phone.value,30),description:api.cleanText(editForm.elements.description.value,3000)};
    dialog.close();await patchAndReload(id,patch,"Đã lưu nội dung tin.");
  });
  dialog?.querySelectorAll("[data-dialog-close]").forEach(button=>button.addEventListener("click",()=>dialog.close()));
  dialog?.addEventListener("click",event=>{if(event.target===dialog)dialog.close();});
  filters?.addEventListener("input",render);

  const load=async()=>{rows=await api.listAdmin();render();};
  const enterDashboard=async()=>{
    loginPanel.hidden=true;dashboard.hidden=false;showDashboardStatus("Đang tải dữ liệu…");
    try{await load();showDashboardStatus("");}catch(error){showDashboardStatus(error.message,true);}
  };
  loginForm?.addEventListener("submit",async event=>{
    event.preventDefault();const button=loginForm.querySelector("button");button.disabled=true;loginStatus.hidden=false;loginStatus.textContent="Đang đăng nhập…";
    try{await api.signIn(loginForm.elements.email.value,loginForm.elements.password.value);loginForm.reset();await enterDashboard();}
    catch(error){loginStatus.textContent=error.status===400?"Email hoặc mật khẩu không đúng.":error.message;}
    finally{button.disabled=false;}
  });
  root.querySelector("[data-admin-logout]")?.addEventListener("click",async()=>{await api.signOut();dashboard.hidden=true;loginPanel.hidden=false;});
  const boot=async()=>{
    if(!api.configured()){loginStatus.hidden=false;loginStatus.textContent="Hệ thống dữ liệu chưa được kết nối.";return;}
    const session=await api.requireAdmin();if(session)enterDashboard();
  };
  boot();
})();
