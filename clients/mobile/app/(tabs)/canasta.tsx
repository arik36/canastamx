import { useEffect, useState } from "react";
import { useRouter } from "expo-router";
import { ActivityIndicator, ScrollView, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { claveArticulo, Linea } from "../../api/canastas";
import { Costo, costearCanasta } from "../../api/precios";
import { esUrlDeSimulador } from "../../api/analitica";
import { useCanasta } from "../../canasta/CanastaProvider";
import { cantidadValida, estilos as s, SelectorCanasta } from "../../components/ControlesCanasta";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { useSesion } from "../../session/SesionProvider";

function EditorLinea({ linea }: { linea: Linea }) {
  const c = useCanasta();
  const [cantidad, setCantidad] = useState(String(linea.cantidad));
  useEffect(() => setCantidad(String(linea.cantidad)), [linea.cantidad]);
  return <View style={s.tarjeta}>
    <Text style={s.subtitulo}>{linea.articulo.producto}</Text><Text style={s.texto}>{linea.articulo.presentacion}</Text>
    <Text style={s.meta}>Cantidad guardada: {linea.cantidad}</Text>
    <TextInput accessibilityLabel={`Cantidad de ${linea.articulo.producto}`} style={s.campo} keyboardType="number-pad"
      value={cantidad} onChangeText={setCantidad} editable={!c.ocupada} />
    {!cantidadValida(cantidad) && <Text accessibilityRole="alert" style={s.texto}>Usa un entero mayor que cero.</Text>}
    <BotonAcceso titulo="Guardar cantidad" disabled={c.ocupada || c.requiereRecarga || !cantidadValida(cantidad) || Number(cantidad) === linea.cantidad}
      onPress={() => { void c.fijar({ ...linea, cantidad: Number(cantidad) }); }} />
    <BotonAcceso titulo={`Quitar ${linea.articulo.producto}`} secundario disabled={c.ocupada || c.requiereRecarga} onPress={() => { void c.quitar(linea.articulo); }} />
  </View>;
}
export default function MiCanasta() {
  const sesion = useSesion();
  const c = useCanasta();
  const router = useRouter();
  const [entidad, setEntidad] = useState("Guanajuato");
  const [costo, setCosto] = useState<{ datos: Costo; simulador: boolean; clave: string }>();
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [intento, setIntento] = useState(0);
  const lineas = c.actual?.lineas;
  const clave = JSON.stringify([c.actual?.id, lineas, entidad.trim(), sesion.cuenta?.id]);
  useEffect(() => {
    setCosto(undefined); setError(""); setCargando(false);
    if (!lineas?.length || sesion.estado !== "conSesion" || c.requiereRecarga) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      if (c.ocupada) return;
      setCargando(true);
      void costearCanasta(lineas, entidad, controller.signal).then(r => {
        if (!controller.signal.aborted) setCosto({ ...r, clave });
      }).catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : "No pudimos calcular el costo."); })
        .finally(() => { if (!controller.signal.aborted) setCargando(false); });
    }, 400);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [clave, intento, c.ocupada, c.requiereRecarga, sesion.estado]);
  const vigente = costo?.clave === clave && !c.ocupada && !c.requiereRecarga ? costo : undefined;
  return <SafeAreaView style={s.fondo} edges={["bottom", "left", "right"]}>
    <ScrollView contentContainerStyle={s.contenido} keyboardShouldPersistTaps="handled">
      {sesion.estado === "conSesion" ? <>
        <Text style={s.texto}>Tus canastas se guardan en tu cuenta y se recuperan al abrir la app.</Text>
        <SelectorCanasta />
        {c.actual && <>
          <Text accessibilityRole="header" style={s.titulo}>{c.actual.nombre}</Text>
          {lineas?.length === 0 && <Text style={s.texto}>Esta canasta está vacía. Busca un artículo en Inicio y agrégalo desde su detalle.</Text>}
          {lineas?.map(l => <EditorLinea key={`${c.actual!.id}-${claveArticulo(l.articulo)}`} linea={l} />)}
          <BotonAcceso titulo="Buscar artículos para agregar" secundario onPress={() => router.push("/")} />
          {!!lineas?.length && <View style={s.grupo}>
            <Text accessibilityRole="header" style={s.subtitulo}>Costo estimado por cadena</Text>
            <Text style={s.texto}>Entidad federativa para estimar el costo</Text>
            <TextInput accessibilityLabel="Entidad para el costo" style={s.campo} value={entidad} onChangeText={setEntidad} />
            <Text style={s.meta}>{(vigente?.simulador ?? esUrlDeSimulador()) ? "Simulador · datos de prueba" : "Interfaz analítica"}</Text>
            {cargando && <ActivityIndicator accessibilityLabel="Consultando costo estimado" />}
            {!!error && <Text accessibilityRole="alert" style={s.texto}>{error}</Text>}
            <BotonAcceso titulo="Actualizar costo" secundario disabled={cargando || c.ocupada} onPress={() => setIntento(n => n + 1)} />
            {vigente && <>
              <Text style={s.texto}>{vigente.datos.entidad} · Quincena: {vigente.datos.quincena}</Text>
              <Text style={s.meta}>Población: {lineas.length} artículos de esta canasta · {vigente.datos.cadenas.length} cadenas con datos en la entidad y quincena indicadas.</Text>
              {vigente.datos.cadenas.length === 0 && <Text style={s.texto}>Sin datos de costo para esta entidad. No equivale a un costo de cero.</Text>}
              {vigente.datos.cadenas.map(cadena => <View key={cadena.cadena} style={s.tarjeta}>
                <Text style={s.subtitulo}>{cadena.cadena}</Text>
                <Text style={s.titulo}>${cadena.total.monto} {cadena.total.moneda}</Text>
                <Text style={s.texto}>{cadena.faltan ? `Total parcial: faltan ${cadena.faltan} artículos sin precio; no se incluyen en el total.` : "Todos los artículos tienen precio."}</Text>
                {cadena.lineas.map(l => <Text key={claveArticulo(l.articulo)} style={s.meta}>
                  {l.articulo.producto} · {l.articulo.presentacion} · Cantidad: {l.cantidad}{"\n"}
                  {l.precio === null ? "Sin precio" : `Mediana por unidad: $${l.precio.monto} ${l.precio.moneda}`}
                </Text>)}
              </View>)}
            </>}
            <Text style={s.meta}>El servicio estima con la mediana de las tiendas de cada cadena. Los precios observados no garantizan el precio ni la existencia en caja.</Text>
          </View>}
        </>}
      </> : <View style={s.grupo}>
        <Text style={s.texto}>{sesion.estado === "cargando" ? "Recuperando tu sesión…" : sesion.mensaje ?? "Inicia sesión para crear y recuperar tus canastas."}</Text>
        {sesion.estado === "error" && <BotonAcceso titulo="Reintentar sesión" onPress={() => { void sesion.reintentar(); }} />}
        <BotonAcceso titulo="Iniciar sesión" disabled={sesion.estado === "cargando"} onPress={() => router.push("/acceso")} />
      </View>}
    </ScrollView>
  </SafeAreaView>;
}
