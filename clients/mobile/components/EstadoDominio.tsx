import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { consultarSalud, type Salud } from "../api/health";
import { colors, fonts, fontSizes, radii, spacing } from "../theme/design-system";

type Estado =
  | { tipo: "cargando" }
  | { tipo: "respuesta"; salud: Salud }
  | { tipo: "error"; mensaje: string };

export function EstadoDominio() {
  const [estado, setEstado] = useState<Estado>({ tipo: "cargando" });
  const [consulta, setConsulta] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setEstado({ tipo: "cargando" });
    consultarSalud(controller.signal)
      .then((salud) => {
        if (!controller.signal.aborted) setEstado({ tipo: "respuesta", salud });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setEstado({
            tipo: "error",
            mensaje: error instanceof Error ? error.message : "No se pudo consultar el dominio.",
          });
        }
      });
    return () => controller.abort();
  }, [consulta]);

  const cargando = estado.tipo === "cargando";
  return (
    <View style={styles.container} accessibilityLiveRegion="polite">
      <Text accessibilityRole="header" style={styles.heading}>Servicio de dominio</Text>
      {estado.tipo === "cargando" && (
        <>
          <ActivityIndicator color={colors.text} accessibilityLabel="Consultando el dominio" />
          <Text style={styles.text}>Cargando…</Text>
        </>
      )}
      {estado.tipo === "respuesta" && (
        <>
          <Text style={styles.status}>Estado: {estado.salud.status}</Text>
          <Text style={styles.text}>Servicio: {estado.salud.service}</Text>
          <Text selectable style={styles.text}>Hora del servidor: {estado.salud.time}</Text>
        </>
      )}
      {estado.tipo === "error" && (
        <>
          <Text accessibilityRole="alert" style={styles.heading}>Error de conexión</Text>
          <Text style={styles.text}>{estado.mensaje}</Text>
        </>
      )}
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ disabled: cargando }}
        disabled={cargando}
        onPress={() => setConsulta((actual) => actual + 1)}
        style={({ pressed }) => [styles.button, (pressed || cargando) && styles.disabled]}
      >
        <Text style={styles.buttonLabel}>{estado.tipo === "error" ? "Reintentar" : "Refrescar"}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignSelf: "stretch", alignItems: "center", gap: spacing.sm },
  heading: { fontFamily: fonts.semibold, fontSize: fontSizes.subtitle, color: colors.text, textAlign: "center" },
  text: { fontFamily: fonts.regular, fontSize: fontSizes.body, color: colors.text, textAlign: "center" },
  status: { fontFamily: fonts.semibold, fontSize: fontSizes.subtitle, color: colors.success, textAlign: "center" },
  button: {
    backgroundColor: colors.primary,
    borderRadius: radii.button,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    minHeight: 48,
    justifyContent: "center",
  },
  buttonLabel: { fontFamily: fonts.semibold, fontSize: fontSizes.body, color: colors.text, textAlign: "center" },
  disabled: { opacity: 0.6 },
});
