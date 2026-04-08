// src/lib/supabaseClient.ts
//
// This file creates ONE Supabase client that the whole frontend shares.
// Think of it like a "phone line" to our database — we only need to set
// it up once and then every component can use it.

import { createClient } from '@supabase/supabase-js';

// import.meta.env is how Vite reads environment variables.
// Variables must start with VITE_ to be available in the browser.
// These values come from the .env file in your project root folder.
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_KEY as string;

// createClient connects to your Supabase project.
// The anon/public key is safe to expose in the browser —
// Supabase's Row Level Security controls what can be read/written.
export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
