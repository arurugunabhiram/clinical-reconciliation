import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Noop stub so the app loads even when Supabase env vars are not yet configured.
// Counters show 0, inserts are silently skipped, real-time is a no-op.
const noopClient = {
  from: () => ({
    select: () => ({
      eq: () => Promise.resolve({ count: 0, data: [], error: null }),
      order: () => ({ limit: () => Promise.resolve({ data: [], error: null }) }),
    }),
    insert: () => Promise.resolve({ data: null, error: null }),
  }),
  channel: () => {
    const ch = { on: () => ch, subscribe: () => ch };
    return ch;
  },
  removeChannel: () => {},
};

// In production, real Supabase credentials are injected via Vercel env vars.
// Locally, if the vars are absent, the noopClient above silences all calls.
export const supabase =
  supabaseUrl && supabaseAnonKey
    ? createClient(supabaseUrl, supabaseAnonKey)
    : noopClient;
