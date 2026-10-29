import { useState } from "react";
import { Redirect, useRouter } from "expo-router";
import { ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { BotonAcceso } from "../components/ControlesAcceso";
import { useSesion } from "../session/SesionProvider";
import { colors, fonts, fontSizes, radii, spacing } from "../theme/design-system";

export default function Acceso() {
  const router = useRouter();
  const sesion = useSesion();
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [validacion, setValidacion] = useState("");
  const cargando = sesion.estado === "cargando";
  async function entrar() {
    if (cargando) return;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo.trim()) || !contrasena) {
      setValidacion("Escribe un correo válido y tu contraseña."); return;
    }
    setValidacion("");
    const clave = contrasena;
    setContrasena("");
    if (await sesion.entrar(correo, clave)) router.replace("/(tabs)/cuenta");
  }
  // La ruta puede restaurarse al recargar Expo; una sesión válida abre Cuenta.
  if (sesion.estado === "conSesion") return <Redirect href="/(tabs)/cuenta" />;
  return <SafeAreaView style={styles.fondo} edges={["bottom", "left", "right"]}>
    <KeyboardAvoidingView style={styles.fondo} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={styles.contenido} keyboardShouldPersistTaps="handled">
        <View style={styles.tarjeta}>
          <Text style={styles.marca}>CanastaMX</Text>
          <Text accessibilityRole="header" style={styles.titulo}>Iniciar sesión</Text>
          <Text style={styles.texto}>Entra a tu cuenta para continuar.</Text>
          <Text nativeID="correo-etiqueta" style={styles.etiqueta}>Correo electrónico</Text>
          <TextInput accessibilityLabel="Correo electrónico" accessibilityLabelledBy="correo-etiqueta" value={correo}
            onChangeText={setCorreo} keyboardType="email-address" autoCapitalize="none" autoCorrect={false}
            autoComplete="email" textContentType="emailAddress" editable={!cargando} style={styles.campo} placeholder="tu@correo.com" placeholderTextColor={colors.muted} />
          <Text style={styles.etiqueta}>Contraseña</Text>
          <TextInput accessibilityLabel="Contraseña" value={contrasena} onChangeText={setContrasena} secureTextEntry
            autoCapitalize="none" autoCorrect={false} autoComplete="off" textContentType="none" editable={!cargando}
            style={styles.campo} placeholder="Tu contraseña" placeholderTextColor={colors.muted} returnKeyType="go" onSubmitEditing={() => { void entrar(); }} />
          {(validacion || sesion.mensaje) ? <Text accessibilityRole="alert" accessibilityLiveRegion="polite" style={styles.mensaje}>{validacion || sesion.mensaje}</Text> : null}
          {cargando && <ActivityIndicator accessibilityLabel="Iniciando sesión" color={colors.button} />}
          <BotonAcceso titulo={cargando ? "Conectando…" : "Iniciar sesión"} disabled={cargando} onPress={() => { void entrar(); }} />
          <BotonAcceso titulo="Explorar sin cuenta" secundario disabled={cargando} onPress={() => { void sesion.salir().then(ok => { if (ok) router.replace("/(tabs)"); }); }} />
          <Text style={styles.aviso}>No somos PROFECO</Text>
          <Text style={styles.pie}>CanastaMX es un proyecto académico independiente.</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colors.background },
  contenido: { flexGrow: 1, justifyContent: "center", alignItems: "center", padding: spacing.xl },
  tarjeta: { width: "100%", maxWidth: 440, padding: spacing.xl, gap: spacing.md, backgroundColor: colors.surface, borderRadius: radii.card },
  marca: { color: colors.button, fontFamily: fonts.semibold, fontSize: fontSizes.subtitle },
  titulo: { color: colors.text, fontFamily: fonts.semibold, fontSize: fontSizes.title },
  texto: { color: colors.muted, fontFamily: fonts.regular, fontSize: fontSizes.body },
  etiqueta: { color: colors.text, fontFamily: fonts.semibold, fontSize: fontSizes.body },
  campo: { minHeight: 48, borderWidth: 1, borderColor: colors.border, borderRadius: radii.button, padding: spacing.md, color: colors.text, fontFamily: fonts.regular, fontSize: fontSizes.body, backgroundColor: colors.background },
  mensaje: { color: colors.text, fontFamily: fonts.regular, fontSize: fontSizes.body, lineHeight: 20 },
  aviso: { color: colors.text, fontFamily: fonts.semibold, fontSize: fontSizes.body, textAlign: "center", marginTop: spacing.sm },
  pie: { color: colors.muted, fontFamily: fonts.regular, fontSize: fontSizes.metadata, textAlign: "center" },
});
