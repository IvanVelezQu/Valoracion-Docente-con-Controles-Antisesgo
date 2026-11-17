import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import { DashboardDocente, DatosDashboardCurso } from './components/DashboardDocente';
import { FormularioEncuesta } from './components/FormularioEncuesta';

const MODULOS_UDEA = [
  { sigla: 'MAT', titulo: 'Proceso de matrícula', id: 'mat' },
  { sigla: 'CIC', titulo: 'Ciclo de vida académica y proceso de graduación', id: 'encuesta', tieneMenu: true },
  { sigla: 'PRA', titulo: 'Prácticas académicas', id: 'pra' },
  { sigla: 'REP', titulo: 'Consultas y representaciones (Dashboard N >= 5)', id: 'dashboard' },
  { sigla: 'SER', titulo: 'Servicios para la formación integral y la permanencia', id: 'ser' },
  { sigla: 'CER', titulo: 'Certificados, formatos, trámites y solicitudes', id: 'cer' },
];

const App = () => {
  const [vista, setVista] = useState<'dashboard' | 'encuesta'>('dashboard');
  const [menuCicAbierto, setMenuCicAbierto] = useState<boolean>(false);
  const [datos, setDatos] = useState<DatosDashboardCurso | null>(null);
  const [errorApi, setErrorApi] = useState<string>('');
  const [sembrando, setSembrando] = useState<boolean>(false);
  const [credencial, setCredencial] = useState<{ token: string; firma: string; usuario: string } | null>(null);

  const cargarDashboard = async () => {
    try {
      setErrorApi('');
      const res = await fetch('http://127.0.0.1:8000/api/v1/dashboard/curso/ING-SIS-2026');
      if (!res.ok) throw new Error('Error al consultar el dashboard');
      setDatos(await res.json());
    } catch {
      setErrorApi('No se pudo conectar con la API en http://127.0.0.1:8000. Verifica que uvicorn esté encendido.');
    }
  };

  const generarTokenDemo = async () => {
    try {
      setErrorApi('');
      const id = Math.floor(Math.random() * 9000) + 1000;
      const tok = 'token_udea_' + id;
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/solicitar-token-ciego', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          correo_institucional: 'ivan.velez' + id + '@udea.edu.co',
          curso_codigo: 'ING-SIS-2026',
          semestre: '2026-2',
          token_cegado: tok,
        }),
      });
      const data = await res.json();
      setCredencial({ token: tok, firma: data.firma_ciega, usuario: 'IVAN.VELEZ' + id });
      setMenuCicAbierto(false);
      setVista('encuesta');
    } catch {
      setErrorApi('No se pudo emitir el token ciego. Asegúrate de que el servidor FastAPI esté corriendo en el puerto 8000.');
    }
  };

  const sembrarEncuestasDemo = async () => {
    setSembrando(true);
    try {
      for (let i = 1; i <= 6; i++) {
        const suffix = Math.floor(Math.random() * 90000) + 10000;
        const tok = `token_semilla_${i}_${suffix}`;
        const r1 = await fetch('http://127.0.0.1:8000/api/v1/auth/solicitar-token-ciego', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            correo_institucional: `estudiante.semilla${suffix}@udea.edu.co`,
            curso_codigo: 'ING-SIS-2026',
            semestre: '2026-2',
            token_cegado: tok,
          }),
        });
        const { firma_ciega } = await r1.json();
        const esHalo = i === 6;
        await fetch('http://127.0.0.1:8000/api/v1/encuestas/enviar', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            curso_codigo: 'ING-SIS-2026',
            semestre: '2026-2',
            token_anonimo: tok,
            firma_token: firma_ciega,
            duracion_seg: esHalo ? 18 : 205,
            AR_01: 4, AR_02: 4, AR_03: 3,
            SEP_01: 4, SEP_02: 1, SEP_03: 4,
            DIM_01: 5, DIM_02: esHalo ? 5 : 4, DIM_03: 5, DIM_04: esHalo ? 5 : 4,
            DIM_05: 5, DIM_06: esHalo ? 5 : 4, DIM_07: 5, DIM_08: esHalo ? 5 : 4,
            REF_01: 5, REF_02: 5, REF_03: esHalo ? 5 : 4,
            INV_01: esHalo ? 5 : 1, INV_02: esHalo ? 5 : 2, INV_03: esHalo ? 5 : 2, INV_04: esHalo ? 5 : 1,
          }),
        });
      }
      await cargarDashboard();
    } finally {
      setSembrando(false);
    }
  };

  useEffect(() => {
    cargarDashboard();
  }, [vista]);

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* 1. Barra superior GOV.CO */}
      <div className="bg-udea-nav text-white text-xs py-1.5 px-6 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <span className="font-black tracking-wider text-sm">gov.co</span>
          <span className="hidden sm:inline text-white/90">
            Participa &nbsp;|&nbsp; Transparencia &nbsp;|&nbsp; Atención a la ciudadanía
          </span>
        </div>
        <div className="flex items-center gap-3 font-medium">
          <span>🔍</span>
          <span>EN</span>
          <span className="font-bold underline">ES</span>
        </div>
      </div>

      {/* 2. Cabezote blanco Universidad de Antioquia */}
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
                onClick={generarTokenDemo}
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

          <div className="flex items-center gap-5">
            <div className="hidden lg:flex items-center gap-1.5 text-[11px] text-slate-600">
              <span className="font-bold text-udea-dark">EMISORA CULTURAL UDEA</span>
              <span className="bg-slate-300 text-slate-800 px-1.5 py-0.5 font-bold rounded-l">AM</span>
              <span className="bg-udea-lime text-white px-1.5 py-0.5 font-bold rounded-r">FM</span>
            </div>
            <span className="text-xs text-slate-700 hidden sm:inline">☰ Enlaces de interés</span>
            <button
              onClick={generarTokenDemo}
              className="bg-udea-gold hover:brightness-95 text-slate-900 font-bold text-xs px-4 py-2.5 flex items-center gap-2 shadow-sm transition"
            >
              <span>👤</span>
              <span>{credencial ? credencial.usuario : 'IVAN.VELEZ1'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* 3. Barra verde institucional de navegación */}
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

      {/* 4. Cintillo degradado "Soy Estudiante UdeA" */}
      <div className="bg-gradient-to-r from-udea-lightlime via-udea-nav to-udea-primary text-white py-1.5 px-6 text-sm italic font-medium">
        <div className="max-w-7xl mx-auto">
          Soy Estudiante UdeA
        </div>
      </div>

      {/* 5. Banner Hero institucional oscuro */}
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
              onClick={generarTokenDemo}
              className="px-5 py-2.5 bg-udea-lime hover:bg-udea-lightlime text-white font-bold text-xs uppercase tracking-wider transition shadow"
            >
              Diligenciar Encuesta (21 ítems)
            </button>
            <button
              onClick={() => setVista('dashboard')}
              className="px-5 py-2.5 bg-udea-primary hover:bg-udea-nav border border-white/25 text-white font-bold text-xs uppercase tracking-wider transition"
            >
              Consultar Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* 6. Barra de módulos grises MAT / CIC / PRA / REP / SER / CER con menú desplegable en CIC */}
      <div className="bg-udea-grayinactive border-b border-slate-300 relative">
        <div className="max-w-7xl mx-auto grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
          {MODULOS_UDEA.map((m) => {
            const activo = (m.id === 'encuesta' && (vista === 'encuesta' || menuCicAbierto)) || (m.id === 'dashboard' && vista === 'dashboard');
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
                  className={`w-full h-full text-left p-4 relative transition border-b-4 ${
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
                      onClick={generarTokenDemo}
                      className="w-full text-left px-4 py-2.5 bg-udea-lime hover:bg-udea-lightlime font-bold text-white"
                    >
                      ★ Valoración Docente v0.2 (Anónima)
                    </button>
                    <button
                      onClick={() => {
                        setMenuCicAbierto(false);
                        setVista('dashboard');
                      }}
                      className="w-full text-left px-4 py-2.5 hover:bg-udea-dark"
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

      {/* Aviso si el backend FastAPI está apagado */}
      {errorApi && (
        <div className="max-w-5xl mx-auto mt-6 px-4 w-full">
          <div className="p-4 bg-red-50 border-l-4 border-red-600 text-red-900 text-sm flex justify-between items-center">
            <span>{errorApi}</span>
            <button
              onClick={cargarDashboard}
              className="px-3 py-1 bg-red-700 text-white text-xs font-bold uppercase"
            >
              Reintentar
            </button>
          </div>
        </div>
      )}

      {/* 7. Contenido principal */}
      <div className="flex-1 pb-12">
        {vista === 'dashboard' && datos && (
          <DashboardDocente
            datos={datos}
            onSembrarDatos={sembrarEncuestasDemo}
            sembrando={sembrando}
          />
        )}
        {vista === 'encuesta' && credencial && (
          <FormularioEncuesta
            cursoCodigo="ING-SIS-2026"
            tokenAnonimo={credencial.token}
            firmaToken={credencial.firma}
            apiUrl="http://127.0.0.1:8000"
          />
        )}
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);