import React from 'react';
import Plot from 'react-plotly.js';

interface DimensionStats {
  mediana_ponderada: number | null;
  media_cruda_secundaria: number | null;
  n_respuestas_dim: number;
  frecuencias_1_a_5: Record<string, number>;
  valores_boxplot: number[];
}

export interface DatosDashboardCurso {
  curso_codigo: string;
  semestre: string;
  publicable: boolean;
  n_total: number;
  n_validas: number;
  porcentaje_aislados?: number;
  mensaje?: string;
  dimensiones?: Record<string, DimensionStats>;
}

export const DashboardDocente: React.FC<{ datos: DatosDashboardCurso }> = ({ datos }) => {
  if (!datos.publicable || !datos.dimensiones) {
    return (
      <section className="max-w-3xl mx-auto p-6 bg-amber-50 border border-amber-300 rounded-xl text-amber-900">
        <h2 className="text-lg font-bold mb-2">Resultados aún no disponibles ({datos.curso_codigo})</h2>
        <p className="text-sm">
          {datos.mensaje ||
            'Por regla de anonimato (N >= 5), los resultados agregados solo se habilitan cuando existen al menos 5 encuestas válidas.'}
        </p>
      </section>
    );
  }

  const dims = Object.keys(datos.dimensiones);

  return (
    <section className="max-w-5xl mx-auto p-6 space-y-6 bg-white rounded-xl shadow-sm border border-slate-200">
      <header className="flex flex-wrap justify-between items-center border-b pb-4 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Dashboard del Docente — {datos.curso_codigo} ({datos.semestre})
          </h1>
          <p className="text-sm text-slate-600">
            Cifra principal: Mediana ponderada por calidad de respuesta (sin rankings entre docentes).
          </p>
        </div>
        <div className="flex gap-4 text-sm">
          <div className="px-3 py-2 bg-slate-100 rounded-lg">
            <span className="text-slate-500 block text-xs">N Válidas</span>
            <strong className="text-slate-900 text-base">{datos.n_validas}</strong> / {datos.n_total}
          </div>
          <div className="px-3 py-2 bg-slate-100 rounded-lg">
            <span className="text-slate-500 block text-xs">% Aislado (w = 0)</span>
            <strong className="text-slate-900 text-base">{datos.porcentaje_aislados}%</strong>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {dims.map((dim) => {
          const info = datos.dimensiones![dim];
          return (
            <div key={dim} className="p-4 rounded-lg border border-slate-200 bg-slate-50">
              <span className="text-xs font-semibold text-indigo-700 uppercase">{dim}</span>
              <div className="text-2xl font-bold text-slate-900 mt-1">
                {info.mediana_ponderada ?? 'N/A'}{' '}
                <span className="text-xs font-normal text-slate-500">mediana pond.</span>
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Media cruda (ref.): {info.media_cruda_secundaria ?? 'N/A'} (N={info.n_respuestas_dim})
              </div>
            </div>
          );
        })}
      </div>

      <div className="border border-slate-200 rounded-lg p-4">
        <h2 className="text-base font-semibold text-slate-800 mb-2">
          Distribución por Dimensión (Boxplots)
        </h2>
        <Plot
          data={dims.map((dim) => ({
            y: datos.dimensiones![dim].valores_boxplot,
            type: 'box',
            name: dim,
            boxpoints: 'outliers',
          }))}
          layout={{
            height: 360,
            margin: { t: 20, r: 20, b: 40, l: 40 },
            yaxis: { title: 'Escala (1 a 5)', range: [0.8, 5.2] },
          }}
          style={{ width: '100%' }}
          config={{ responsive: true, displayModeBar: false }}
        />
      </div>
    </section>
  );
};
