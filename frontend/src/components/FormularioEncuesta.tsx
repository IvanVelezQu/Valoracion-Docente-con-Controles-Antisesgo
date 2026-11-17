import React, { useState, useRef } from 'react';
import { ITEMS_INSTRUMENTO_V02 } from '../types/instrumento';

const ESCALA_FRECUENCIA = [
  { valor: 1, etiqueta: '1 - Nunca / Muy en desacuerdo' },
  { valor: 2, etiqueta: '2 - Rara vez' },
  { valor: 3, etiqueta: '3 - A veces' },
  { valor: 4, etiqueta: '4 - Frecuentemente' },
  { valor: 5, etiqueta: '5 - Siempre / Muy de acuerdo' },
  { valor: 0, etiqueta: '0 - No aplica' },
];

const ETIQUETA_FAMILIA: Record<string, string> = {
  AR: 'Autorreflexión del Estudiante',
  SEP: 'Contexto de la Asignatura',
  DIM: 'Valoración del Desempeño Docente',
  REF: 'Verificación de Criterios del Curso',
  INV: 'Control de Consistencia',
};

export const FormularioEncuesta: React.FC<{
  cursoCodigo: string;
  tokenAnonimo: string;
  firmaToken: string;
  apiUrl?: string;
}> = ({ cursoCodigo, tokenAnonimo, firmaToken, apiUrl = 'http://127.0.0.1:8000' }) => {
  const inicioRef = useRef<number>(Date.now());
  const [respuestas, setRespuestas] = useState<Record<string, number>>({});
  const [estadoEnvio, setEstadoEnvio] = useState<'idle' | 'enviando' | 'exito' | 'error'>('idle');
  const [mensaje, setMensaje] = useState<string>('');

  const respondidas = Object.keys(respuestas).length;
  const progreso = Math.round((respondidas / ITEMS_INSTRUMENTO_V02.length) * 100);

  const seleccionarValor = (codigo: string, valor: number) => {
    setRespuestas((prev) => ({ ...prev, [codigo]: valor }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (respondidas < ITEMS_INSTRUMENTO_V02.length) {
      setEstadoEnvio('error');
      setMensaje('Por favor completa los 21 ítems antes de enviar (faltan ' + (ITEMS_INSTRUMENTO_V02.length - respondidas) + ').');
      return;
    }

    const duracionSeg = Math.max(1, Math.round((Date.now() - inicioRef.current) / 1000));
    setEstadoEnvio('enviando');

    try {
      const res = await fetch(apiUrl + '/api/v1/encuestas/enviar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          curso_codigo: cursoCodigo,
          semestre: '2026-2',
          token_anonimo: tokenAnonimo,
          firma_token: firmaToken,
          duracion_seg: duracionSeg,
          ...respuestas,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al registrar la encuesta');
      }

      setEstadoEnvio('exito');
      setMensaje('Tu valoración anónima fue procesada y firmada correctamente.');
    } catch (error: any) {
      setEstadoEnvio('error');
      setMensaje(error.message);
    }
  };

  return (
    <main className="max-w-5xl mx-auto my-8 px-4">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-udea-primary inline-block border-b-4 border-udea-primary pb-1">
          Instrumento de Valoración Docente v0.2 — {cursoCodigo}
        </h2>
        <p className="text-sm text-slate-600 mt-2">
          Protección criptográfica mediante firma ciega RSA (RFC 9474). Tu identidad institucional nunca comparte base de datos con tus respuestas.
        </p>
      </div>

      <div className="bg-[#f4f6f4] border-l-4 border-udea-lime p-4 mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="text-sm text-udea-dark font-medium">
          Avance del cuestionario: <span className="font-bold text-udea-primary">{respondidas} de {ITEMS_INSTRUMENTO_V02.length}</span> preguntas respondidas ({progreso}%)
        </div>
        <div className="w-full sm:w-64 bg-slate-200 h-2.5 overflow-hidden">
          <div className="bg-udea-primary h-full transition-all duration-300" style={{ width: progreso + '%' }} />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5" aria-label="Formulario de valoración docente UdeA">
        {ITEMS_INSTRUMENTO_V02.map((item, idx) => {
          const opciones = item.opciones || ESCALA_FRECUENCIA;
          return (
            <fieldset
              key={item.codigo}
              className="p-5 bg-white border border-slate-200 hover:border-udea-lime transition shadow-sm"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 bg-udea-graytab text-udea-primary">
                  {ETIQUETA_FAMILIA[item.familia]}
                </span>
                <span className="text-xs text-slate-400 font-mono">{item.codigo}</span>
              </div>

              <legend className="font-medium text-slate-900 text-base mb-4">
                <span className="text-udea-primary font-bold mr-2">{idx + 1}.</span>
                {item.enunciado}
              </legend>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                {opciones.map((op) => {
                  const seleccionado = respuestas[item.codigo] === op.valor;
                  return (
                    <label
                      key={op.valor}
                      className={
                        'flex items-center gap-2.5 p-3 border cursor-pointer text-sm transition ' +
                        (seleccionado
                          ? 'bg-udea-primary border-udea-primary text-white font-medium shadow-sm'
                          : 'bg-[#f9faf9] border-slate-300 text-slate-700 hover:border-udea-lime hover:bg-white')
                      }
                    >
                      <input
                        type="radio"
                        name={item.codigo}
                        value={op.valor}
                        checked={seleccionado}
                        onChange={() => seleccionarValor(item.codigo, op.valor)}
                        className="sr-only"
                      />
                      <span
                        className={
                          'w-3.5 h-3.5 rounded-full border flex items-center justify-center ' +
                          (seleccionado ? 'border-udea-gold bg-udea-gold' : 'border-slate-400')
                        }
                      />
                      <span>{op.etiqueta}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
          );
        })}

        {mensaje && (
          <div
            role="status"
            className={
              'p-4 text-sm font-medium border-l-4 ' +
              (estadoEnvio === 'error'
                ? 'bg-red-50 text-red-900 border-red-600'
                : 'bg-emerald-50 text-udea-dark border-udea-primary')
            }
          >
            {mensaje}
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={estadoEnvio === 'enviando' || estadoEnvio === 'exito'}
            className="py-3 px-8 bg-udea-primary hover:bg-udea-dark disabled:bg-slate-400 text-white font-bold uppercase tracking-wide text-sm transition shadow"
          >
            {estadoEnvio === 'enviando' ? 'Procesando envío anónimo...' : 'Enviar Valoración Anónima'}
          </button>
        </div>
      </form>
    </main>
  );
};