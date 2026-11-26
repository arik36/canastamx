import { useEffect, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import { compararPrecios, Comparacion } from "../../api/precios";
import { esUrlDeSimulador } from "../../api/analitica";
import { useCanasta } from "../../canasta/CanastaProvider";
import { cantidadValida, SelectorCanasta } from "../../components/ControlesCanasta";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { useSesion } from "../../session/SesionProvider";
import { ImagenArticulo } from "../../components/ImagenArticulo";
import { colors, fonts } from "../../theme/design-system";

export default function DetalleDeArticulo() {
  const params = useLocalSearchParams<{ producto?: string; nombre?: string; presentacion?: string; entidad?: string; catalogo?: string }>();
  const producto = typeof params.producto === "string" ? params.producto : "";
  const presentacion = typeof params.presentacion === "string" ? params.presentacion : "";
  const entidad = typeof params.entidad === "string" ? params.entidad : "";
  const router = useRouter();
  const sesion = useSesion();
  const canasta = useCanasta();
  const [datos, setDatos] = useState<Comparacion>();
  const [simulador, setSimulador] = useState(esUrlDeSimulador);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [intento, setIntento] = useState(0);
  const [cantidad, setCantidad] = useState("1");
  const [mensaje, setMensaje] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setDatos(undefined); setError(""); setMensaje("");
    if (!producto || !presentacion || !entidad) { setError("Abre un artículo desde los resultados de Inicio."); return; }
    setCargando(true);
    void compararPrecios({ producto, presentacion }, entidad, controller.signal).then(r => {
      if (!controller.signal.aborted) { setDatos(r.datos); setSimulador(r.simulador); }
    }).catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : "No pudimos comparar los precios."); })
      .finally(() => { if (!controller.signal.aborted) setCargando(false); });
    return () => controller.abort();
  }, [producto, presentacion, entidad, intento]);
  const catalogo = typeof params.catalogo === "string" ? params.catalogo : "";
  const nombre = typeof params.nombre === "string" && params.nombre ? params.nombre : producto || "Detalle de artículo";
  function paso(delta: number) {
    const actual = cantidadValida(cantidad) ? Number(cantidad) : 1;
    const nueva = Math.max(1, actual + delta);
    if (Number.isSafeInteger(nueva)) { setCantidad(String(nueva)); setMensaje(""); }
  }
  return <SafeAreaView style={s.fondo}>
    <KeyboardAvoidingView style={s.fondo} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 16 }}>
        <View>
          <ImagenArticulo grande producto={producto} presentacion={presentacion} catalogo={catalogo} />
          <Pressable accessibilityRole="button" accessibilityLabel="Volver a los artículos" style={s.volver}
            onPress={() => { if (router.canGoBack()) router.back(); else router.replace("/"); }}><Ionicons name="chevron-back" size={23} color={colors.text} /></Pressable>
          <Text style={s.ilustrativa}>Imagen ilustrativa</Text>
        </View>
        <View style={s.contenido}>
          <Text accessibilityRole="header" style={s.titulo}>{nombre}</Text>
          <View style={s.chips}><Text style={s.chip}>{presentacion}</Text>{!!catalogo && <Text style={s.chip}>{catalogo}</Text>}</View>
          {simulador && <Text style={s.meta}>Simulador · datos de prueba</Text>}
          {cargando && <View style={s.estado}><ActivityIndicator color={colors.button} accessibilityLabel="Consultando precios" /><Text style={s.meta}>Consultando precios por establecimiento…</Text></View>}
          {!!error && <View style={s.tarjeta}><Text accessibilityRole="alert" style={s.texto}>{error}</Text>
            {!!producto && <BotonAcceso titulo="Reintentar precios" onPress={() => setIntento(n => n + 1)} />}</View>}
          {datos && <>
            <View style={s.seccion}><Text style={s.subtitulo}>Compara precios</Text><Text style={s.meta}>{datos.entidad} · {datos.quincena}</Text></View>
            <Text style={s.meta}>{datos.establecimientos.length} registros de precio por establecimiento en esta consulta.</Text>
            {datos.establecimientos.length === 0 && <Text style={s.texto}>No hay precios para comparar.</Text>}
            {datos.establecimientos.length === 1 && <Text style={s.meta}>Sólo hay un establecimiento disponible.</Text>}
            {datos.establecimientos.map((e, i) => <View key={`${e.nombre}-${e.marca}-${i}`} style={s.tarjeta}>
              <View style={s.filaPrecio}><Text style={s.precio}>${e.precio.monto}</Text><Text style={s.moneda}>{e.precio.moneda}</Text></View>
              <View style={s.tienda}><Ionicons name="storefront-outline" size={17} color={colors.button} /><Text style={s.establecimiento}>{e.nombre}</Text></View>
              <Text style={s.meta}>{[e.cadena, e.marca && `Marca: ${e.marca}`].filter(Boolean).join(" · ")}</Text>
              {!!e.municipio && <Text style={s.meta}>{e.municipio}</Text>}
              {!!e.direccion && <Text style={s.meta}>{e.direccion}</Text>}
              <Text style={s.fecha}>Último registro: {e.fechaRegistro}</Text>
            </View>)}
          </>}
          <Text style={s.aviso}>Precios observados en QQP; no garantizan precio ni existencia en caja.</Text>
        </View>
      {datos && sesion.estado === "conSesion" && <View style={s.controles}>
          <SelectorCanasta compacto />
          <View style={s.cantidadFila}>
            <Pressable accessibilityRole="button" accessibilityLabel="Reducir cantidad" disabled={canasta.ocupada || cantidad === "1"} onPress={() => paso(-1)} style={[s.paso, (canasta.ocupada || cantidad === "1") && s.atenuado]}><Ionicons name="remove" size={20} color={colors.text} /></Pressable>
            <TextInput accessibilityLabel="Cantidad para agregar" style={s.cantidad} keyboardType="number-pad" value={cantidad}
              onChangeText={v => { setCantidad(v); setMensaje(""); }} editable={!canasta.ocupada} selectTextOnFocus />
            <Pressable accessibilityRole="button" accessibilityLabel="Aumentar cantidad" disabled={canasta.ocupada} onPress={() => paso(1)} style={[s.paso, s.mas, canasta.ocupada && s.atenuado]}><Ionicons name="add" size={20} color="white" /></Pressable>
          </View>
          {!cantidadValida(cantidad) && <Text accessibilityRole="alert" style={s.meta}>Usa un entero mayor que cero.</Text>}
          {!!mensaje && <View style={s.confirmacion}><Text accessibilityLiveRegion="polite" style={[s.meta, { flex: 1 }]}>{mensaje}</Text><Pressable accessibilityRole="button" style={s.verCanasta} onPress={() => router.push("/canasta")}><Text style={s.enlace}>Ver canasta</Text></Pressable></View>}
      </View>}
      </ScrollView>
      {datos && <View style={s.pie}>
        {sesion.estado === "conSesion" && <Text numberOfLines={1} style={s.meta}>{canasta.actual ? `Canasta: ${canasta.actual.nombre}` : "Elige o crea una canasta en el detalle"}</Text>}
        {sesion.estado === "conSesion" ? <BotonAcceso titulo={canasta.ocupada ? "Guardando…" : `Agregar ${cantidadValida(cantidad) ? cantidad : ""} a mi canasta`} disabled={canasta.ocupada || canasta.requiereRecarga || !canasta.actual || !cantidadValida(cantidad)}
          onPress={() => { setMensaje(""); void canasta.agregar(datos.articulo, Number(cantidad)).then(ok => {
            if (ok) setMensaje(`Agregado a «${canasta.actual?.nombre ?? "tu canasta"}». Si ya estaba, se sumó la cantidad.`);
          }); }} /> : <>
          <Text style={s.meta}>{sesion.estado === "cargando" ? "Recuperando sesión…" : "Inicia sesión para guardar este artículo en una canasta."}</Text>
          <BotonAcceso titulo="Iniciar sesión" disabled={sesion.estado === "cargando"} onPress={() => router.push("/acceso")} />
        </>}
      </View>}
    </KeyboardAvoidingView>
  </SafeAreaView>;
}
const s = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colors.background }, contenido: { padding: 16, gap: 12 },
  volver: { position: "absolute", top: 12, left: 16, width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: "rgba(255,255,255,0.95)" },
  ilustrativa: { position: "absolute", bottom: 12, right: 16, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 8, backgroundColor: "rgba(30,35,35,0.7)", color: "white", fontFamily: fonts.regular, fontSize: 10 },
  titulo: { fontFamily: fonts.semibold, fontSize: 22, lineHeight: 29, color: colors.text },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 6 }, chip: { borderWidth: 1, borderColor: colors.border, borderRadius: 14, paddingVertical: 5, paddingHorizontal: 10, backgroundColor: "white", fontFamily: fonts.regular, fontSize: 11, color: colors.muted },
  estado: { paddingVertical: 24, gap: 12, alignItems: "center" }, seccion: { gap: 4, marginTop: 8 },
  subtitulo: { fontFamily: fonts.semibold, fontSize: 16, color: colors.text },
  texto: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 21, color: colors.text },
  meta: { fontFamily: fonts.regular, fontSize: 11, lineHeight: 16, color: colors.muted },
  tarjeta: { borderWidth: 1, borderColor: colors.border, borderRadius: 18, backgroundColor: "white", padding: 16, gap: 6 },
  filaPrecio: { flexDirection: "row", flexWrap: "wrap", alignItems: "baseline", gap: 6 }, precio: { fontFamily: fonts.semibold, fontSize: 30, color: colors.text }, moneda: { fontFamily: fonts.regular, fontSize: 11, color: colors.muted },
  tienda: { flexDirection: "row", alignItems: "center", gap: 7, marginTop: 2 }, establecimiento: { flex: 1, fontFamily: fonts.semibold, fontSize: 13, color: colors.text },
  fecha: { fontFamily: fonts.regular, fontSize: 10, color: colors.muted, marginTop: 3 }, aviso: { fontFamily: fonts.regular, fontSize: 10, lineHeight: 15, color: colors.muted, textAlign: "center", marginVertical: 8 },
  pie: { flexShrink: 0, padding: 16, gap: 8, borderTopWidth: 1, borderTopColor: colors.border, backgroundColor: "white" }, controles: { padding: 16, paddingTop: 0, gap: 12 },
  cantidadFila: { flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 14 }, paso: { width: 44, height: 44, borderRadius: 22, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.background, alignItems: "center", justifyContent: "center" },
  mas: { backgroundColor: colors.button, borderColor: colors.button }, atenuado: { opacity: 0.45 }, cantidad: { minWidth: 64, maxWidth: 120, minHeight: 44, textAlign: "center", fontFamily: fonts.semibold, fontSize: 22, color: colors.text, padding: 4 },
  confirmacion: { flexDirection: "row", alignItems: "center", gap: 8 }, verCanasta: { minHeight: 44, justifyContent: "center", paddingHorizontal: 4 }, enlace: { fontFamily: fonts.semibold, fontSize: 12, color: colors.button },
});
