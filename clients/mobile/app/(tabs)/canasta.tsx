import { useEffect, useState } from "react";
import { useRouter } from "expo-router";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, useWindowDimensions, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { claveArticulo, Linea } from "../../api/canastas";
import { Costo, costearCanasta } from "../../api/precios";
import { useCanasta } from "../../canasta/CanastaProvider";
import { cantidadValida, SelectorCanasta } from "../../components/ControlesCanasta";
import { ImagenArticulo } from "../../components/ImagenArticulo";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { useRegion } from "../../components/RegionProvider";
import { useSesion } from "../../session/SesionProvider";
import { colors, fonts } from "../../theme/design-system";

function EditorLinea({ linea, precio, consultando = false }: { linea: Linea; precio?: string | null; consultando?: boolean }) {
  const c = useCanasta();
  const ventana = useWindowDimensions();
  const apilada = ventana.width < 360 || ventana.fontScale > 1.2;
  const [cantidad, setCantidad] = useState(String(linea.cantidad));
  const [editar, setEditar] = useState(false);
  useEffect(() => setCantidad(String(linea.cantidad)), [linea.cantidad]);
  const bloqueada = c.ocupada || c.requiereRecarga;
  function quitar() { Alert.alert('Quitar artículo', `¿Quitar ${linea.articulo.producto} de esta canasta?`, [{ text: 'Cancelar', style: 'cancel' }, { text: 'Quitar', style: 'destructive', onPress: () => { void c.quitar(linea.articulo); } }]); }
  return <View style={s.articulo}>
    <View style={[s.fila, apilada && { flexDirection: 'column', alignItems: 'stretch' }]}>
      <View style={[s.descripcionFila, apilada && { flex: undefined, width: '100%' }]}>
      <ImagenArticulo producto={linea.articulo.producto} presentacion={linea.articulo.presentacion} mini />
      <View style={s.descripcion}><Text style={s.nombre}>{linea.articulo.producto}</Text><Text style={s.meta}>{linea.articulo.presentacion}</Text><Text style={s.precioUnidad}>{precio === null ? 'Sin precio en esta cadena' : precio ? `$${precio} por unidad` : consultando ? 'Consultando precio…' : 'Precio no disponible'}</Text></View>
      </View>
      <View style={[s.cantidadGrupo, apilada && { alignSelf: 'flex-end' }]}>
        <Pressable hitSlop={4} accessibilityRole="button" accessibilityLabel={`Reducir cantidad de ${linea.articulo.producto}`} disabled={bloqueada} onPress={() => { if (linea.cantidad === 1) quitar(); else void c.fijar({ ...linea, cantidad: linea.cantidad - 1 }); }} style={[s.paso, s.menos, bloqueada && s.atenuado]}><Ionicons name="remove" size={16} color={colors.text} /></Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel={`Editar cantidad de ${linea.articulo.producto}, ${linea.cantidad}`} onPress={() => setEditar(v => !v)} disabled={bloqueada}><Text style={s.cantidad}>{linea.cantidad}</Text></Pressable>
        <Pressable hitSlop={4} accessibilityRole="button" accessibilityLabel={`Aumentar cantidad de ${linea.articulo.producto}`} disabled={bloqueada || !Number.isSafeInteger(linea.cantidad + 1)} onPress={() => { void c.fijar({ ...linea, cantidad: linea.cantidad + 1 }); }} style={[s.paso, bloqueada && s.atenuado]}><Ionicons name="add" size={16} color="white" /></Pressable>
      </View>
    </View>
    {editar && <View style={s.fila}><TextInput style={s.campo} accessibilityLabel={`Cantidad de ${linea.articulo.producto}`} value={cantidad} onChangeText={setCantidad} keyboardType="number-pad" maxLength={16} editable={!bloqueada} selectTextOnFocus /><Pressable accessibilityRole="button" accessibilityLabel="Guardar cantidad" disabled={bloqueada || !cantidadValida(cantidad)} style={s.guardar} onPress={() => { void c.fijar({ ...linea, cantidad: Number(cantidad) }).then(ok => { if (ok) setEditar(false); }); }}><Ionicons name="checkmark" size={22} color={colors.button} /></Pressable><Pressable accessibilityRole="button" accessibilityLabel="Cancelar cambio de cantidad" disabled={bloqueada} style={s.guardar} onPress={() => { setCantidad(String(linea.cantidad)); setEditar(false); }}><Ionicons name="close" size={22} color={colors.muted} /></Pressable></View>}
    {editar && !cantidadValida(cantidad) && <Text accessibilityRole="alert" style={s.meta}>Usa un entero mayor que cero.</Text>}
  </View>;
}
export default function MiCanasta() {
  const sesion = useSesion();
  const c = useCanasta();
  const router = useRouter();
  const { entidad } = useRegion();
  const [costo, setCosto] = useState<{ datos: Costo; simulador: boolean; clave: string }>();
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);
  const [intento, setIntento] = useState(0);
  const [cadena, setCadena] = useState('');
  const lineas = c.actual?.lineas;
  const clave = JSON.stringify([c.actual?.id, lineas, entidad.trim(), sesion.cuenta?.id]);
  useEffect(() => {
    setCosto(undefined); setError(''); setCargando(false);
    if (!lineas?.length || sesion.estado !== 'conSesion' || c.requiereRecarga) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      if (c.ocupada) return;
      setCargando(true);
      void costearCanasta(lineas, entidad, controller.signal).then(r => { if (!controller.signal.aborted) setCosto({ ...r, clave }); })
        .catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'No pudimos calcular el costo.'); })
        .finally(() => { if (!controller.signal.aborted) setCargando(false); });
    }, 400);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [clave, intento, c.ocupada, c.requiereRecarga, sesion.estado]);
  const vigente = costo?.clave === clave && !c.ocupada && !c.requiereRecarga ? costo : undefined;
  const seleccionada = vigente?.datos.cadenas.find(v => v.cadena === cadena) ?? vigente?.datos.cadenas[0];
  return <View style={s.fondo}>
    <ScrollView contentContainerStyle={s.contenido} keyboardShouldPersistTaps="handled">
      {sesion.estado === 'conSesion' ? <>
        <View style={s.barra}><Pressable accessibilityRole="button" onPress={() => router.push('/')} style={s.agregar}><Ionicons name="add" size={13} color="white" /><Text style={s.agregarTexto}>Agregar más</Text></Pressable><View style={{ flex: 1 }}><SelectorCanasta compacto /></View></View>
        {c.actual && <>
          {c.actual.lineas.length === 0 ? <View style={s.vacia}><Ionicons name="basket-outline" size={52} color={colors.primary} /><Text style={s.titulo}>Tu canasta está lista para empezar</Text><Text style={s.texto}>Busca artículos y toca + para agregarlos aquí.</Text><BotonAcceso titulo="Explorar artículos" onPress={() => router.push('/')} /></View> : <>
            <View style={s.cadenaFila}><View style={{ flex: 1 }}><Text style={s.cadena}>{seleccionada?.cadena ?? 'Artículos en tu canasta'}</Text><Text style={s.meta}>{seleccionada ? `Precios estimados · ${entidad}` : entidad}</Text></View><Pressable accessibilityRole="button" accessibilityLabel="Actualizar costo de la canasta" onPress={() => setIntento(n => n + 1)} style={s.guardar}><Ionicons name="refresh-outline" size={19} color={colors.button} /></Pressable></View>
            {lineas?.map(l => <EditorLinea key={claveArticulo(l.articulo)} linea={l} consultando={cargando || c.ocupada} precio={seleccionada?.lineas.find(v => claveArticulo(v.articulo) === claveArticulo(l.articulo))?.precio?.monto ?? (seleccionada ? null : undefined)} />)}
            {cargando && <ActivityIndicator color={colors.primary} accessibilityLabel="Consultando costo estimado" />}
            {!!error && <Text accessibilityRole="alert" style={s.texto}>{error}</Text>}
            {vigente && vigente.datos.cadenas.length === 0 && <Text style={s.texto}>No hay precios disponibles para estimar esta canasta. No equivale a un costo de cero.</Text>}
          </>}
        </>}
      </> : <View style={s.vacia}><Ionicons name="basket-outline" size={52} color={colors.primary} /><Text style={s.titulo}>Tus compras, en una canasta</Text><Text style={s.texto}>{sesion.estado === 'cargando' ? 'Recuperando tu sesión…' : sesion.mensaje ?? 'Crea una cuenta o inicia sesión para guardar tus artículos.'}</Text><BotonAcceso titulo="Iniciar sesión o crear cuenta" disabled={sesion.estado === 'cargando'} onPress={() => router.push('/acceso')} />{sesion.estado === 'error' && <BotonAcceso titulo="Reintentar" secundario onPress={() => { void sesion.reintentar(); }} />}</View>}
    </ScrollView>
    {vigente && !!lineas?.length && vigente.datos.cadenas.length > 0 && <ScrollView style={s.resumen} contentContainerStyle={s.resumenContenido}>
      <Text style={s.resumenTitulo}>COSTO ESTIMADO POR CADENA COMERCIAL</Text>
      {vigente.datos.cadenas.map(v => <Pressable key={v.cadena} accessibilityRole="button" accessibilityLabel={`Ver precios de ${v.cadena}`} onPress={() => setCadena(v.cadena)} style={s.totalFila}><Text style={[s.totalNombre, v.cadena === seleccionada?.cadena && { fontFamily: fonts.semibold }]}>{v.cadena}{v.faltan ? ` · Faltan ${v.faltan}` : ''}</Text><Text style={s.total}>${v.total.monto}{v.faltan ? ' parcial' : ''}</Text></Pressable>)}
      <View style={s.separador} /><Text style={s.resumenNota}>{vigente.simulador ? 'Simulador · ' : ''}{vigente.datos.quincena} · {lineas.length} artículos · {vigente.datos.cadenas.length} cadenas. Toca una cadena para ver sus precios.</Text>
      <Text style={s.resumenNota}>Estimaciones independientes en MXN; no se suman entre cadenas. Los precios observados no garantizan precio ni existencia en caja.</Text>
    </ScrollView>}
  </View>;
}
const s = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colors.background }, contenido: { padding: 16, gap: 12, paddingBottom: 24 }, barra: { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: 4 },
  agregar: { backgroundColor: colors.button, borderRadius: 22, paddingHorizontal: 10, minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 3 }, agregarTexto: { color: 'white', fontFamily: fonts.semibold, fontSize: 11 },
  descripcionFila: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 10 }, atenuado: { opacity: 0.45 },
  fila: { flexDirection: 'row', alignItems: 'center', gap: 10 }, articulo: { backgroundColor: 'white', borderRadius: 12, borderWidth: 1, borderColor: colors.border, padding: 10, gap: 10 }, descripcion: { flex: 1 }, nombre: { fontFamily: fonts.semibold, fontSize: 12, color: colors.text, lineHeight: 16 }, meta: { fontFamily: fonts.regular, color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 2 }, precioUnidad: { fontFamily: fonts.regular, color: colors.muted, fontSize: 10, marginTop: 3 },
  cantidadGrupo: { flexDirection: 'row', alignItems: 'center', gap: 8 }, paso: { width: 36, height: 36, borderRadius: 10, backgroundColor: colors.button, alignItems: 'center', justifyContent: 'center' }, menos: { backgroundColor: '#EEE9DD' }, cantidad: { fontFamily: fonts.semibold, fontSize: 13, color: colors.text, minWidth: 20, textAlign: 'center', paddingVertical: 12 }, campo: { flex: 1, minHeight: 44, padding: 10, borderRadius: 10, borderWidth: 1, borderColor: colors.border, color: colors.text }, guardar: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  cadenaFila: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 2 }, cadena: { fontFamily: fonts.semibold, fontSize: 13, color: colors.text }, vacia: { padding: 24, gap: 18, backgroundColor: 'white', borderRadius: 18, marginTop: 12 }, titulo: { fontFamily: fonts.semibold, fontSize: 21, lineHeight: 28, color: colors.text }, texto: { fontFamily: fonts.regular, color: colors.muted, fontSize: 14, lineHeight: 22 },
  resumen: { margin: 16, marginTop: 0, maxHeight: '35%', flexGrow: 0, backgroundColor: colors.text, borderRadius: 16, boxShadow: '0px 4px 8px rgba(0,0,0,0.13)' }, resumenContenido: { padding: 16, gap: 8 }, resumenTitulo: { fontFamily: fonts.semibold, color: 'white', fontSize: 10, letterSpacing: 0.4 }, totalFila: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 8, minHeight: 44 }, totalNombre: { flex: 1, minWidth: 100, color: 'white', fontFamily: fonts.regular, fontSize: 12 }, total: { color: 'white', fontFamily: fonts.semibold, fontSize: 13 }, separador: { height: 1, backgroundColor: '#5B5B57', marginTop: 4 }, resumenNota: { fontFamily: fonts.regular, color: '#D1D1C9', fontSize: 10, lineHeight: 15 },
});
