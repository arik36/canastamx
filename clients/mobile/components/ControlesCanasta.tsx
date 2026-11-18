import { useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import { useCanasta } from "../canasta/CanastaProvider";
import { BotonAcceso } from "./ControlesAcceso";
import { colors, fonts, fontSizes, radii, spacing } from "../theme/design-system";

export const cantidadValida = (texto: string) => /^\d+$/.test(texto) && Number.isSafeInteger(Number(texto)) && Number(texto) > 0;
export function SelectorCanasta() {
  const c = useCanasta();
  const [nombre, setNombre] = useState("");
  return <View style={estilos.grupo}>
    <Text style={estilos.subtitulo}>Canasta de destino</Text>
    {c.canastas.map(item => <BotonAcceso key={item.id} titulo={`${c.actual?.id === item.id ? "Seleccionada: " : ""}${item.nombre}`}
      secundario={c.actual?.id !== item.id} disabled={c.ocupada} onPress={() => c.seleccionar(item.id)} />)}
    {c.listaCargada && c.canastas.length === 0 && <Text style={estilos.texto}>Aún no tienes canastas. Crea una para guardar artículos.</Text>}
    <TextInput accessibilityLabel="Nombre de nueva canasta" placeholder="Nombre de nueva canasta" placeholderTextColor={colors.muted}
      style={estilos.campo} value={nombre} onChangeText={setNombre} editable={!c.ocupada} maxLength={200} />
    <BotonAcceso titulo="Crear canasta" secundario disabled={c.ocupada || c.requiereRecarga || !c.listaCargada || !nombre.trim()}
      onPress={() => { void c.crear(nombre).then(ok => { if (ok) setNombre(""); }); }} />
    {c.ocupada && <Text accessibilityLiveRegion="polite" style={estilos.texto}>Consultando el dominio…</Text>}
    {!!c.error && <Text accessibilityRole="alert" style={estilos.texto}>{c.error}</Text>}
    <BotonAcceso titulo="Actualizar canastas" secundario disabled={c.ocupada} onPress={() => { void c.recargar(); }} />
  </View>;
}
export const estilos = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colors.background },
  contenido: { padding: spacing.xl, gap: spacing.lg, paddingBottom: spacing.xxl },
  grupo: { gap: spacing.md },
  tarjeta: { backgroundColor: colors.surface, borderRadius: radii.card, padding: spacing.lg, gap: spacing.sm },
  titulo: { fontFamily: fonts.semibold, fontSize: fontSizes.title, color: colors.text },
  subtitulo: { fontFamily: fonts.semibold, fontSize: fontSizes.subtitle, color: colors.text },
  texto: { fontFamily: fonts.regular, fontSize: fontSizes.body, color: colors.text, lineHeight: 21 },
  meta: { fontFamily: fonts.regular, fontSize: fontSizes.body, color: colors.muted, lineHeight: 21 },
  campo: { minHeight: 48, padding: spacing.md, borderWidth: 1, borderColor: colors.muted, borderRadius: radii.button,
    backgroundColor: colors.surface, color: colors.text, fontFamily: fonts.regular, fontSize: fontSizes.body },
});
