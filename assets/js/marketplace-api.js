(()=>{
  const config=window.LUMI_MARKETPLACE_CONFIG||{};
  const base=String(config.supabaseUrl||"").replace(/\/$/,"");
  const publishableKey=String(config.supabasePublishableKey||config.supabaseAnonKey||"");
  const sessionKey="lumi_marketplace_admin_session";

  class MarketplaceError extends Error{
    constructor(message,status=0,details=null){super(message);this.name="MarketplaceError";this.status=status;this.details=details;}
  }

  const configured=()=>Boolean(base&&publishableKey&&!base.includes("YOUR_PROJECT"));
  const apiHeaders=token=>({apikey:publishableKey,...(token?{Authorization:`Bearer ${token}`}:{})});
  const parseResponse=async response=>{
    if(response.status===204)return null;
    const text=await response.text();
    if(!text)return null;
    try{return JSON.parse(text);}catch{return text;}
  };
  const request=async(path,{method="GET",body,token,headers={},signal,withCount=false}={})=>{
    if(!configured())throw new MarketplaceError("Hệ thống dữ liệu chưa được kết nối.");
    const payloadIsBinary=body instanceof Blob||body instanceof ArrayBuffer;
    const response=await fetch(`${base}${path}`,{
      method,signal,
      headers:{...apiHeaders(token),...(body!==undefined&&!payloadIsBinary?{"Content-Type":"application/json"}:{}),...headers},
      body:body===undefined?undefined:(payloadIsBinary?body:JSON.stringify(body))
    });
    const data=await parseResponse(response);
    // A saved page can disappear when listings expire. Preserve the total so
    // the caller can return to the last available page instead of showing error.
    if(withCount&&response.status===416){
      const total=response.headers.get("Content-Range")?.split("/")[1];
      if(/^\d+$/.test(total||""))return {rows:[],total:Number(total)};
    }
    if(!response.ok){
      const message=data?.message||data?.msg||data?.error_description||data?.error||`Yêu cầu không thành công (${response.status}).`;
      throw new MarketplaceError(message,response.status,data);
    }
    if(withCount){
      const total=response.headers.get("Content-Range")?.split("/")[1];
      if(!/^\d+$/.test(total||""))throw new MarketplaceError("Không đọc được tổng số căn.");
      return {rows:data,total:Number(total)};
    }
    return data;
  };
  const restPath=(table,params={})=>{
    const search=new URLSearchParams(params);
    return `/rest/v1/${table}${search.size?`?${search.toString()}`:""}`;
  };
  const cleanText=(value,max=500)=>String(value??"").trim().slice(0,max);
  const slugify=value=>cleanText(value,150).normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/đ/g,"d").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,90);
  const randomCode=()=>crypto.randomUUID().replace(/-/g,"").slice(0,8).toUpperCase();
  const formatCurrency=(value,type="sale")=>{
    const amount=Number(value||0);
    if(!amount)return "Liên hệ";
    if(type==="rent")return `${new Intl.NumberFormat("vi-VN",{maximumFractionDigits:1}).format(amount/1_000_000)} triệu/tháng`;
    if(amount>=1_000_000_000)return `${new Intl.NumberFormat("vi-VN",{maximumFractionDigits:2}).format(amount/1_000_000_000)} tỷ`;
    return `${new Intl.NumberFormat("vi-VN").format(amount)} đ`;
  };
  const imageUrl=path=>path?`${base}/storage/v1/object/public/${encodeURIComponent(config.storageBucket||"listing-images")}/${String(path).split("/").map(encodeURIComponent).join("/")}`:"";
  const listingUrl=listing=>{
    const segment=listing?.listing_type==="rent"?"cho-thue-lumi-hanoi":"mua-ban-lumi-hanoi";
    const slug=cleanText(listing?.slug,120);
    return slug?`/${segment}/${encodeURIComponent(slug)}/`:"/tin-dang-lumi-hanoi/";
  };

  const getSession=()=>{
    try{return JSON.parse(sessionStorage.getItem(sessionKey)||"null");}catch{return null;}
  };
  const saveSession=session=>{
    if(session)sessionStorage.setItem(sessionKey,JSON.stringify({...session,expires_at:session.expires_at||(Math.floor(Date.now()/1000)+Number(session.expires_in||3600))}));
    else sessionStorage.removeItem(sessionKey);
  };
  let refreshInFlight=null;
  const refreshSession=async session=>{
    if(!session?.refresh_token)return null;
    if(refreshInFlight)return refreshInFlight;
    refreshInFlight=(async()=>{try{
      const refreshed=await request("/auth/v1/token?grant_type=refresh_token",{method:"POST",body:{refresh_token:session.refresh_token}});
      saveSession(refreshed);
      return refreshed;
    }catch{saveSession(null);return null;}})();
    try{return await refreshInFlight;}finally{refreshInFlight=null;}
  };
  const validSession=async()=>{
    let session=getSession();
    if(!session)return null;
    let expiresAt=Number(session.expires_at||0);
    if(!expiresAt){saveSession(session);session=getSession();expiresAt=Number(session.expires_at);}
    if(expiresAt&&expiresAt-Date.now()/1000<90)session=await refreshSession(session);
    return session;
  };

  const listPublic=async(type,filters={},options={})=>{
    const params={
      select:"id,slug,listing_code,listing_type,title,description,poster_name,contact_phone,phase,tower,bedroom_count,unit_type,area_sqm,price_vnd,furnishing,floor_label,available_from,is_featured,approved_at,expires_at,created_at,listing_images(id,storage_path,sort_order,alt_text)",
      listing_type:`eq.${type}`,
      status:"eq.approved",
      order:"is_featured.desc,sort_priority.desc,approved_at.desc",
      limit:"120"
    };
    if(filters.phase)params.phase=`eq.${filters.phase}`;
    if(filters.tower)params.tower=`eq.${filters.tower}`;
    if(filters.bedroom)params.unit_type=`eq.${filters.bedroom}`;
    if(filters.minPrice)params.price_vnd=`gte.${Number(filters.minPrice)}`;
    if(filters.maxPrice)params.price_vnd=`lte.${Number(filters.maxPrice)}`;
    const rows=await request(restPath("listings",params),{signal:options.signal});
    const keyword=cleanText(filters.keyword,80).toLocaleLowerCase("vi");
    return keyword?rows.filter(row=>[row.title,row.phase,row.tower,row.unit_type].some(value=>String(value||"").toLocaleLowerCase("vi").includes(keyword))):rows;
  };

  // Apply filters and ordering BEFORE the range. Each inventory request returns
  // at most ten records, even when the marketplace has hundreds of listings.
  const listPublicPage=async(type,filters={},page=1,{signal}={})=>{
    const orders={
      newest:"approved_at.desc.nullslast,created_at.desc,id.desc",
      price_asc:"price_vnd.asc.nullslast,approved_at.desc,id.desc",
      price_desc:"price_vnd.desc.nullslast,approved_at.desc,id.desc",
      area_asc:"area_sqm.asc.nullslast,approved_at.desc,id.desc",
      area_desc:"area_sqm.desc.nullslast,approved_at.desc,id.desc"
    };
    const params={
      select:"id,slug,listing_type,title,poster_name,contact_phone,phase,tower,unit_type,area_sqm,price_vnd,floor_label,is_featured,approved_at,created_at,listing_images(storage_path,sort_order,alt_text)",
      listing_type:`eq.${type==="rent"?"rent":"sale"}`,status:"eq.approved",
      order:orders[filters.sort]||orders.newest,limit:"10",
      offset:String((Math.max(1,Math.min(100000,Math.floor(Number(page)||1)))-1)*10)
    };
    if(filters.phase)params.phase=`eq.${cleanText(filters.phase,40)}`;
    if(filters.tower)params.tower=`eq.${cleanText(filters.tower,40)}`;
    if(filters.bedroom)params.unit_type=`eq.${cleanText(filters.bedroom,40)}`;
    if(Number(filters.maxPrice)>0)params.price_vnd=`lte.${Number(filters.maxPrice)}`;
    const areas={"0-50":"(area_sqm.gt.0,area_sqm.lt.50)","50-70":"(area_sqm.gte.50,area_sqm.lt.70)","70-90":"(area_sqm.gte.70,area_sqm.lt.90)","90-120":"(area_sqm.gte.90,area_sqm.lte.120)","120-9999":"(area_sqm.gt.120)"};
    if(areas[filters.area])params.and=areas[filters.area];
    const keyword=cleanText(filters.keyword,80);
    if(keyword){
      // Quoted PostgREST values keep punctuation out of the query grammar.
      // Treat wildcard characters literally; the surrounding % means contains.
      const literal=keyword.replace(/[\\%_*]/g,"\\$&");
      const value=JSON.stringify(`%${literal}%`);
      params.or=`(${["title","phase","tower","unit_type"].map(field=>`${field}.ilike.${value}`).join(",")})`;
    }
    return request(restPath("listings",params),{signal,withCount:true,headers:{Prefer:"count=exact"}});
  };

  const getPublicListing=async identifier=>{
    const key=/^[0-9a-f-]{36}$/i.test(identifier)?"id":"slug";
    const rows=await request(restPath("listings",{
      select:"id,slug,listing_code,listing_type,title,description,poster_name,phase,tower,bedroom_count,unit_type,area_sqm,price_vnd,furnishing,floor_label,available_from,contact_phone,is_featured,approved_at,expires_at,listing_images(id,storage_path,sort_order,alt_text)",
      [key]:`eq.${identifier}`,
      status:"eq.approved",
      limit:"1"
    }));
    return rows?.[0]||null;
  };

  const createListing=async data=>{
    const id=crypto.randomUUID();
    const listingCode=`LH-${randomCode()}`;
    const slug=`${slugify(data.title)||"tin-dang-lumi-hanoi"}-${listingCode.toLowerCase()}`;
    const payload={...data,id,listing_code:listingCode,slug};
    await request(restPath("listings"),{method:"POST",body:payload,headers:{Prefer:"return=minimal"}});
    return {...payload,status:"pending",is_featured:false,sort_priority:0};
  };

  const uploadImage=async(listingId,file,index)=>{
    const extension=(file.name.split(".").pop()||"jpg").toLowerCase().replace(/[^a-z0-9]/g,"").slice(0,5)||"jpg";
    const path=`pending/${listingId}/${String(index+1).padStart(2,"0")}-${crypto.randomUUID()}.${extension}`;
    const encoded=path.split("/").map(encodeURIComponent).join("/");
    await request(`/storage/v1/object/${encodeURIComponent(config.storageBucket||"listing-images")}/${encoded}`,{
      method:"POST",body:file,headers:{"Content-Type":file.type,"x-upsert":"false"}
    });
    return path;
  };

  const addListingImage=async(listingId,path,index,altText)=>request(restPath("listing_images"),{
    method:"POST",
    body:{listing_id:listingId,storage_path:path,sort_order:index,alt_text:cleanText(altText,180)},
    headers:{Prefer:"return=minimal"}
  });


  const createReport=async(listingId,reason,details)=>request(restPath("listing_reports"),{
    method:"POST",
    body:{listing_id:listingId,reason:cleanText(reason,40),details:cleanText(details,600)},
    headers:{Prefer:"return=minimal"}
  });

  const isAdminSession=async session=>{
    if(!session?.access_token)return false;
    let user=session.user;
    if(!user?.id)user=await request("/auth/v1/user",{token:session.access_token});
    if(!user?.id)return false;
    const rows=await request(restPath("admin_users",{select:"user_id",user_id:`eq.${user.id}`,limit:"1"}),{token:session.access_token});
    return Boolean(rows?.length);
  };

  const signIn=async(email,password)=>{
    const session=await request("/auth/v1/token?grant_type=password",{method:"POST",body:{email:cleanText(email,200),password:String(password||"")}});
    saveSession(session);
    const allowed=await isAdminSession(session);
    if(!allowed){saveSession(null);throw new MarketplaceError("Tài khoản này không có quyền quản trị.",403);}
    return session;
  };
  const signOut=async()=>{
    const session=getSession();
    if(session?.access_token){try{await request("/auth/v1/logout",{method:"POST",token:session.access_token});}catch{} }
    saveSession(null);
  };
  const requireAdmin=async()=>{
    const session=await validSession();
    if(!session)return null;
    try{
      const allowed=await isAdminSession(session);
      return allowed?session:null;
    }catch{return null;}
  };
  const listAdmin=async()=>{
    const session=await requireAdmin();
    if(!session)throw new MarketplaceError("Phiên quản trị đã hết hạn.",401);
    return request(restPath("listings",{select:"*,listing_images(*),listing_reports(id,reason,details,created_at)",order:"created_at.desc",limit:"300"}),{token:session.access_token});
  };
  const updateListing=async(id,patch,expectedUpdatedAt)=>{
    const session=await requireAdmin();
    if(!session)throw new MarketplaceError("Phiên quản trị đã hết hạn.",401);
    const params={id:`eq.${id}`};
    if(expectedUpdatedAt)params.updated_at=`eq.${expectedUpdatedAt}`;
    const result=await request(restPath("listings",params),{method:"PATCH",body:patch,token:session.access_token,headers:{Prefer:"return=representation"}});
    if(!Array.isArray(result)||result.length!==1)throw new MarketplaceError("Tin đã thay đổi hoặc không còn tồn tại. Tải lại tin để kiểm tra trước khi lưu.",409);
    return result[0];
  };

  // Admin queries filter the entire inventory before paging. List payloads only
  // include one thumbnail and one open-report marker; full content is on demand.
  const adminParams=(filters={},now=new Date())=>{
    const params={};const clauses=[];const stamp=now.toISOString();
    const status=filters.status||"";
    if(status==="approved")clauses.push("status.eq.approved",`or(expires_at.is.null,expires_at.gt.${stamp})`);
    else if(status==="expired")clauses.push(`or(status.eq.expired,and(status.eq.approved,expires_at.lte.${stamp}))`);
    else if(status==="expiring")clauses.push("status.eq.approved",`expires_at.gt.${stamp}`,`expires_at.lte.${new Date(now.getTime()+7*86400000).toISOString()}`);
    else if(["pending","rejected","sold","rented"].includes(status))params.status=`eq.${status}`;
    if(["sale","rent"].includes(filters.type))params.listing_type=`eq.${filters.type}`;
    if(["Signature","Prestige","Elite"].includes(filters.phase))params.phase=`eq.${filters.phase}`;
    if(["S1","S2","S3","S5","S6","P1","P2","E1","E2"].includes(filters.tower))params.tower=`eq.${filters.tower}`;
    if(["1PN","2PN","3PN","4PN","Duplex","Penthouse","Shop chân đế"].includes(filters.unit_type))params.unit_type=`eq.${filters.unit_type}`;
    if(filters.featured==="yes")params.is_featured="eq.true";
    const keyword=cleanText(filters.keyword,100);
    if(keyword){
      const quoted=value=>JSON.stringify(`%${value.replace(/[\\%_*]/g,"\\$&")}%`);
      const terms=["title","slug","listing_code","poster_name","contact_phone","tower"].map(field=>`${field}.ilike.${quoted(keyword)}`);
      const phone=keyword.replace(/[\s().-]/g,"");
      if(/^\+?\d{6,15}$/.test(phone)&&phone!==keyword)terms.push(`contact_phone.ilike.${quoted(phone)}`);
      clauses.push(`or(${terms.join(",")})`);
    }
    if(clauses.length)params.and=`(${clauses.join(",")})`;
    return params;
  };
  const adminToken=async()=>{
    const session=await requireAdmin();
    if(!session)throw new MarketplaceError("Phiên quản trị đã hết hạn. Vui lòng đăng nhập lại.",401);
    return session;
  };
  const listAdminPage=async(filters={},page=1,{pageSize=20,signal}={})=>{
    const session=await adminToken();
    const size=[20,50,100].includes(Number(pageSize))?Number(pageSize):20;
    const orders={newest:"created_at.desc,id.desc",oldest:"created_at.asc,id.asc",updated:"updated_at.desc,id.desc",expiry:"expires_at.asc.nullslast,id.desc"};
    const params={...adminParams(filters),
      select:"id,listing_code,slug,listing_type,status,title,phase,tower,unit_type,area_sqm,price_vnd,poster_name,contact_phone,contact_public,is_featured,sort_priority,approved_at,expires_at,created_at,updated_at,listing_images(storage_path,sort_order),open_reports:listing_reports(id)",
      order:orders[filters.sort]||orders.newest,limit:String(size),offset:String((Math.max(1,Math.min(100000,Math.floor(Number(page)||1)))-1)*size),
      "listing_images.order":"sort_order.asc,id.asc","listing_images.limit":"1","open_reports.resolved_at":"is.null","open_reports.limit":"1"
    };
    if(filters.status==="reported")params.open_reports="not.is.null";
    return request(restPath("listings",params),{token:session.access_token,signal,withCount:true,headers:{Prefer:"count=exact"}});
  };
  const adminCounts=async({signal}={})=>{
    const session=await adminToken();const now=new Date();
    const entries=await Promise.all(["all","pending","approved","expiring","reported"].map(async key=>{
      const params={...adminParams({status:key},now),select:"id",limit:"1"};
      if(key==="reported")Object.assign(params,{select:"id,open_reports:listing_reports()","open_reports.resolved_at":"is.null",open_reports:"not.is.null"});
      const result=await request(restPath("listings",params),{method:"HEAD",token:session.access_token,signal,withCount:true,headers:{Prefer:"count=exact"}});
      return [key,result.total];
    }));
    return Object.fromEntries(entries);
  };
  const getAdminListing=async(id,{signal}={})=>{
    const session=await adminToken();
    const result=await request(restPath("listings",{id:`eq.${cleanText(id,50)}`,select:"*,listing_images(*),listing_reports(id,reason,details,created_at,resolved_at)","listing_images.order":"sort_order.asc,id.asc","listing_reports.order":"created_at.desc",limit:"1"}),{token:session.access_token,signal});
    if(!result?.length)throw new MarketplaceError("Tin không còn tồn tại hoặc bạn không có quyền truy cập.",404);
    return result[0];
  };
  const applyAdminAction=async(items,action,{onProgress}={})=>{
    if(!Array.isArray(items)||!items.length||items.length>100)throw new MarketplaceError("Chọn từ 1 đến 100 tin trên trang hiện tại.",400);
    if(!["approve","hide","reject","done","feature","unfeature"].includes(action))throw new MarketplaceError("Thao tác không hợp lệ.",400);
    const session=await adminToken();const success=[];const failed=[];
    const stamp=new Date().toISOString();
    const expiry=new Date(Date.now()+Number(config.listingLifetimeDays||45)*86400000).toISOString();
    const queue=[...new Map(items.map(item=>[item.id,item])).values()];
    let next=0;
    const work=async()=>{while(next<queue.length){
      const row=queue[next++];
      try{
        if(!row.updated_at)throw new MarketplaceError("Cần tải lại tin trước khi thao tác.",409);
        if(action==="approve"&&!row.contact_public)throw new MarketplaceError("Người đăng chưa đồng ý công khai liên hệ.",400);
        if(action==="feature"&&(row.status!=="approved"||(row.expires_at&&new Date(row.expires_at)<=new Date())))throw new MarketplaceError("Chỉ ghim tin đang hiển thị.",400);
        const patches={approve:{status:"approved",approved_at:row.approved_at||stamp,expires_at:expiry},hide:{status:"expired",expires_at:stamp,is_featured:false,sort_priority:0},reject:{status:"rejected",is_featured:false,sort_priority:0},done:{status:row.listing_type==="rent"?"rented":"sold",is_featured:false,sort_priority:0},feature:{is_featured:true,sort_priority:100},unfeature:{is_featured:false,sort_priority:0}};
        const changed=await request(restPath("listings",{id:`eq.${row.id}`,updated_at:`eq.${row.updated_at}`,select:"id"}),{method:"PATCH",body:patches[action],token:session.access_token,headers:{Prefer:"return=representation"}});
        if(!Array.isArray(changed)||changed.length!==1)throw new MarketplaceError("Tin đã thay đổi. Tải lại để kiểm tra.",409);
        success.push(row.id);
      }catch(error){failed.push({id:row.id,code:row.listing_code,message:error.message});}
      onProgress?.({done:success.length+failed.length,total:queue.length});
    }};
    await Promise.all(Array.from({length:Math.min(3,queue.length)},work));
    return {success,failed};
  };
  const resolveAdminReports=async(listingId,reportIds)=>{
    const ids=[...new Set(reportIds)].filter(id=>/^\d+$/.test(String(id)));
    if(!ids.length)return 0;
    const session=await adminToken();
    const changed=await request(restPath("listing_reports",{listing_id:`eq.${listingId}`,id:`in.(${ids.join(",")})`,resolved_at:"is.null",select:"id"}),{method:"PATCH",body:{resolved_at:new Date().toISOString(),resolved_by:session.user.id},token:session.access_token,headers:{Prefer:"return=representation"}});
    return changed?.length||0;
  };
  const deleteListing=async listing=>{
    const session=await requireAdmin();
    if(!session)throw new MarketplaceError("Phiên quản trị đã hết hạn.",401);
    const id=cleanText(listing?.id,50);
    if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id))throw new MarketplaceError("Không xác định được tin cần xóa.",400);
    const imagePaths=[...new Set((listing?.listing_images||[]).map(image=>cleanText(image?.storage_path,500)).filter(Boolean))];
    if(imagePaths.length){
      await request(`/storage/v1/object/${encodeURIComponent(config.storageBucket||"listing-images")}`,{
        method:"DELETE",body:{prefixes:imagePaths},token:session.access_token
      });
    }
    const deleted=await request(restPath("listings",{id:`eq.${id}`}),{
      method:"DELETE",token:session.access_token,headers:{Prefer:"return=representation"}
    });
    if(!Array.isArray(deleted)||deleted.length!==1)throw new MarketplaceError("Tin không còn tồn tại hoặc anh/chị không có quyền xóa.",404);
    return {id,deletedImageCount:imagePaths.length};
  };

  const requestSeoSync=async(reason="admin_change")=>{
    const session=await requireAdmin();
    if(!session)throw new MarketplaceError("Phiên quản trị đã hết hạn.",401);
    return request("/functions/v1/marketplace-seo-sync",{
      method:"POST",
      body:{reason:cleanText(reason,80)},
      token:session.access_token
    });
  };

  window.LumiMarketplace={
    config,configured,MarketplaceError,cleanText,slugify,formatCurrency,imageUrl,listingUrl,
    listPublic,listPublicPage,getPublicListing,createListing,uploadImage,addListingImage,createReport,
    signIn,signOut,requireAdmin,listAdmin,updateListing,deleteListing,requestSeoSync,
    listAdminPage,adminCounts,getAdminListing,applyAdminAction,resolveAdminReports
  };
})();
