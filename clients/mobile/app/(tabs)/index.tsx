import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text } from "react-native";
import { PantallaVacia } from "../../components/PantallaVacia";
import { colors, fonts, fontSizes, radii, spacing } from "../../theme/design-system";

export default function BusquedaDeArticulos() {
  const router = useRouter();

  return (
    <PantallaVacia title="Búsqueda de artículos">
      <Pressable
        accessibilityRole="button"
        style={({ pressed }) => [styles.button, pressed && styles.pressed]}
        onPress={() =>
          router.push({
            pathname: "/articulo/[id]",
            // Identificador de navegación; no representa un artículo del catálogo.
            params: { id: "prueba" },
          })
        }
      >
        <Text style={styles.buttonLabel}>Probar detalle de artículo</Text>
      </Pressable>
    </PantallaVacia>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.primary,
    borderRadius: radii.button,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    minHeight: 48,
    maxWidth: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  pressed: { opacity: 0.8 },
  buttonLabel: {
    fontFamily: fonts.semibold,
    fontSize: fontSizes.body,
    lineHeight: 20,
    color: colors.text,
    textAlign: "center",
  },
});