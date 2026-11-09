// Etiquetas de secretaría para el tablero. Copia de pipeline/reference/departments.toml
// (R8, ADR 0030, ADR 0053): las salidas traen solo el código. departments.test.ts verifica
// que cada código de indicators.json tenga etiqueta.
export const DEPARTMENT_LABELS: Readonly<Record<string, string>> = {
  buen_comienzo: 'Buen Comienzo',
  communications: 'Comunicaciones',
  citizen_culture: 'Cultura Ciudadana',
  disaster_management: 'Gestión del Riesgo de Desastres (DAGRD)',
  youth: 'Juventud',
  peace_and_human_rights: 'Paz y Derechos Humanos',
  women: 'Mujeres',
  economic_development: 'Desarrollo Económico',
  education: 'Educación',
  evaluation_and_control: 'Evaluación y Control',
  downtown_management: 'Gerencia del Centro',
  general: 'General',
  human_management: 'Gestión Humana y Servicio a la Ciudadanía',
  territorial_management: 'Gestión y Control Territorial',
  government: 'Gobierno',
  treasury: 'Hacienda',
  social_inclusion: 'Inclusión Social y Familia',
  infrastructure: 'Infraestructura Física',
  digital_innovation: 'Innovación Digital',
  environment: 'Medio Ambiente',
  mobility: 'Movilidad',
  participation: 'Participación Ciudadana',
  planning: 'Planeación',
  private_office: 'Privada',
  health: 'Salud',
  security: 'Seguridad y Convivencia',
  supplies_and_services: 'Suministros y Servicios',
  tourism: 'Turismo y Entretenimiento',
  unassigned: 'Sin asignar',
};

/** Etiqueta de una secretaría; si el código no está, devuelve el código. */
export const departmentLabel = (code: string): string => DEPARTMENT_LABELS[code] ?? code;
