import { Pressable, StyleSheet, Text } from "react-native";
import { colors, fonts, fontSizes, radii, spacing } from "../theme/design-system";

export function BotonAcceso({ titulo, onPress, disabled = false, secundario = false }: { titulo: string; onPress(): void; disabled?: boolean; secundario?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress}
    style={({ pressed }) => [styles.boton, secundario && styles.secundario, (disabled || pressed) && styles.atenuado]}>
    <Text style={[styles.etiqueta, secundario && styles.etiquetaSecundaria]}>{titulo}</Text>
  </Pressable>;
}
const styles = StyleSheet.create({
  boton: { minHeight: 48, borderRadius: radii.button, padding: spacing.md, backgroundColor: colors.button, justifyContent: "center", alignItems: "center" },
  secundario: { backgroundColor: "transparent", borderWidth: 1, borderColor: colors.button },
  etiqueta: { color: colors.surface, fontFamily: fonts.semibold, fontSize: fontSizes.body, textAlign: "center" },
  etiquetaSecundaria: { color: colors.button }, atenuado: { opacity: 0.55 },
});
