// Navegación del recorrido (docs/producto.md, 3.2). No es dato de negocio.
export interface ScreenInfo {
  id: string;
  title: string;
}

export const SCREENS: readonly ScreenInfo[] = [
  { id: 'portada', title: 'Portada' },
  { id: 'la-regla', title: 'La regla' },
  { id: 'el-patron', title: 'El patrón' },
  { id: 'la-comparacion', title: 'La comparación' },
  { id: 'la-objecion', title: 'La objeción' },
  { id: 'mas-alla-de-las-elecciones', title: 'Más allá de las elecciones' },
  { id: 'como-leer-esto', title: 'Cómo leer esto' },
  { id: 'hacia-2027', title: 'Hacia 2027' },
  { id: 'fuentes', title: 'Fuentes' },
];

export function neighbors(id: string): {
  number: number;
  previous: ScreenInfo | undefined;
  next: ScreenInfo | undefined;
} {
  const index = SCREENS.findIndex((screen) => screen.id === id);
  return {
    number: index + 1,
    previous: SCREENS[index - 1],
    next: SCREENS[index + 1],
  };
}
