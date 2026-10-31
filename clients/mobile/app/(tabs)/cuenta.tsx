import { useRouter } from "expo-router";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { AccesoAlertas } from "../../components/AccesoAlertas";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { useSesion } from "../../session/SesionProvider";
import { colors, fonts, fontSizes, radii, spacing } from "../../theme/design-system";

export default function Cuenta() {
  const sesion = useSesion();
  const router = useRouter();
  return <SafeAreaView style={styles.fondo} edges={["bottom", "left", "right"]}>
    <ScrollView contentContainerStyle={styles.contenido}>
      <View style={styles.tarjeta}>

        {sesion.estado === "cargando" ? <><ActivityIndicator color={colors.button} /><Text style={styles.texto}>Recuperando tu sesión…</Text></> : <>
          {sesion.cuenta ? <>
            <View accessible accessibilityLabel={`Inicial ${sesion.cuenta.correo.charAt(0).toUpperCase()}`} style={styles.avatar}><Text style={styles.inicial}>{sesion.cuenta.correo.charAt(0).toUpperCase()}</Text></View>
            <Text style={styles.etiqueta}>Correo electrónico</Text>
            <Text selectable style={styles.texto}>{sesion.cuenta.correo}</Text>
            <AccesoAlertas />
            <BotonAcceso titulo="Cerrar sesión" secundario onPress={() => { void sesion.salir(); }} />
          </> : <>
            <Text style={styles.texto}>Explora sin cuenta o inicia sesión para acceder a tu perfil.</Text>
            {sesion.estado === "error" ? <>
              <BotonAcceso titulo="Reintentar" onPress={() => { void sesion.reintentar(); }} />
              <BotonAcceso titulo="Continuar sin cuenta" secundario onPress={() => { void sesion.salir(); }} />
            </> : <BotonAcceso titulo="Iniciar sesión" onPress={() => router.push("/acceso")} />}
            <AccesoAlertas />
          </>}
        </>}
        {sesion.mensaje && <Text accessibilityRole="alert" accessibilityLiveRegion="polite" style={styles.texto}>{sesion.mensaje}</Text>}
        <Text style={styles.etiqueta}>Sobre nosotros</Text>
        <Text style={styles.texto}>No somos PROFECO. CanastaMX es un proyecto académico independiente.</Text>
      </View>
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colors.background },
  contenido: { flexGrow: 1, justifyContent: "center", alignItems: "center", padding: spacing.xl },
  tarjeta: { width: "100%", maxWidth: 440, padding: spacing.xl, gap: spacing.lg, borderRadius: radii.card, backgroundColor: colors.surface },

  texto: { color: colors.text, fontFamily: fonts.regular, fontSize: fontSizes.body, lineHeight: 22 },
  etiqueta: { color: colors.text, fontFamily: fonts.semibold, fontSize: fontSizes.body },
  avatar: { width: 64, height: 64, borderRadius: 32, backgroundColor: colors.primary, alignSelf: "center", alignItems: "center", justifyContent: "center" },
  inicial: { color: colors.text, fontSize: fontSizes.title, fontFamily: fonts.semibold },
});
