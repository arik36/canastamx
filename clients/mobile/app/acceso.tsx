import { useRef, useState } from "react";
import { Redirect, useRouter } from "expo-router";
import { ActivityIndicator, ImageBackground, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { StatusBar } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { BotonAcceso } from "../components/ControlesAcceso";
import { registrarCuenta, validarRegistro } from "../api/sesion";
import { useSesion } from "../session/SesionProvider";
import { colors, fonts, fontSizes, radii, spacing } from "../theme/design-system";

export default function Acceso() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const sesion = useSesion();
  const [modo, setModo] = useState<"portada" | "entrar" | "registro">("portada");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [visible, setVisible] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [registrando, setRegistrando] = useState(false);
  const bloqueo = useRef(false);
  const cargando = registrando || sesion.estado === "cargando";
  function cambiar(nuevo: typeof modo) {
    if (bloqueo.current || cargando) return;
    setModo(nuevo); setMensaje(""); setContrasena(""); setConfirmacion(""); setVisible(false);
  }
  async function enviar() {
    if (bloqueo.current || cargando) return;
    const error = modo === "registro" ? validarRegistro(correo, contrasena, confirmacion)
      : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(correo.trim()) || !contrasena ? "Escribe un correo válido y tu contraseña." : "";
    if (error) { setMensaje(error); return; }
    bloqueo.current = true; setMensaje("");
    const clave = contrasena;
    setContrasena(""); setConfirmacion("");
    try {
      if (modo === "registro") {
        setRegistrando(true);
        await registrarCuenta(correo, clave);
        setModo("entrar"); setVisible(false);
        setMensaje("Cuenta creada. Inicia sesión con tu correo y contraseña.");
      } else if (await sesion.entrar(correo, clave)) router.replace("/(tabs)/cuenta");
    } catch (e) {
      setMensaje((e instanceof Error ? e.message : "No pudimos crear tu cuenta.")
        + (e instanceof Error && /conexión|8 segundos/.test(e.message) ? " Si la cuenta alcanzó a crearse, puedes intentar iniciar sesión." : ""));
    } finally { bloqueo.current = false; setRegistrando(false); }
  }
  if (sesion.estado === "conSesion") return <Redirect href="/(tabs)/cuenta" />;
  return <ImageBackground source={require("../assets/hero-v2.png")} style={s.fondo}>
    <StatusBar style="light" />
    <View style={s.sombra} />
    <SafeAreaView style={s.fondo} edges={["top", "left", "right"]}>
      <KeyboardAvoidingView style={s.fondo} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView contentContainerStyle={s.contenido} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag">
          <View style={s.marca}><View style={s.logoIcono}><Ionicons name="basket-outline" size={25} color="white" /></View><View style={{ flex: 1 }}><Text style={s.logo}>Canasta<Text style={{ color: colors.primary }}>MX</Text></Text><Text style={s.fuente}>Fuente: datos abiertos de PROFECO{`\n`}Quién es Quién en los Precios</Text></View></View>
          <View style={[s.hero, modo !== "portada" && { minHeight: 48, paddingVertical: 16 }]}>{modo === "portada" && <Text style={s.lema}>Transparencia en cada precio. Poder en cada decisión de compra.</Text>}</View>
          <View style={[s.tarjeta, { paddingBottom: 22 + insets.bottom }]}>
            {modo === "portada" ? <>
              <Pressable accessibilityRole="button" disabled={cargando} onPress={() => router.replace("/(tabs)")} style={s.explorar}><Text style={s.explorarTexto}>Explorar artículos</Text></Pressable>
              <Pressable accessibilityRole="button" disabled={cargando} onPress={() => cambiar("entrar")} style={s.enlace}><Text style={s.enlaceTexto}>Iniciar sesión</Text></Pressable>
              <Pressable accessibilityRole="button" disabled={cargando} onPress={() => cambiar("registro")} style={s.crearEnlace}><Text style={s.registroTexto}>¿Aún no tienes cuenta? <Text style={s.enlaceTexto}>Regístrate</Text></Text></Pressable>
            </> : <>
              <View style={s.cabeceraFormulario}><Text accessibilityRole="header" style={[s.titulo, { flex: 1 }]}>{modo === "registro" ? "Crear cuenta" : "Iniciar sesión"}</Text><Pressable accessibilityRole="button" accessibilityLabel="Volver a la portada" disabled={cargando} onPress={() => cambiar("portada")} style={s.volver}><Ionicons name="arrow-back" size={16} color={colors.button} /><Text style={s.enlaceTexto}>Volver</Text></Pressable></View>
              <Text style={s.texto}>{modo === "registro" ? "Guarda tus canastas y consulta tus compras desde tu cuenta." : "Qué gusto tenerte de vuelta."}</Text>
              <Text style={s.etiqueta}>Correo electrónico</Text>
              <TextInput accessibilityLabel="Correo electrónico" value={correo} onChangeText={setCorreo} keyboardType="email-address"
                autoCapitalize="none" autoCorrect={false} autoComplete="email" textContentType="emailAddress" editable={!cargando}
                style={s.campo} placeholder="tu@correo.com" placeholderTextColor={colors.muted} />
              <Text style={s.etiqueta}>Contraseña</Text>
              <View style={s.clave}><TextInput accessibilityLabel="Contraseña" value={contrasena} onChangeText={setContrasena}
                secureTextEntry={!visible} autoCapitalize="none" autoCorrect={false} autoComplete="off" textContentType="none"
                editable={!cargando} style={[s.campo, s.entradaClave]} placeholder="Tu contraseña" placeholderTextColor={colors.muted}
                returnKeyType="go" onSubmitEditing={() => { if (modo === "entrar") void enviar(); }} />
                <Pressable accessibilityRole="button" accessibilityLabel={visible ? "Ocultar contraseña" : "Mostrar contraseña"} disabled={cargando}
                  onPress={() => setVisible(v => !v)} style={s.ojo}><Ionicons name={visible ? "eye-off-outline" : "eye-outline"} size={22} color={colors.button} /></Pressable></View>
              {modo === "registro" && <>
                <Text style={s.texto}>Entre 8 y 72 caracteres, al menos una mayúscula y un número.</Text>
                <Text style={s.etiqueta}>Confirmar contraseña</Text>
                <TextInput accessibilityLabel="Confirmar contraseña" value={confirmacion} onChangeText={setConfirmacion} secureTextEntry={!visible}
                  autoCapitalize="none" autoCorrect={false} autoComplete="off" textContentType="none" editable={!cargando}
                  style={s.campo} returnKeyType="go" onSubmitEditing={() => { void enviar(); }} />
              </>}
              {(mensaje || (modo === "entrar" && sesion.mensaje)) && <Text accessibilityRole="alert" accessibilityLiveRegion="polite" style={s.texto}>{mensaje || sesion.mensaje}</Text>}
              {cargando && <ActivityIndicator accessibilityLabel="Conectando" color={colors.button} />}
              <BotonAcceso titulo={cargando ? "Conectando…" : modo === "registro" ? "Crear cuenta" : "Iniciar sesión"} disabled={cargando} onPress={() => { void enviar(); }} />
              <BotonAcceso titulo={modo === "registro" ? "Ya tengo cuenta" : "Crear una cuenta"} secundario disabled={cargando} onPress={() => cambiar(modo === "registro" ? "entrar" : "registro")} />
              <BotonAcceso titulo="Explorar sin cuenta" secundario disabled={cargando} onPress={() => router.replace("/(tabs)")} />
            </>}
            <Text style={s.pie}>Explora sin cuenta o guarda tus canastas al iniciar sesión.{`\n`}No somos PROFECO.</Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  </ImageBackground>;
}
const s = StyleSheet.create({
  fondo: { flex: 1 }, sombra: { ...StyleSheet.absoluteFillObject, backgroundColor: "rgba(0,0,0,0.16)" },
  contenido: { flexGrow: 1, justifyContent: "space-between" },
  marca: { flexDirection: "row", alignItems: "center", gap: 12, padding: 24, paddingTop: 16 },
  logoIcono: { width: 44, height: 44, borderRadius: 14, backgroundColor: colors.primary, justifyContent: "center", alignItems: "center" },
  logo: { color: "white", fontFamily: fonts.semibold, fontSize: 23, textShadowColor: 'rgba(0,0,0,0.5)', textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 5 },
  fuente: { color: "#FFFFFF", fontFamily: fonts.regular, fontSize: 10, lineHeight: 14, marginTop: 4 },
  hero: { flex: 1, justifyContent: "flex-end", minHeight: 140, padding: 24, paddingBottom: 28 },
  lema: { color: "white", fontFamily: fonts.semibold, fontSize: 26, lineHeight: 33, maxWidth: 335, textShadowColor: 'rgba(0,0,0,0.6)', textShadowOffset: { width: 0, height: 2 }, textShadowRadius: 8 },
  credito: { color: "white", fontFamily: fonts.regular, fontSize: 11 },
  tarjeta: { width: "100%", padding: 24, gap: 12, backgroundColor: colors.surface, borderTopLeftRadius: 26, borderTopRightRadius: 26 },
  explorar: { minHeight: 54, borderRadius: 15, backgroundColor: "#00A859", justifyContent: "center", alignItems: "center", boxShadow: "0px 5px 12px rgba(0,168,89,0.28)" },
  explorarTexto: { fontFamily: fonts.semibold, color: "white", fontSize: 15 },
  enlace: { minHeight: 44, borderRadius: 12, backgroundColor: colors.background, justifyContent: "center", alignItems: "center" }, enlaceTexto: { color: colors.button, fontFamily: fonts.semibold, fontSize: 13 },
  cabeceraFormulario: { flexDirection: "row", alignItems: "center", gap: 8 }, volver: { minHeight: 44, paddingHorizontal: 4, flexDirection: "row", alignItems: "center", gap: 4 },
  crearEnlace: { minHeight: 44, alignItems: "center", justifyContent: "center" }, registroTexto: { fontFamily: fonts.regular, fontSize: 12, color: colors.muted, textAlign: 'center' },
  titulo: { color: colors.text, fontFamily: fonts.semibold, fontSize: fontSizes.title },
  texto: { color: colors.muted, fontFamily: fonts.regular, fontSize: fontSizes.body, lineHeight: 21 },
  etiqueta: { color: colors.text, fontFamily: fonts.semibold, fontSize: fontSizes.body },
  campo: { minHeight: 50, borderWidth: 1, borderColor: colors.border, borderRadius: radii.button, padding: spacing.md, color: colors.text, fontFamily: fonts.regular, fontSize: 16, backgroundColor: colors.background },
  clave: { flexDirection: "row", alignItems: "center" }, entradaClave: { flex: 1, paddingRight: 52 },
  ojo: { position: "absolute", right: 0, width: 48, height: 50, justifyContent: "center", alignItems: "center" },
  pie: { color: colors.muted, fontFamily: fonts.regular, fontSize: 11, textAlign: "center" },
});
