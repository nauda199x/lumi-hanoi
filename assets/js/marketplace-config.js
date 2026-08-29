/*
 * Public browser configuration for the Lumi Hanoi marketplace.
 * The Supabase anon key is designed to be public. Never place a service-role
 * key, database password or another private credential in this file.
 */
window.LUMI_MARKETPLACE_CONFIG = Object.freeze({
  supabaseUrl: "",
  supabaseAnonKey: "",
  storageBucket: "listing-images",
  maxImages: 12,
  maxImageBytes: 5 * 1024 * 1024,
  listingLifetimeDays: 45
});
