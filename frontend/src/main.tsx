import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import type { Session } from '@supabase/supabase-js';
import './index.css';
import { supabase, iniciarSesionGoogleUdea, cerrarSesion } from './lib/supabase';
import { DashboardDocente, DatosDashboardCurso } from './components/DashboardDocente';
import { FormularioEncuesta } from './components/FormularioEncuesta';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const MODULOS_UDEA = [
  { sigla: 'MAT', titulo: 'Proceso de matrícula', id: 'mat' },
  { sigla: 'CIC', titulo: 'Ciclo de vida académica y proceso de graduación', id: 'encuesta', tieneMenu: true },
  { sigla: 'PRA', titulo: 'Prácticas académicas', id: 'pra' },
  { sigla: 'REP', titulo: 'Consultas y representaciones (Dashboard N >= 5)', id: 'dashboard' },
  { sigla: 'SER', titulo: 'Servicios para la formación integral y la permanencia', id: 'ser' },
  { sigla: 'CER', titulo: 'Certificados, formatos, trámites y solicitudes', id: 'cer' },
];

const App = () => {
  const [session, setSession] = useState<Session | null>(null);
  const [vista, setVista] = useState<'dashboard' | 'encuesta'>('dashboard');
  const [menuCicAbierto, setMenuCicAbierto] = useState<boolean>(false);
  const [datos, setDatos] = useState<DatosDashboardCurso | null>(null);
  const [errorApi, setErrorApi] = useState<string>('');
  const [credencial, setCredencial] = useState<{ token: string; firma: string } | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, nuevaSesion) => {
      setSession(nuevaSesion);
    });

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  const cargarDashboard = async () => {
    try {
      setErrorApi('');
      const res = await fetch(`${API_BASE}/api/v1/dashboard/curso/ING-SIS-2026`);
      if (!res.ok) throw new Error('Error al consultar el dashboard');
      setDatos(await res.json());
    } catch {
      setErrorApi(`No se pudo conectar con la API en ${API_BASE}. Verifica que uvicorn esté encendido.`);
    }
  };

  const solicitarTokenYabrirEncuesta = async () => {
    if (!session) {
      setErrorApi('Debes iniciar sesión con tu correo @udea.edu.co antes de diligenciar la encuesta.');
      return;
    }

    try {
      setErrorApi('');
      const idAleatorio = Math.floor(Math.random() * 900000) + 100000;
      const tok = 'token_anonimo_udea_v02_' + idAleatorio;

      const res = await fetch(`${API_BASE}/api/v1/auth/solicitar-token-ciego`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          correo_institucional: session.user.email,
          curso_codigo: 'ING-SIS-2026',
          semestre: '2026-2',
          token_cegado: tok,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'No se pudo emitir el token anónimo.');
      }

      setCredencial({ token: tok, firma: data.firma_ciega });
      setMenuCicAbierto(false);
      setVista('encuesta');
    } catch (err: any) {
      setErrorApi(err.message || 'Error al solicitar el token ciego al servidor.');
    }
  };

  const manejarLogin = async () => {
    try {
      setErrorApi('');
      await iniciarSesionGoogleUdea();
    } catch (err: any) {
      setErrorApi('Error al iniciar sesión con Google: ' + (err.message || err));
    }
  };

  const manejarLogout = async () => {
    await cerrarSesion();
    setCredencial(null);
    setVista('dashboard');
  };

  useEffect(() => {
    cargarDashboard();
  }, [vista]);

  const nombreUsuario = session?.user?.email
    ? session.user.email.split('@')[0].toUpperCase()
    : null;

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <div className="bg-udea-nav text-white text-xs py-1.5 px-6 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <span className="font-black tracking-wider text-sm">gov.co</span>
          <span className="hidden sm:inline text-white/90">
            Participa &nbsp;|&nbsp; Transparencia &nbsp;|&nbsp; Atención a la ciudadanía
          </span>
        </div>
        <div className="flex items-center gap-3 font-medium">
          <span>EN</span>
          <span className="font-bold underline">ES</span>
        </div>
      </div>

      <header className="bg-white py-4 px-6 border-b border-slate-200">
        <div className="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-4">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-12 bg-udea-primary text-white flex items-center justify-center font-serif font-bold text-lg rounded-sm shadow-sm">
                UdeA
              </div>
              <div className="leading-tight font-serif text-udea-primary font-bold text-sm tracking-wide">
                UNIVERSIDAD<br />DE ANTIOQUIA
              </div>
            </div>

            <nav className="hidden md:flex items-center gap-6 text-xs text-slate-700">
              <button
                onClick={solicitarTokenYabrirEncuesta}
                className={vista === 'encuesta' ? 'font-bold text-udea-primary border-b-2 border-udea-primary pb-0.5' : 'hover:text-udea-primary'}
              >
                Estudiante
              </button>
              <button
                onClick={() => setVista('dashboard')}
                className={vista === 'dashboard' ? 'font-bold text-udea-primary border-b-2 border-udea-primary pb-0.5' : 'hover:text-udea-primary'}
              >
                Profesor
              </button>
              <span className="text-slate-500">Empleado</span>
              <span className="text-slate-500">Egresado</span>
              <span className="text-slate-500">Jubilado</span>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            {session ? (
              <>
                <div className="bg-udea-gold text-slate-900 font-bold text-xs px-4 py-2.5 flex items-center gap-2 shadow-sm">
                  <span>👤</span>
                  <span>{nombreUsuario}</span>
                </div>
                <button
                  onClick={manejarLogout}
                  className="bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs px-3 py-2.5 transition cursor-pointer"
                >
                  Salir
                </button>
              </>
            ) : (
              <button
                onClick={manejarLogin}
                className="bg-udea-gold hover:brightness-95 text-slate-900 font-bold text-xs px-4 py-2.5 flex items-center gap-2 shadow-sm transition cursor-pointer"
              >
                <span>🔐</span>
                <span>Iniciar sesión @udea.edu.co</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="bg-udea-nav text-white text-xs">
        <div className="max-w-7xl mx-auto px-6 py-2.5 flex flex-wrap justify-between gap-4 font-medium">
          <span>La UdeA</span>
          <span>Estudia en la UdeA</span>
          <span className="font-bold underline">Docencia</span>
          <span>Investigación</span>
          <span>Extensión</span>
          <span>Internacional</span>
          <span>Cultura</span>
          <span>Bienestar</span>
          <span>Unidades académicas</span>
        </div>
      </div>

      <div className="bg-gradient-to-r from-udea-lightlime via-udea-nav to-udea-primary text-white py-1.5 px-6 text-sm italic font-medium">
        <div className="max-w-7xl mx-auto">
          Soy Estudiante UdeA {session ? `— Sesión activa: ${session.user.email}` : ''}
        </div>
      </div>

      <div className="bg-udea-dark text-white py-10 px-6 relative">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="space-y-1.5 max-w-2xl">
            <p className="text-udea-lightlime font-bold text-2xl md:text-3xl">
              ¡Valoración Docente con Controles Antisesgo!
            </p>
            <p className="font-serif text-xl md:text-2xl text-white/90">
              Instrumento v0.2: Firma ciega RSA y separación física de bases de datos
            </p>
            <p className="text-udea-lime font-bold text-xl pt-1">
              Proyecto Integrador I · Semestre 2026-2
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={solicitarTokenYabrirEncuesta}
              className="px-5 py-2.5 bg-udea-lime hover:bg-udea-lightlime text-white font-bold text-xs uppercase tracking-wider transition shadow cursor-pointer"
            >
              Diligenciar Encuesta (21 ítems)
            </button>
            <button
              onClick={() => setVista('dashboard')}
              className="px-5 py-2.5 bg-udea-primary hover:bg-udea-nav border border-white/25 text-white font-bold text-xs uppercase tracking-wider transition cursor-pointer"
            >
              Consultar Dashboard
            </button>
          </div>
        </div>
      </div>

      <div className="bg-udea-grayinactive border-b border-slate-300 relative">
        <div className="max-w-7xl mx-auto grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
          {MODULOS_UDEA.map((m) => {
            const activo =
              (m.id === 'encuesta' && (vista === 'encuesta' || menuCicAbierto)) ||
              (m.id === 'dashboard' && vista === 'dashboard');
            return (
              <div key={m.sigla} className="relative">
                <button
                  onClick={() => {
                    if (m.tieneMenu) setMenuCicAbierto(!menuCicAbierto);
                    else if (m.id === 'dashboard') {
                      setMenuCicAbierto(false);
                      setVista('dashboard');
                    }
                  }}
                  className={`w-full h-full text-left p-4 relative transition border-b-4 cursor-pointer ${
                    activo
                      ? 'bg-udea-graytab border-t-2 border-x-2 border-t-udea-primary border-x-udea-primary border-b-udea-primary'
                      : 'bg-udea-grayinactive border-b-udea-lime hover:bg-udea-graytab'
                  }`}
                >
                  <div className="text-3xl font-bold text-slate-400/60 tracking-tight leading-none mb-1">
                    {m.sigla}
                  </div>
                  <div className="text-xs text-slate-800 font-medium leading-snug pr-3">
                    {m.titulo}
                  </div>
                  <span className="absolute bottom-2 right-3 text-[10px] text-slate-600">▼</span>
                </button>

                {m.tieneMenu && menuCicAbierto && (
                  <div className="absolute left-0 top-full w-full bg-udea-primary text-white text-xs z-30 shadow-lg divide-y divide-white/15">
                    <div className="px-4 py-2.5 hover:bg-udea-dark cursor-pointer">Plan de estudios</div>
                    <div className="px-4 py-2.5 hover:bg-udea-dark cursor-pointer">Notas académicas</div>
                    <button
                      onClick={solicitarTokenYabrirEncuesta}
                      className="w-full text-left px-4 py-2.5 bg-udea-lime hover:bg-udea-lightlime font-bold text-white cursor-pointer"
                    >
                      ★ Valoración Docente v0.2 (Anónima)
                    </button>
                    <button
                      onClick={() => {
                        setMenuCicAbierto(false);
                        setVista('dashboard');
                      }}
                      className="w-full text-left px-4 py-2.5 hover:bg-udea-dark cursor-pointer"
                    >
                      Dashboard Docente (N &gt;= 5)
                    </button>
                    <div className="px-4 py-2.5 hover:bg-udea-dark cursor-pointer">Historia académica</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {errorApi && (
        <div className="max-w-5xl mx-auto mt-6 px-4 w-full">
          <div className="p-4 bg-red-50 border-l-4 border-red-600 text-red-900 text-sm flex justify-between items-center gap-4">
            <span>{errorApi}</span>
            <button
              onClick={() => setErrorApi('')}
              className="px-3 py-1 bg-red-700 text-white text-xs font-bold uppercase cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}

      <div className="flex-1 pb-12">
        {vista === 'dashboard' && datos && <DashboardDocente datos={datos} />}
        {vista === 'encuesta' && credencial && (
          <FormularioEncuesta
            apiUrl={API_BASE}
            cursoCodigo="ING-SIS-2026"
            firmaToken={credencial.firma}
            tokenAnonimo={credencial.token}
          />
        )}
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);