/*
 * Public browser configuration for the Lumi Hanoi marketplace.
 * The Supabase publishable key is designed for public browser clients. Never
 * place a secret/service-role key, database password or private credential here.
 */
window.LUMI_MARKETPLACE_CONFIG = Object.freeze({
  supabaseUrl: "",
  supabasePublishableKey: "",
  storageBucket: "listing-images",
  maxImages: 12,
  maxImageBytes: 5 * 1024 * 1024,
  listingLifetimeDays: 45
});
