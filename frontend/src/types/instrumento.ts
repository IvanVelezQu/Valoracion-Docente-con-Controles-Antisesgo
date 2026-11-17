export type FamiliaItem = 'AR' | 'SEP' | 'DIM' | 'REF' | 'INV';

export interface ItemInstrumentoV02 {
  codigo: string;
  familia: FamiliaItem;
  enunciado: string;
  contrastaCon?: string;
  opciones?: { valor: number; etiqueta: string }[];
}

// Orden oficial de presentación (21 ítems):
// 1. Autorreflexión (AR-01 a AR-03)
// 2. Separación (SEP-01 a SEP-03)
// 3. 8 ítems de dimensión intercalados con los 3 de referencia (REF-01 a REF-03)
// 4. 4 ítems inversos al final (al menos 6 preguntas después de su pareja)
export const ITEMS_INSTRUMENTO_V02: ItemInstrumentoV02[] = [
  {
    codigo: 'AR_01',
    familia: 'AR',
    enunciado: '¿A qué porcentaje de las clases asistió?',
    contrastaCon: 'DIM-01, DIM-05, DIM-06',
    opciones: [
      { valor: 1, etiqueta: '0–25 %' },
      { valor: 2, etiqueta: '26–50 %' },
      { valor: 3, etiqueta: '51–75 %' },
      { valor: 4, etiqueta: '76–100 %' },
    ],
  },
  {
    codigo: 'AR_02',
    familia: 'AR',
    enunciado: '¿Qué porcentaje de las lecturas o actividades previas completó?',
    contrastaCon: 'DIM-02, DIM-03',
    opciones: [
      { valor: 1, etiqueta: '0–25 %' },
      { valor: 2, etiqueta: '26–50 %' },
      { valor: 3, etiqueta: '51–75 %' },
      { valor: 4, etiqueta: '76–100 %' },
    ],
  },
  {
    codigo: 'AR_03',
    familia: 'AR',
    enunciado: '¿Cuántas veces usó asesorías o foros para resolver dudas?',
    contrastaCon: 'DIM-06',
    opciones: [
      { valor: 1, etiqueta: '0 veces' },
      { valor: 2, etiqueta: '1–2 veces' },
      { valor: 3, etiqueta: '3–5 veces' },
      { valor: 4, etiqueta: 'Más de 5 veces' },
    ],
  },
  {
    codigo: 'SEP_01',
    familia: 'SEP',
    enunciado: 'Antes de cursarla, mi interés en esta materia era…',
    contrastaCon: 'DIM-02',
    opciones: [
      { valor: 1, etiqueta: '1 - Muy bajo' },
      { valor: 2, etiqueta: '2 - Bajo' },
      { valor: 3, etiqueta: '3 - Moderado' },
      { valor: 4, etiqueta: '4 - Alto' },
      { valor: 5, etiqueta: '5 - Muy alto' },
    ],
  },
  {
    codigo: 'SEP_02',
    familia: 'SEP',
    enunciado: 'La materia es obligatoria en mi plan de estudios',
    contrastaCon: 'Todas',
    opciones: [
      { valor: 1, etiqueta: 'Sí' },
      { valor: 0, etiqueta: 'No (Electiva / Optativa)' },
    ],
  },
  {
    codigo: 'SEP_03',
    familia: 'SEP',
    enunciado: 'La nota que espero obtener en el curso se encuentra en el rango…',
    contrastaCon: 'DIM-04, DIM-08',
    opciones: [
      { valor: 1, etiqueta: '0,0 – 2,9' },
      { valor: 2, etiqueta: '3,0 – 3,4' },
      { valor: 3, etiqueta: '3,5 – 3,9' },
      { valor: 4, etiqueta: '4,0 – 4,4' },
      { valor: 5, etiqueta: '4,5 – 5,0' },
    ],
  },
  // Bloque Dimensiones intercalado con Referencia (escala 1-5 + 0 = No aplica)
  {
    codigo: 'DIM_01',
    familia: 'DIM',
    enunciado: 'El docente explicó los conceptos centrales con claridad y precisión.',
  },
  {
    codigo: 'DIM_02',
    familia: 'DIM',
    enunciado: 'Las sesiones siguieron una secuencia lógica y articulada con el programa.',
  },
  {
    codigo: 'REF_02',
    familia: 'REF',
    enunciado: 'El programa del curso publicado detallaba los criterios de evaluación.',
    contrastaCon: 'DIM-04',
  },
  {
    codigo: 'DIM_03',
    familia: 'DIM',
    enunciado: 'Las actividades y materiales propuestos facilitaron la comprensión de los temas.',
  },
  {
    codigo: 'DIM_04',
    familia: 'DIM',
    enunciado: 'Las evaluaciones fueron coherentes con los criterios y temas trabajados en clase.',
  },
  {
    codigo: 'REF_01',
    familia: 'REF',
    enunciado: 'Las actividades calificadas se devolvieron dentro del plazo establecido.',
    contrastaCon: 'DIM-05',
  },
  {
    codigo: 'DIM_05',
    familia: 'DIM',
    enunciado: 'La retroalimentación entregada permitió identificar aciertos y aspectos por mejorar.',
  },
  {
    codigo: 'DIM_06',
    familia: 'DIM',
    enunciado: 'El docente mostró disposición y acompañamiento para resolver dudas académicas.',
  },
  {
    codigo: 'REF_03',
    familia: 'REF',
    enunciado: 'Los horarios de asesoría publicados se cumplieron.',
    contrastaCon: 'DIM-06',
  },
  {
    codigo: 'DIM_07',
    familia: 'DIM',
    enunciado: 'Se promovió un ambiente de trato respetuoso y participación en el curso.',
  },
  {
    codigo: 'DIM_08',
    familia: 'DIM',
    enunciado: 'El desarrollo general del curso aportó de manera significativa a mi formación.',
  },
  // Bloque Inversos al final (cada uno al menos 6 preguntas después de su pareja DIM)
  {
    codigo: 'INV_01',
    familia: 'INV',
    enunciado: 'Con frecuencia las explicaciones me dejaron sin saber cuál era la idea principal.',
    contrastaCon: 'DIM-01',
  },
  {
    codigo: 'INV_02',
    familia: 'INV',
    enunciado: 'Las sesiones saltaban entre temas sin relación clara.',
    contrastaCon: 'DIM-02',
  },
  {
    codigo: 'INV_03',
    familia: 'INV',
    enunciado: 'Me enteré de cómo me iban a calificar solo después de la evaluación.',
    contrastaCon: 'DIM-04',
  },
  {
    codigo: 'INV_04',
    familia: 'INV',
    enunciado: 'La retroalimentación se limitó a la nota, sin indicar qué mejorar.',
    contrastaCon: 'DIM-05',
  },
];
