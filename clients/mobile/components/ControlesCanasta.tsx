import { useState } from "react";
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useCanasta } from "../canasta/CanastaProvider";
import { BotonAcceso } from "./ControlesAcceso";
import { PanelInferior } from "./PanelInferior";
import { colors, fonts, fontSizes, radii, spacing } from "../theme/design-system";

export const cantidadValida = (texto: string) => /^\d+$/.test(texto) && Number.isSafeInteger(Number(texto)) && Number(texto) > 0;
export function SelectorCanasta({ compacto = false }: { compacto?: boolean }) {
  const c = useCanasta();
  const [abierto, setAbierto] = useState(false);
  const [nombre, setNombre] = useState("");
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [formulario, setFormulario] = useState<"lista" | "crear" | "editar">("lista");
  const bloqueada = c.ocupada || c.requiereRecarga;
  return <View style={estilos.grupo}>
    <Pressable accessibilityRole="button" accessibilityLabel="Elegir o administrar canastas" disabled={c.ocupada}
      onPress={() => { setNuevoNombre(c.actual?.nombre ?? ""); setFormulario("lista"); setNombre(""); setAbierto(true); }} style={[estilos.selector, compacto && { backgroundColor: "transparent", padding: 0, minHeight: 44 }]}>
      {!compacto && <Ionicons name="basket-outline" size={24} color={colors.button} />}
      <View style={{ flex: 1 }}>{!compacto && <Text style={estilos.meta}>Canasta de destino</Text>}<Text numberOfLines={2} style={[estilos.subtitulo, compacto && { fontSize: 14 }]}>{c.actual?.nombre ?? "Mis canastas"}</Text></View>
      <Ionicons name={compacto ? "settings-outline" : "options-outline"} size={20} color={colors.button} />
    </Pressable>
    <PanelInferior visible={abierto} titulo="Mis canastas" cerrar={() => setAbierto(false)} bloqueado={c.ocupada}>
            <Text style={estilos.meta}>Selecciona la canasta que quieres usar.</Text>
            {c.canastas.map(item => <Pressable key={item.id} accessibilityRole="radio" accessibilityState={{ checked: c.actual?.id === item.id, disabled: c.ocupada }}
              disabled={c.ocupada} onPress={() => { c.seleccionar(item.id); setNuevoNombre(item.nombre); setFormulario("lista"); }}
              style={[estilos.canastaOpcion, c.actual?.id === item.id && estilos.canastaSeleccionada]}>
              <Ionicons name="basket-outline" size={22} color={colors.button} /><View style={{ flex: 1 }}><Text style={estilos.canastaNombre}>{item.nombre}</Text><Text style={estilos.canastaMeta}>{item.lineas.length} artículos{c.actual?.id === item.id ? " · Activa" : ""}</Text></View>
              <Ionicons name={c.actual?.id === item.id ? "radio-button-on" : "radio-button-off"} size={20} color={colors.button} />
            </Pressable>)}
            {c.listaCargada && c.canastas.length === 0 && <Text style={estilos.texto}>Aún no tienes canastas. Crea una para guardar artículos.</Text>}
            {formulario !== "crear" && <BotonAcceso titulo="+ Crear nueva canasta" secundario disabled={bloqueada || !c.listaCargada} onPress={() => setFormulario("crear")} />}
            {formulario === "crear" && <>
            <Text style={estilos.subtitulo}>Nueva canasta</Text>
            <TextInput accessibilityLabel="Nombre de nueva canasta" placeholder="Ej. Súper de la quincena" placeholderTextColor={colors.muted}
              style={estilos.campo} value={nombre} onChangeText={setNombre} editable={!c.ocupada} maxLength={200} />
            <BotonAcceso titulo="Crear canasta" disabled={bloqueada || !c.listaCargada || !nombre.trim()}
              onPress={() => { void c.crear(nombre).then(ok => { if (ok) { setNombre(""); setAbierto(false); } }); }} />
            <BotonAcceso titulo="Cancelar creación" secundario disabled={c.ocupada} onPress={() => setFormulario("lista")} />
            </>}
            {c.actual && formulario === "lista" && <BotonAcceso titulo="Editar canasta activa" secundario disabled={bloqueada} onPress={() => { setNuevoNombre(c.actual!.nombre); setFormulario("editar"); }} />}
            {c.actual && formulario === "editar" && <>
              <Text style={estilos.subtitulo}>Administrar «{c.actual.nombre}»</Text>
              <TextInput accessibilityLabel="Nuevo nombre de la canasta" style={estilos.campo} value={nuevoNombre} onChangeText={setNuevoNombre} editable={!c.ocupada} maxLength={200} />
              <BotonAcceso titulo="Guardar nombre" secundario disabled={bloqueada || !nuevoNombre.trim() || nuevoNombre.trim() === c.actual.nombre}
                onPress={() => { void c.renombrar(nuevoNombre).then(ok => { if (ok) setAbierto(false); }); }} />
              <BotonAcceso titulo="Eliminar canasta" secundario disabled={bloqueada} onPress={() => Alert.alert("Eliminar canasta", `Se eliminará «${c.actual!.nombre}» y sus artículos de tu cuenta.`, [
                { text: "Cancelar", style: "cancel" }, { text: "Eliminar", style: "destructive", onPress: () => { void c.borrar().then(ok => { if (ok) setAbierto(false); }); } },
              ])} />
              <BotonAcceso titulo="Cancelar edición" secundario disabled={c.ocupada} onPress={() => setFormulario("lista")} />
            </>}
            {!!c.error && <Text accessibilityRole="alert" style={estilos.texto}>{c.error}</Text>}
            <BotonAcceso titulo="Actualizar canastas" secundario disabled={c.ocupada} onPress={() => { void c.recargar(); }} />
            <BotonAcceso titulo="Listo" secundario disabled={c.ocupada} onPress={() => setAbierto(false)} />
    </PanelInferior>
    {c.ocupada && <Text accessibilityLiveRegion="polite" style={estilos.meta}>Guardando o recuperando tu canasta…</Text>}
    {!!c.error && <Text accessibilityRole="alert" style={estilos.texto}>{c.error}</Text>}
    {c.requiereRecarga && <BotonAcceso titulo="Recuperar estado de la canasta" secundario disabled={c.ocupada} onPress={() => { void c.recargar(); }} />}
  </View>;
}
export const estilos = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colors.background },
  contenido: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xxl },
  grupo: { gap: spacing.md },
  tarjeta: { backgroundColor: colors.surface, borderRadius: radii.card, padding: spacing.lg, gap: spacing.sm, borderWidth: 1, borderColor: colors.border },
  titulo: { fontFamily: fonts.semibold, fontSize: fontSizes.title, color: colors.text },
  subtitulo: { fontFamily: fonts.semibold, fontSize: fontSizes.subtitle, color: colors.text },
  texto: { fontFamily: fonts.regular, fontSize: fontSizes.body, color: colors.text, lineHeight: 21 },
  meta: { fontFamily: fonts.regular, fontSize: fontSizes.body, color: colors.muted, lineHeight: 21 },
  campo: { minHeight: 48, padding: spacing.md, borderWidth: 1, borderColor: colors.border, borderRadius: radii.button,
    backgroundColor: colors.surface, color: colors.text, fontFamily: fonts.regular, fontSize: 16 },
  selector: { flexDirection: "row", alignItems: "center", gap: 12, backgroundColor: colors.surface, padding: 16, borderRadius: 16, minHeight: 64 },
  canastaOpcion: { minHeight: 64, flexDirection: "row", alignItems: "center", gap: 10, borderWidth: 1, borderColor: colors.border, borderRadius: 12, padding: 12 },
  canastaSeleccionada: { borderColor: colors.primary, backgroundColor: "#EFFBFA" }, canastaNombre: { fontFamily: fonts.semibold, color: colors.text, fontSize: 13 }, canastaMeta: { fontFamily: fonts.regular, color: colors.muted, fontSize: 11, marginTop: 3 },
  fila: { flexDirection: "row", alignItems: "center", gap: 12, flexWrap: "wrap" },
  paso: { minHeight: 48, minWidth: 48, borderRadius: 14, backgroundColor: "#C6EBE5", alignItems: "center", justifyContent: "center" },
  resumen: { padding: 20, gap: 12, backgroundColor: colors.text, borderRadius: 20 },
  resumenTexto: { fontFamily: fonts.semibold, fontSize: 16, color: colors.surface },
});
