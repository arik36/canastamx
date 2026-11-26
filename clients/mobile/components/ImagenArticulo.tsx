import { useState } from "react";
import { Image, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors, fonts } from "../theme/design-system";
import { clasificarImagen } from "./clasificarImagen";

const atlas = { alimentos: require("../assets/productos/alimentos-v1.png"), frescos: require("../assets/productos/frescos-v1.png"), despensa: require("../assets/productos/despensa-v1.png"), complementos: require("../assets/productos/complementos-v1.png") };
const fotos = { pechuga: require("../assets/pollo.jpg"), huevo: require("../assets/huevo.jpg"), aceite: require("../assets/aceite.jpg"), chile: require("../assets/chile.jpg"), atunAhumado: require("../assets/productos/atun-ahumado-v1.png") };
export function ImagenArticulo({ producto = "", presentacion = "", catalogo = "", grande = false, mini = false }: { producto?: string; presentacion?: string; catalogo?: string; grande?: boolean; mini?: boolean }) {
  const imagen = clasificarImagen(producto, presentacion);
  const [medida, setMedida] = useState({ ancho: 0, alto: 0 });
  const lado = Math.min(medida.ancho, medida.alto);
  return <View accessible accessibilityLabel={imagen ? `Imagen ilustrativa de ${producto}; no acredita marca ni presentación exacta` : `Sin fotografía asignada para ${producto}`} onLayout={e => { const { width, height } = e.nativeEvent.layout; setMedida(v => v.ancho === width && v.alto === height ? v : { ancho: width, alto: height }); }} style={[s.imagen, grande && s.grande, mini && s.mini]}>
    {imagen && "atlas" in imagen ? (lado > 0 && <View style={{ position: "absolute", width: lado, height: lado, left: (medida.ancho - lado) / 2, top: (medida.alto - lado) / 2, overflow: "hidden" }}><Image source={atlas[imagen.atlas]} resizeMode="stretch" style={{ position: "absolute", width: lado * 4, height: lado * 4, left: -(imagen.celda % 4) * lado, top: -Math.floor(imagen.celda / 4) * lado }} /></View>)
      : imagen && "foto" in imagen ? <Image source={fotos[imagen.foto]} style={[StyleSheet.absoluteFillObject, { width: "100%", height: "100%" }]} resizeMode="cover" />
      : <View style={s.respaldo}><Ionicons name="basket-outline" size={mini ? 24 : 40} color={colors.button} />{!mini && <><Text numberOfLines={3} style={s.nombre}>{producto || catalogo || "Artículo"}</Text><Text style={s.aviso}>Sin fotografía asignada</Text></>}</View>}
  </View>;
}
const s = StyleSheet.create({
  imagen: { aspectRatio: 1, width: "100%", backgroundColor: "#E8E3D4", overflow: "hidden", alignItems: "center", justifyContent: "center" },
  grande: { aspectRatio: 1.5 },
  mini: { width: 56, height: 56, borderRadius: 10 },
  respaldo: { padding: 12, alignItems: "center", gap: 8 }, nombre: { fontFamily: fonts.semibold, color: colors.button, fontSize: 13, textAlign: "center" }, aviso: { fontFamily: fonts.regular, color: colors.muted, fontSize: 10, textAlign: "center" },
});
