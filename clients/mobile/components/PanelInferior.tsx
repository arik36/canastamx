import { ReactNode } from "react";
import { Keyboard, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { colors, fonts } from "../theme/design-system";

export function PanelInferior({ visible, titulo, cerrar, bloqueado = false, alto = false, desplazable = true, children }: {
  visible: boolean; titulo: string; cerrar(): void; bloqueado?: boolean; alto?: boolean; desplazable?: boolean; children: ReactNode;
}) {
  const insets = useSafeAreaInsets();
  const cerrarSiLibre = () => { if (!bloqueado) { Keyboard.dismiss(); cerrar(); } };
  return <Modal visible={visible} transparent animationType="slide" onRequestClose={cerrarSiLibre}>
    <SafeAreaView style={s.fondo} edges={["top", "left", "right"]}>
      <KeyboardAvoidingView style={s.fondoTeclado} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <Pressable style={s.exterior} accessibilityRole="button" accessibilityLabel={`Cerrar ${titulo}`} disabled={bloqueado} onPress={cerrarSiLibre} />
        <View accessibilityViewIsModal style={[s.panel, alto && { height: "85%" }, { paddingBottom: Math.max(12, insets.bottom) }]}>
          <View style={s.tirador} />
          <View style={s.cabecera}><Text accessibilityRole="header" style={s.titulo}>{titulo}</Text><Pressable accessibilityRole="button" accessibilityLabel="Cerrar panel" disabled={bloqueado} onPress={cerrarSiLibre} style={[s.cerrar, bloqueado && { opacity: 0.4 }]}><Ionicons name="close" size={22} color={colors.muted} /></Pressable></View>
          {desplazable ? <ScrollView style={s.scroll} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" contentContainerStyle={s.contenido}>{children}</ScrollView>
            : <View style={[s.contenido, { flex: 1 }]}>{children}</View>}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  </Modal>;
}
const s = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: "rgba(15,25,25,0.42)" }, fondoTeclado: { flex: 1, justifyContent: "flex-end" }, exterior: { flex: 1 },
  panel: { maxHeight: "85%", backgroundColor: colors.surface, borderTopLeftRadius: 24, borderTopRightRadius: 24, overflow: "hidden" },
  tirador: { width: 40, height: 4, backgroundColor: colors.border, borderRadius: 4, alignSelf: "center", marginTop: 10 },
  cabecera: { paddingLeft: 20, paddingRight: 12, paddingTop: 8, paddingBottom: 8, flexDirection: "row", alignItems: "center", gap: 8 },
  titulo: { flex: 1, fontFamily: fonts.semibold, fontSize: 20, lineHeight: 27, color: colors.text }, cerrar: { minWidth: 44, minHeight: 44, alignItems: "center", justifyContent: "center" },
  scroll: { flexGrow: 0, flexShrink: 1 }, contenido: { paddingHorizontal: 20, paddingTop: 4, paddingBottom: 8, gap: 12 },
});
