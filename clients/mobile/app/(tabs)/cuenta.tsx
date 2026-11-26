import { useState } from "react";
import { useRouter } from "expo-router";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { EstadoDominio } from "../../components/EstadoDominio";
import { useSesion } from "../../session/SesionProvider";
import { colors, fonts } from "../../theme/design-system";
export default function Cuenta() {
  const sesion = useSesion();
  const router = useRouter();
  const [conexion, setConexion] = useState(false);
  return <ScrollView contentContainerStyle={s.contenido}>
    <View style={s.fila}><Text accessibilityRole="header" style={s.titulo}>Mi cuenta</Text><Pressable style={s.buscar} accessibilityRole="button" onPress={() => router.push('/')}><Ionicons name="search-outline" size={13} color="white" /><Text style={s.buscarTexto}>Buscar artículos</Text></Pressable></View>
    {sesion.estado === 'cargando' ? <ActivityIndicator color={colors.primary} /> : sesion.cuenta ? <>
      <View style={[s.tarjeta, s.perfil]}><View style={s.avatar}><Text style={s.inicial}>{sesion.cuenta.correo.charAt(0).toUpperCase()}</Text></View><Text selectable style={s.correo}>{sesion.cuenta.correo}</Text></View>
      <Pressable style={[s.tarjeta, s.canastas]} accessibilityRole="button" onPress={() => router.push('/canasta')}><View style={{ flex: 1 }}><Text style={s.canastasTitulo}>Mis canastas</Text><Text style={s.canastasTexto}>Tus artículos, guardados en tu cuenta</Text></View><Ionicons name="basket-outline" size={24} color="white" /></Pressable>
    </> : <View style={s.tarjeta}><View style={s.filaInvitado}><View style={s.avatar}><Ionicons name="person-outline" size={23} color="white" /></View><Text style={s.etiqueta}>Guarda tus canastas</Text></View><Text style={s.texto}>Explora sin cuenta o regístrate para guardar tus canastas.</Text><BotonAcceso titulo="Iniciar sesión o crear cuenta" onPress={() => router.push('/acceso')} />{sesion.estado === 'error' && <BotonAcceso titulo="Reintentar sesión" secundario onPress={() => { void sesion.reintentar(); }} />}</View>}
    {!!sesion.mensaje && <Text accessibilityRole="alert" style={s.texto}>{sesion.mensaje}</Text>}
    <View style={s.tarjeta}><Text style={s.etiqueta}>Sobre nosotros</Text><Text style={s.texto}>CanastaMX procesa y analiza los datos abiertos de PROFECO para darte transparencia en los precios. No somos PROFECO: somos un proyecto académico independiente.</Text></View>
    <Pressable style={s.conexion} accessibilityRole="button" accessibilityState={{ expanded: conexion }} onPress={() => setConexion(v => !v)}><Text style={s.texto}>Estado de conexión</Text><Ionicons name={conexion ? 'chevron-up' : 'chevron-down'} size={16} color={colors.muted} /></Pressable>
    {conexion && <EstadoDominio />}
    {sesion.cuenta && <Pressable style={s.salir} accessibilityRole="button" onPress={() => { void sesion.salir(); }}><Ionicons name="log-out-outline" size={18} color={colors.button} /><Text style={s.salirTexto}>Cerrar sesión</Text></Pressable>}
  </ScrollView>;
}
const s = StyleSheet.create({
  contenido: { padding: 16, gap: 12, paddingBottom: 32 }, fila: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 4 }, filaInvitado: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 12 }, titulo: { fontFamily: fonts.semibold, fontSize: 21, color: colors.text },
  buscar: { flexDirection: 'row', gap: 4, paddingHorizontal: 12, minHeight: 44, backgroundColor: colors.button, borderRadius: 22, alignItems: 'center' }, buscarTexto: { color: 'white', fontFamily: fonts.semibold, fontSize: 11 },
  tarjeta: { backgroundColor: 'white', borderRadius: 14, padding: 16, gap: 10, borderWidth: 1, borderColor: colors.border }, perfil: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 18 },
  avatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center' }, inicial: { color: 'white', fontFamily: fonts.semibold, fontSize: 19 }, correo: { fontFamily: fonts.semibold, fontSize: 13, flex: 1, color: colors.text },
  canastas: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12, backgroundColor: colors.button, borderColor: colors.button }, canastasTitulo: { color: 'white', fontFamily: fonts.semibold, fontSize: 14 }, canastasTexto: { color: 'white', fontFamily: fonts.regular, fontSize: 11, marginTop: 3 },
  etiqueta: { fontFamily: fonts.semibold, color: colors.text, fontSize: 13 }, texto: { fontFamily: fonts.regular, color: colors.muted, fontSize: 12, lineHeight: 19 }, conexion: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 12, minHeight: 44 },
  salir: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, minHeight: 44 }, salirTexto: { fontFamily: fonts.semibold, color: colors.button, fontSize: 13 },
});
