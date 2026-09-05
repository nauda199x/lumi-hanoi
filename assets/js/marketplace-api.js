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
    if(session)sessionStorage.setItem(sessionKey,JSON.stringify(session));
    else sessionStorage.removeItem(sessionKey);
  };
  const refreshSession=async session=>{
    if(!session?.refresh_token)return null;
    try{
      const refreshed=await request("/auth/v1/token?grant_type=refresh_token",{method:"POST",body:{refresh_token:session.refresh_token}});
      saveSession(refreshed);
      return refreshed;
    }catch{saveSession(null);return null;}
  };
  const validSession=async()=>{
    let session=getSession();
    if(!session)return null;
    const expiresAt=Number(session.expires_at||0);
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
  const updateListing=async(id,patch)=>{
    const session=await requireAdmin();
    if(!session)throw new MarketplaceError("Phiên quản trị đã hết hạn.",401);
    return request(restPath("listings",{id:`eq.${id}`}),{method:"PATCH",body:patch,token:session.access_token,headers:{Prefer:"return=minimal"}});
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
    signIn,signOut,requireAdmin,listAdmin,updateListing,deleteListing,requestSeoSync
  };
})();
