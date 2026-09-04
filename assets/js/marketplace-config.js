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
