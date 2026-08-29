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
