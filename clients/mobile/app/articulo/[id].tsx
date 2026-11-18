import { useEffect, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";
import { ActivityIndicator, ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { compararPrecios, Comparacion } from "../../api/precios";
import { esUrlDeSimulador } from "../../api/analitica";
import { useCanasta } from "../../canasta/CanastaProvider";
import { cantidadValida, estilos as s, SelectorCanasta } from "../../components/ControlesCanasta";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { useSesion } from "../../session/SesionProvider";

export default function DetalleDeArticulo() {
  const params = useLocalSearchParams<{ producto?: string; presentacion?: string; entidad?: string }>();
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
  return <SafeAreaView style={s.fondo} edges={["bottom", "left", "right"]}>
    <ScrollView contentContainerStyle={s.contenido} keyboardShouldPersistTaps="handled">
      <Text accessibilityRole="header" style={s.titulo}>Detalle de artículo</Text>
      <Text style={s.subtitulo}>{producto}</Text><Text style={s.texto}>{presentacion}</Text>
      <Text style={s.meta}>{simulador ? "Simulador · datos de prueba" : "Interfaz analítica"}</Text>
      {cargando && <ActivityIndicator accessibilityLabel="Consultando precios" />}
      {!!error && <View style={s.grupo}><Text accessibilityRole="alert" style={s.texto}>{error}</Text>
        {!!producto && <BotonAcceso titulo="Reintentar precios" onPress={() => setIntento(n => n + 1)} />}</View>}
      {datos && <>
        <Text style={s.texto}>{datos.entidad} · Quincena: {datos.quincena}</Text>
        <Text style={s.meta}>Población: {datos.establecimientos.length} registros de precio por establecimiento en esta consulta.</Text>
        {datos.establecimientos.length === 0 && <Text style={s.texto}>No hay precios para comparar.</Text>}
        {datos.establecimientos.length === 1 && <Text style={s.texto}>Sólo hay un establecimiento disponible para este artículo.</Text>}
        {datos.establecimientos.map((e, i) => <View key={`${e.nombre}-${e.marca}-${i}`} style={s.tarjeta}>
          <Text style={s.subtitulo}>{e.nombre}</Text><Text style={s.texto}>{e.cadena} · {e.marca}</Text>
          {!!e.municipio && <Text style={s.meta}>{e.municipio}</Text>}
          {!!e.direccion && <Text style={s.meta}>{e.direccion}</Text>}
          <Text style={s.titulo}>${e.precio.monto} {e.precio.moneda}</Text>
          <Text style={s.meta}>Fecha de registro: {e.fechaRegistro}</Text>
        </View>)}
        {sesion.estado === "conSesion" ? <View style={s.grupo}>
          <SelectorCanasta />
          <Text style={s.texto}>Cantidad que se agregará{canasta.actual ? ` a «${canasta.actual.nombre}»` : ""}</Text>
          <TextInput accessibilityLabel="Cantidad para agregar" style={s.campo} keyboardType="number-pad" value={cantidad}
            onChangeText={v => { setCantidad(v); setMensaje(""); }} editable={!canasta.ocupada} />
          {!cantidadValida(cantidad) && <Text accessibilityRole="alert" style={s.texto}>Usa un entero mayor que cero.</Text>}
          <BotonAcceso titulo="Agregar a canasta" disabled={canasta.ocupada || canasta.requiereRecarga || !canasta.actual || !cantidadValida(cantidad)}
            onPress={() => { setMensaje(""); void canasta.agregar(datos.articulo, Number(cantidad)).then(ok => {
              if (ok) setMensaje("Artículo guardado. Si ya estaba en la canasta, se sumó la cantidad.");
            }); }} />
          {!!mensaje && <Text accessibilityLiveRegion="polite" style={s.texto}>{mensaje}</Text>}
          <BotonAcceso titulo="Ver mi canasta" secundario onPress={() => router.push("/canasta")} />
        </View> : <View style={s.grupo}>
          <Text style={s.texto}>{sesion.estado === "cargando" ? "Recuperando sesión…" : "Inicia sesión para guardar artículos en una canasta."}</Text>
          <BotonAcceso titulo="Iniciar sesión" disabled={sesion.estado === "cargando"} onPress={() => router.push("/acceso")} />
        </View>}
      </>}
      <Text style={s.meta}>Precios observados en QQP; no garantizan precio ni existencia en caja.</Text>
    </ScrollView>
  </SafeAreaView>;
}
