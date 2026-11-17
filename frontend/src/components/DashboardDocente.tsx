import React from 'react';

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
  minimo_requerido?: number;
  porcentaje_aislados?: number;
  mensaje?: string;
  dimensiones?: Record<string, DimensionStats>;
}

const NOMBRES_DIMENSIONES: Record<string, string> = {
  DIM_01: 'Claridad explicativa',
  DIM_02: 'Secuencia articulada',
  DIM_03: 'Materiales y actividades',
  DIM_04: 'Coherencia evaluativa',
  DIM_05: 'Retroalimentación oportuna',
  DIM_06: 'Disposición en asesorías',
  DIM_07: 'Trato respetuoso',
  DIM_08: 'Aporte formativo global',
};

function calcularCuartiles(valores: number[]) {
  if (!valores || valores.length === 0) return { min: 1, q1: 3, med: 4, q3: 5, max: 5 };
  const s = [...valores].sort((a, b) => a - b);
  const pos = (p: number) => {
    const idx = p * (s.length - 1);
    const lo = Math.floor(idx);
    const hi = Math.ceil(idx);
    return s[lo] + (s[hi] - s[lo]) * (idx - lo);
  };
  return {
    min: s[0],
    q1: pos(0.25),
    med: pos(0.5),
    q3: pos(0.75),
    max: s[s.length - 1],
  };
}

