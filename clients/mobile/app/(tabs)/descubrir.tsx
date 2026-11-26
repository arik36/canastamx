import { useRouter } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { colors, fonts } from "../../theme/design-system";
export default function Descubrir() {
  const router = useRouter();
  return <ScrollView contentContainerStyle={s.contenido}>
    <View style={s.tarjeta}>
      <View style={s.icono}><Ionicons name="grid-outline" size={32} color={colors.button} /></View>
      <Text accessibilityRole="header" style={s.titulo}>Descubrir</Text>
      <Text style={s.texto}>No está disponible en esta versión.</Text>
      <Text style={s.texto}>Puedes buscar artículos, comparar precios y armar tus canastas desde Inicio.</Text>
      <BotonAcceso titulo="Explorar artículos" onPress={() => router.push("/")} />
    </View>
  </ScrollView>;
}
const s = StyleSheet.create({
  contenido: { flexGrow: 1, justifyContent: "center", padding: 16, backgroundColor: colors.background },
  tarjeta: { backgroundColor: colors.surface, borderRadius: 20, padding: 20, gap: 16, borderWidth: 1, borderColor: colors.border },
  icono: { width: 64, height: 64, borderRadius: 20, backgroundColor: '#EFFBFA', alignItems: 'center', justifyContent: 'center' },
  titulo: { fontFamily: fonts.semibold, fontSize: 22, color: colors.text },
  texto: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 22, color: colors.muted },
});
