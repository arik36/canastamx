import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text } from "react-native";
import { colors, fonts, fontSizes, radii, spacing } from "../theme/design-system";

export function AccesoAlertas({ campana = false }: { campana?: boolean }) {
  const router = useRouter();

  return (
    <Pressable
      onPress={() => router.push("/alertas")}
      accessibilityRole="button"
      accessibilityLabel="Mis alertas"
      style={({ pressed }) => [
        styles.button,
        campana && styles.campana,
        pressed && styles.pressed,
      ]}
    >
      <Text style={styles.label}>{campana ? "🔔" : "Mis alertas"}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.primary,
    borderRadius: radii.button,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    minHeight: 48,
    minWidth: 48,
    justifyContent: "center",
    alignItems: "center",
  },
  campana: { marginRight: spacing.md },
  label: { fontFamily: fonts.semibold, fontSize: fontSizes.body, color: colors.text },
  pressed: { opacity: 0.8 },
});
