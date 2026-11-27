/// <reference types="vite/client" />
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export const iniciarSesionGoogleUdea = async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin,
      queryParams: {
        hd: 'udea.edu.co', // Sugiere directamente cuentas de Google Workspace UdeA
        prompt: 'select_account',
      },
    },
  });
  if (error) throw error;
};

export const cerrarSesion = async () => {
  await supabase.auth.signOut();
};