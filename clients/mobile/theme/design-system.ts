// Fuente: docs/entregas/diseño.md (sistema de diseño de D).
export const colors = {
  primary: "#23BBB7",
  background: "#F0EADF",
  text: "#2F2F2F",
  success: "#00A859",
} as const;

// Rojo se reserva para fallos; naranja, para anomalías de mercado.
// La especificación aún no define sus códigos y estas pantallas no los usan.
export const fonts = {
  regular: "Inter_400Regular",
  semibold: "Inter_600SemiBold",
} as const;

export const fontSizes = {
  title: 24,
  subtitle: 18,
  body: 14,
  metadata: 11,
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
} as const;

export const radii = {
  button: 12,
  card: 16,
  modal: 24,
} as const;