export const DashboardDocente: React.FC<{
  datos: DatosDashboardCurso;
  onSembrarDatos?: () => void;
  sembrando?: boolean;
}> = ({ datos, onSembrarDatos, sembrando }) => {
  if (!datos.publicable || !datos.dimensiones) {
    return (
      <section className="max-w-5xl mx-auto my-8 p-6 bg-[#f4f6f4] border-l-4 border-udea-gold text-slate-800 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-udea-primary mb-1">
              Resultados protegidos por umbral de anonimato ({datos.curso_codigo})
            </h2>
            <p className="text-sm text-slate-700">
              {datos.mensaje || 'Se requieren al menos 5 respuestas válidas (N >= 5) para publicar resultados.'}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Encuestas recibidas: <strong>{datos.n_total}</strong> · Válidas actuales: <strong>{datos.n_validas}</strong> de 5 requeridas.
            </p>
          </div>
          {onSembrarDatos && (
            <button
              onClick={onSembrarDatos}
              disabled={sembrando}
              className="px-5 py-2.5 bg-udea-primary hover:bg-udea-dark disabled:bg-slate-400 text-white font-bold text-xs uppercase tracking-wider shadow transition"
            >
              {sembrando ? 'Cargando encuestas...' : 'Simular 6 Encuestas Demo (5 honestas + 1 Halo)'}
            </button>
          )}
        </div>
      </section>
    );
  }

  const dims = Object.keys(datos.dimensiones);

  return (
    <section className="max-w-5xl mx-auto my-8 px-4 space-y-8">
      <div className="flex flex-wrap justify-between items-end gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-2xl font-bold text-udea-primary inline-block border-b-4 border-udea-primary pb-1">
            Reporte Consolidado de Valoración Docente
          </h2>
          <p className="text-sm text-slate-600 mt-2">
            Asignatura: <strong>{datos.curso_codigo}</strong> · Semestre <strong>{datos.semestre}</strong> · Instrumento v0.2 (Controles Antisesgo)
          </p>
        </div>

        <div className="flex gap-3 text-sm">
          <div className="px-4 py-2 bg-udea-graytab border-b-4 border-udea-primary">
            <span className="text-[11px] uppercase font-bold text-slate-500 block">Encuestas Válidas</span>
            <strong className="text-udea-primary text-lg">{datos.n_validas}</strong>{' '}
            <span className="text-xs text-slate-500">de {datos.n_total}</span>
          </div>
          <div className="px-4 py-2 bg-udea-graytab border-b-4 border-udea-lime">
            <span className="text-[11px] uppercase font-bold text-slate-500 block">% Aislado (w = 0)</span>
            <strong className="text-udea-dark text-lg">{datos.porcentaje_aislados}%</strong>
          </div>
        </div>
      </div>

      {/* Tarjetas de las 8 dimensiones */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {dims.map((dim) => {
          const info = datos.dimensiones![dim];
          return (
            <div
              key={dim}
              className="p-4 bg-white border border-slate-200 border-t-4 border-t-udea-primary shadow-sm hover:shadow transition"
            >
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-udea-primary uppercase">{dim}</span>
                <span className="text-[11px] bg-udea-graytab px-2 py-0.5 text-slate-600 font-medium">
                  N = {info.n_respuestas_dim}
                </span>
              </div>
              <p className="text-xs text-slate-600 font-medium mt-1 truncate">
                {NOMBRES_DIMENSIONES[dim] || dim}
              </p>
              <div className="text-3xl font-black text-udea-dark mt-2">
                {info.mediana_ponderada ?? 'N/A'}
                <span className="text-xs font-normal text-udea-primary ml-1.5">Mediana pond.</span>
              </div>
              <div className="text-xs text-slate-500 mt-2 pt-2 border-t border-slate-100 flex justify-between">
                <span>Media cruda (ref.):</span>
                <strong className="text-slate-700">{info.media_cruda_secundaria ?? 'N/A'}</strong>
              </div>
            </div>
          );
        })}
      </div>

      {/* Gráfico de Boxplots y Distribución de Frecuencias */}
      <div className="bg-white border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-bold text-udea-primary mb-1">
          Distribución por Dimensión — Boxplots y Frecuencias (Escala 1 a 5)
        </h3>
        <p className="text-xs text-slate-500 mb-6">
          La línea dorada indica la mediana ponderada por calidad de respuesta (w), excluyendo envíos aislados (w = 0).
        </p>

        <div className="space-y-4">
          {dims.map((dim) => {
            const info = datos.dimensiones![dim];
            const q = calcularCuartiles(info.valores_boxplot);
            const aPorcentaje = (val: number) => ((val - 1) / 4) * 100;

            return (
              <div key={dim} className="grid grid-cols-1 md:grid-cols-12 items-center gap-4 py-2 border-b border-slate-100">
                <div className="md:col-span-3">
                  <span className="text-xs font-bold text-udea-primary block">{dim}</span>
                  <span className="text-xs text-slate-600">{NOMBRES_DIMENSIONES[dim]}</span>
                </div>

                {/* Boxplot horizontal en escala 1..5 */}
                <div className="md:col-span-6 relative h-8 bg-[#f4f6f4] border border-slate-200 px-3 flex items-center">
                  <div className="relative w-full h-full flex items-center">
                    {[1, 2, 3, 4, 5].map((esc) => (
                      <div
                        key={esc}
                        style={{ left: `${aPorcentaje(esc)}%` }}
                        className="absolute top-0 bottom-0 border-l border-dashed border-slate-300 text-[9px] text-slate-400 pl-0.5"
                      >
                        {esc}
                      </div>
                    ))}
                    {/* Bigote min a max */}
                    <div
                      style={{
                        left: `${aPorcentaje(q.min)}%`,
                        width: `${Math.max(2, aPorcentaje(q.max) - aPorcentaje(q.min))}%`,
                      }}
                      className="absolute h-0.5 bg-udea-dark"
                    />
                    {/* Caja Q1 a Q3 */}
                    <div
                      style={{
                        left: `${aPorcentaje(q.q1)}%`,
                        width: `${Math.max(4, aPorcentaje(q.q3) - aPorcentaje(q.q1))}%`,
                      }}
                      className="absolute h-5 bg-udea-primary/85 border border-udea-dark rounded-sm"
                    />
                    {/* Mediana ponderada */}
                    <div
                      style={{ left: `${aPorcentaje(info.mediana_ponderada ?? q.med)}%` }}
                      className="absolute h-6 w-1.5 bg-udea-gold -ml-0.5 shadow"
                      title={`Mediana ponderada: ${info.mediana_ponderada}`}
                    />
                  </div>
                </div>

                {/* Frecuencias 1 a 5 */}
                <div className="md:col-span-3 flex justify-end gap-1.5 text-[11px]">
                  {[1, 2, 3, 4, 5].map((esc) => {
                    const count = info.frecuencias_1_a_5[String(esc)] || 0;
                    return (
                      <span
                        key={esc}
                        className={`px-1.5 py-0.5 rounded border ${
                          count > 0
                            ? 'bg-udea-primary text-white border-udea-primary font-bold'
                            : 'bg-slate-50 text-slate-400 border-slate-200'
                        }`}
                        title={`Calificación ${esc}: ${count} votos`}
                      >
                        {esc}:{count}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};