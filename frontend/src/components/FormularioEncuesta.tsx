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

export const FormularioEncuesta: React.FC<{
  cursoCodigo: string;
  tokenAnonimo: string;
  firmaToken: string;
  apiUrl?: string;
}> = ({ cursoCodigo, tokenAnonimo, firmaToken, apiUrl = 'http://localhost:8000' }) => {
  const inicioRef = useRef<number>(Date.now());
  const [respuestas, setRespuestas] = useState<Record<string, number>>({});
  const [estadoEnvio, setEstadoEnvio] = useState<'idle' | 'enviando' | 'exito' | 'error'>('idle');
  const [mensaje, setMensaje] = useState<string>('');

  const seleccionarValor = (codigo: string, valor: number) => {
    setRespuestas((prev) => ({ ...prev, [codigo]: valor }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (Object.keys(respuestas).length < ITEMS_INSTRUMENTO_V02.length) {
      setMensaje('Por favor responde los 21 ítems antes de enviar.');
      return;
    }

    const duracionSeg = Math.max(1, Math.round((Date.now() - inicioRef.current) / 1000));
    setEstadoEnvio('enviando');

    try {
      const res = await fetch(`${apiUrl}/api/v1/encuestas/enviar`, {
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
      setMensaje('Tu valoración anónima ha sido registrada exitosamente.');
    } catch (error: any) {
      setEstadoEnvio('error');
      setMensaje(error.message);
    }
  };

  return (
    <main className="max-w-3xl mx-auto p-6 bg-white rounded-xl shadow-sm border border-slate-200">
      <header className="mb-6 border-b pb-4">
        <h1 className="text-2xl font-bold text-slate-900">
          Valoración Docente — Instrumento v0.2 ({cursoCodigo})
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          Tu identidad está protegida mediante firma ciega (RFC 9474). Las respuestas nunca comparten base de datos con el registro de matrícula.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6" aria-label="Formulario de valoración docente v0.2">
        {ITEMS_INSTRUMENTO_V02.map((item, idx) => {
          const opciones = item.opciones || ESCALA_FRECUENCIA;
          return (
            <fieldset
              key={item.codigo}
              className="p-4 rounded-lg bg-slate-50 border border-slate-200"
            >
              <legend className="font-medium text-slate-800 mb-3">
                <span className="text-indigo-700 font-semibold mr-2">{idx + 1}.</span>
                {item.enunciado}
              </legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {opciones.map((op) => {
                  const seleccionado = respuestas[item.codigo] === op.valor;
                  return (
                    <label
                      key={op.valor}
                      className={`flex items-center gap-2 p-2.5 rounded border cursor-pointer text-sm transition ${
                        seleccionado
                          ? 'bg-indigo-50 border-indigo-600 text-indigo-900 font-medium'
                          : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      <input
                        type="radio"
                        name={item.codigo}
                        value={op.valor}
                        checked={seleccionado}
                        onChange={() => seleccionarValor(item.codigo, op.valor)}
                        className="sr-only"
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
            className={`p-4 rounded-lg text-sm font-medium ${
              estadoEnvio === 'error'
                ? 'bg-red-50 text-red-800 border border-red-200'
                : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
            }`}
          >
            {mensaje}
          </div>
        )}

        <button
          type="submit"
          disabled={estadoEnvio === 'enviando' || estadoEnvio === 'exito'}
          className="w-full py-3 px-6 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white font-semibold rounded-lg shadow transition"
        >
          {estadoEnvio === 'enviando' ? 'Enviando de forma anónima...' : 'Enviar valoración anónima'}
        </button>
      </form>
    </main>
  );
};
