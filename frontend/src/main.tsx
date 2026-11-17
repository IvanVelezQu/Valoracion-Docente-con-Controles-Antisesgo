import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { DashboardDocente, DatosDashboardCurso } from './components/DashboardDocente';
import { FormularioEncuesta } from './components/FormularioEncuesta';

const App = () => {
  const [vista, setVista] = useState<'dashboard' | 'encuesta'>('dashboard');
  const [datos, setDatos] = useState<DatosDashboardCurso | null>(null);
  const [credencial, setCredencial] = useState<{ token: string; firma: string } | null>(null);

  const cargarDashboard = async () => {
    const res = await fetch('http://127.0.0.1:8000/api/v1/dashboard/curso/ING-SIS-2026');
    setDatos(await res.json());
  };

  const generarTokenDemo = async () => {
    const id = Math.floor(Math.random() * 90000) + 10000;
    const tok = 'token_demo_' + id;
    const res = await fetch('http://127.0.0.1:8000/api/v1/auth/solicitar-token-ciego', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        correo_institucional: 'estudiante' + id + '@udea.edu.co',
        curso_codigo: 'ING-SIS-2026',
        semestre: '2026-2',
        token_cegado: tok,
      }),
    });
    const data = await res.json();
    setCredencial({ token: tok, firma: data.firma_ciega });
    setVista('encuesta');
  };

  useEffect(() => {
    cargarDashboard();
  }, [vista]);

  return (
    <div className="py-8 px-4 space-y-6">
      <nav className="max-w-5xl mx-auto flex gap-3 bg-white p-3 rounded-xl shadow-sm border border-slate-200">
        <button
          onClick={() => setVista('dashboard')}
          className={'px-4 py-2 rounded-lg font-medium text-sm ' + (vista === 'dashboard' ? 'bg-indigo-600 text-white' : 'text-slate-700 hover:bg-slate-100')}
        >
          Ver Dashboard Docente (Plotly)
        </button>
        <button
          onClick={generarTokenDemo}
          className={'px-4 py-2 rounded-lg font-medium text-sm ' + (vista === 'encuesta' ? 'bg-indigo-600 text-white' : 'text-slate-700 hover:bg-slate-100')}
        >
          Simular Nuevo Estudiante (21 ítems)
        </button>
      </nav>

      {vista === 'dashboard' && datos && <DashboardDocente datos={datos} />}
      {vista === 'encuesta' && credencial && (
        <FormularioEncuesta
          cursoCodigo="ING-SIS-2026"
          tokenAnonimo={credencial.token}
          firmaToken={credencial.firma}
          apiUrl="http://127.0.0.1:8000"
        />
      )}
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
