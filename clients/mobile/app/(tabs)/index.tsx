import { useEffect, useRef, useState } from "react";
import { useRouter } from "expo-router";
import { ActivityIndicator, FlatList, Keyboard, Pressable, ScrollView, StyleSheet, Text, TextInput, useWindowDimensions, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { ArticuloEncontrado, buscarArticulos, ErrorAnalitica, ResultadoDeBusqueda } from "../../api/analitica";
import { explorarArticulos } from "../../api/explorar";
import { ImagenArticulo } from "../../components/ImagenArticulo";
import { useRegion } from "../../components/RegionProvider";
import { useCanasta } from "../../canasta/CanastaProvider";
import { useSesion } from "../../session/SesionProvider";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { PanelInferior } from "../../components/PanelInferior";
import { colors, fonts } from "../../theme/design-system";

const catalogos = [['BASICOS', 'Básicos'], ['PACIC', 'PACIC'], ['FRUTAS Y LEGUMBRES', 'Frutas y Legumbres'], ['MERCADOS', 'Mercados'], ['PESCADOS Y MARISCOS', 'Pescados y Mariscos']] as const;
const centavos = (v: string) => { const [e, d = ''] = v.split('.'); return BigInt(e + d.padEnd(2, '0')); };
export default function Inicio() {
  const router = useRouter();
  const { entidad, setQuincena } = useRegion();
  const sesion = useSesion();
  const canasta = useCanasta();
  const ventana = useWindowDimensions();
  const columnas = ventana.width < 350 || ventana.fontScale > 1.3 ? 1 : 2;
  const [termino, setTermino] = useState('');
  const [catalogo, setCatalogo] = useState<string | undefined>('BASICOS');
  const [orden, setOrden] = useState<'seleccion' | 'menor' | 'mayor'>('seleccion');
  const [datos, setDatos] = useState<ResultadoDeBusqueda>();
  const [simulador, setSimulador] = useState(false);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [offset, setOffset] = useState(0);
  const [intento, setIntento] = useState(0);
  const [filtros, setFiltros] = useState(false);
  const [minimo, setMinimo] = useState('');
  const [maximo, setMaximo] = useState('');
  const [rango, setRango] = useState({ min: '', max: '' });
  const [errorFiltro, setErrorFiltro] = useState('');
  const [agregar, setAgregar] = useState<ArticuloEncontrado>();
  const [nombre, setNombre] = useState('');
  const [crearCanasta, setCrearCanasta] = useState(false);
  const [aviso, setAviso] = useState('');
  const solicitud = useRef(0);
  const explorando = termino.trim().length < 2;
  useEffect(() => {
    const controller = new AbortController();
    const numero = ++solicitud.current;
    setCargando(true); setError(''); setDatos(undefined);
    const timer = setTimeout(() => {
      const peticion = termino.trim().length >= 2
        ? buscarArticulos({ q: termino, entidad, catalogo, offset }, controller.signal)
        : explorarArticulos(entidad, catalogo, controller.signal);
      void peticion.then(r => {
        if (controller.signal.aborted || numero !== solicitud.current) return;
        setDatos(r.datos); setSimulador(r.simulador);
        if (r.datos.cobertura) setQuincena(r.datos.quincena);
      }).catch(e => {
        if (!controller.signal.aborted && numero === solicitud.current) setError(e instanceof ErrorAnalitica ? e.message : 'No pudimos cargar los artículos.');
      }).finally(() => { if (!controller.signal.aborted && numero === solicitud.current) setCargando(false); });
    }, 350);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [termino, entidad, catalogo, offset, intento, setQuincena]);
  useEffect(() => { setOffset(0); }, [entidad]);
  useEffect(() => { if (!aviso) return; const timer = setTimeout(() => setAviso(''), 3500); return () => clearTimeout(timer); }, [aviso]);
  const resultados = datos?.cobertura ? datos : undefined;
  const visibles = (resultados?.resultados ?? []).filter(a => (!rango.min || centavos(a.precioTipico.monto) >= centavos(rango.min))
    && (!rango.max || centavos(a.precioTipico.monto) <= centavos(rango.max)));
  visibles.sort((a, b) => {
    if (orden === 'seleccion') return 0;
    const x = centavos(a.precioTipico.monto), y = centavos(b.precioTipico.monto);
    return (x < y ? -1 : x > y ? 1 : 0) * (orden === 'menor' ? 1 : -1);
  });
  function abrir(a: ArticuloEncontrado) {
    router.push({ pathname: '/articulo/[id]', params: { id: 'comparar', nombre: a.nombre, producto: a.articulo.producto, presentacion: a.articulo.presentacion, entidad, catalogo: a.catalogo } });
  }
  function aplicar() {
    const min = minimo.trim().replace(',', '.');
    const max = maximo.trim().replace(',', '.');
    if ([min, max].some(v => v && !/^\d+(\.\d{1,2})?$/.test(v)) || (min && max && centavos(min) > centavos(max))) {
      setErrorFiltro('Escribe precios válidos y un máximo mayor o igual al mínimo.'); return;
    }
    setRango({ min, max }); setErrorFiltro(''); setFiltros(false); Keyboard.dismiss();
  }
  return <SafeAreaView style={s.fondo} edges={['left', 'right']}>
    <FlatList key={columnas} numColumns={columnas} data={visibles} keyExtractor={a => JSON.stringify(a.articulo)}
      columnWrapperStyle={columnas === 2 ? { gap: 12 } : undefined} contentContainerStyle={s.lista} keyboardShouldPersistTaps="handled"
      ListHeaderComponent={<View style={s.cabecera}>
        <View style={s.buscador}>
          <Pressable accessibilityRole="button" accessibilityLabel="Buscar artículos" style={s.buscar} onPress={() => { Keyboard.dismiss(); setIntento(n => n + 1); }}><Ionicons name="search-outline" size={19} color={colors.muted} /></Pressable>
          <TextInput accessibilityLabel="Artículo que buscas" style={s.entrada} value={termino} onChangeText={v => { setTermino(v); setOffset(0); }} placeholder="Buscar artículo (atún, pollo, arroz…)" placeholderTextColor="#8B8B84"
            returnKeyType="search" autoCorrect={false} onSubmitEditing={() => { Keyboard.dismiss(); setIntento(n => n + 1); }} />
          {!!termino && <Pressable accessibilityRole="button" accessibilityLabel="Limpiar búsqueda" style={s.buscar} onPress={() => { setTermino(''); setOffset(0); }}><Ionicons name="close" size={19} color={colors.muted} /></Pressable>}
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.catalogos}>
          {catalogos.map(([id, etiqueta]) => <Pressable key={id} accessibilityRole="button" accessibilityState={{ selected: catalogo === id }} onPress={() => { setCatalogo(catalogo === id ? undefined : id); setOffset(0); }} style={[s.chip, catalogo === id && s.activo]}><Text style={[s.chipTexto, catalogo === id && s.activoTexto]}>{etiqueta}</Text></Pressable>)}
        </ScrollView>
        <View style={s.herramientas}>
          <Pressable accessibilityRole="button" accessibilityLabel="Filtros de precio" onPress={() => { setErrorFiltro(''); setMinimo(rango.min); setMaximo(rango.max); setFiltros(true); }} style={[s.chip, (rango.min || rango.max) && s.activo]}><Ionicons name="filter-outline" size={13} color={rango.min || rango.max ? 'white' : colors.text} /><Text style={[s.chipTexto, (rango.min || rango.max) && s.activoTexto]}>Filtros</Text></Pressable>
          <Text style={s.ordenar}>ORDENAR:</Text>
          {([['menor', 'Precio', 'arrow-up'], ['mayor', 'Precio', 'arrow-down'], ['seleccion', 'Selección', undefined]] as const).map(([id, etiqueta, icono]) => <Pressable key={id} accessibilityRole="button" accessibilityLabel={`Ordenar por ${id === 'seleccion' ? 'selección original' : id === 'menor' ? 'menor precio' : 'mayor precio'}`} accessibilityState={{ selected: orden === id }}
            onPress={() => setOrden(id)} style={[s.ordenChip, orden === id && s.activo]}><Text style={[s.chipTexto, orden === id && s.activoTexto]}>{etiqueta}</Text>{icono && <Ionicons name={icono} size={12} color={orden === id ? 'white' : colors.muted} />}</Pressable>)}
        </View>
        {simulador && <Text style={s.avisoPrueba}>Simulador · datos de prueba</Text>}
        {cargando && <View style={s.estado} accessibilityLiveRegion="polite"><ActivityIndicator color={colors.button} accessibilityLabel="Cargando artículos" /><Text style={s.estadoTitulo}>Consultando artículos</Text><Text style={s.estadoTexto}>Esto puede tardar unos minutos. Puedes cambiar la búsqueda mientras esperas.</Text></View>}
        {!!error && <View style={s.estado}><Ionicons name="cloud-offline-outline" size={32} color={colors.button} /><Text style={s.estadoTitulo}>No pudimos cargar los artículos</Text><Text style={s.estadoTexto}>{error}</Text><BotonAcceso titulo="Reintentar" onPress={() => setIntento(n => n + 1)} /></View>}
        {datos?.cobertura === false && <View style={s.estado}><Ionicons name="location-outline" size={32} color={colors.button} /><Text style={s.estadoTitulo}>Todavía no hay cobertura aquí</Text><Text style={s.estadoTexto}>Puedes consultar {datos.entidadesCubiertas.join(', ')}.</Text></View>}
        {!cargando && !error && resultados && visibles.length === 0 && <View style={s.estado}><Ionicons name="search-outline" size={30} color={colors.button} /><Text style={s.estadoTitulo}>Sin artículos para esta selección</Text><Text style={s.texto}>Prueba otra búsqueda, catálogo o rango de precios.</Text></View>}
      </View>}
      renderItem={({ item }) => <View style={[s.tarjeta, columnas === 1 && { maxWidth: '100%' }]}>
        <Pressable accessibilityRole="button" accessibilityLabel={`Comparar ${item.nombre}, ${item.articulo.presentacion}`} onPress={() => abrir(item)}>
          <ImagenArticulo producto={item.articulo.producto} presentacion={item.articulo.presentacion} catalogo={item.catalogo} />
        </Pressable>
        <View style={s.informacion}>
          <Pressable accessibilityRole="button" accessibilityLabel={`${item.nombre}, ${item.articulo.presentacion}`} onPress={() => abrir(item)}><Text numberOfLines={2} style={s.nombre}>{item.nombre}</Text><Text numberOfLines={2} style={s.presentacion}>{item.articulo.presentacion}</Text></Pressable>
          <View style={s.precioFila}><Text accessibilityLabel={`Precio típico ${item.precioTipico.monto} pesos`} style={s.precio}>${item.precioTipico.monto}</Text>
            <Pressable accessibilityRole="button" hitSlop={4} accessibilityLabel={`Agregar ${item.nombre} a una canasta`} style={s.mas} onPress={() => { if (sesion.estado !== 'conSesion') router.push('/acceso'); else { setNombre(''); setCrearCanasta(false); setAgregar(item); } }}><Ionicons name="add" size={23} color="white" /></Pressable>
          </View>
        </View>
      </View>}
      ListFooterComponent={<View style={s.pie}>
        {!!resultados?.resultados.length && <Text style={s.nota}>{explorando ? 'Selección de artículos para explorar.' : `${resultados.total} resultados · Página ${Math.floor(offset / 20) + 1}.`} {orden !== 'seleccion' || rango.min || rango.max ? 'Orden y rango aplicados a los artículos cargados.' : ''}</Text>}
        {!explorando && resultados && resultados.total > 20 && <View style={s.paginas}><BotonAcceso titulo="Anterior" secundario disabled={!offset || cargando} onPress={() => setOffset(n => Math.max(0, n - 20))} /><BotonAcceso titulo="Siguiente" secundario disabled={offset + 20 >= resultados.total || cargando} onPress={() => setOffset(n => n + 20)} /></View>}
        <Text style={s.nota}>Imágenes ilustrativas; no representan la marca ni el envase exactos.</Text>
        <Text style={s.nota}>Precios típicos en MXN · Mediana QQP. Consulta establecimientos, fechas y observaciones en cada artículo.</Text>
      </View>} />
    {!!aviso && <View style={s.toast}><Ionicons name="checkmark-circle-outline" size={20} color="white" /><Text accessibilityLiveRegion="polite" style={s.toastTexto}>{aviso}</Text></View>}
    <PanelInferior visible={filtros} titulo="Filtrar por precio" cerrar={() => setFiltros(false)}>
      <Text style={s.texto}>Rango para los artículos cargados, en pesos.</Text>
      <View style={s.paginas}><View style={{ flex: 1, gap: 6 }}><Text style={s.nombre}>Desde</Text><TextInput accessibilityLabel="Precio mínimo en pesos" placeholder="$ 0.00" style={[s.campo, { flex: undefined }]} value={minimo} onChangeText={v => { setMinimo(v); setErrorFiltro(''); }} keyboardType="decimal-pad" /></View><View style={{ flex: 1, gap: 6 }}><Text style={s.nombre}>Hasta</Text><TextInput accessibilityLabel="Precio máximo en pesos" placeholder="Sin límite" style={[s.campo, { flex: undefined }]} value={maximo} onChangeText={v => { setMaximo(v); setErrorFiltro(''); }} keyboardType="decimal-pad" /></View></View>
      {!!errorFiltro && <Text accessibilityRole="alert" style={s.texto}>{errorFiltro}</Text>}
      <BotonAcceso titulo="Aplicar filtros" onPress={aplicar} /><BotonAcceso titulo="Quitar filtros" secundario onPress={() => { setErrorFiltro(''); setRango({ min: '', max: '' }); setFiltros(false); Keyboard.dismiss(); }} />
    </PanelInferior>
    <PanelInferior visible={!!agregar} titulo="¿A qué canasta lo agregamos?" cerrar={() => setAgregar(undefined)} bloqueado={canasta.ocupada}>
      <Text style={s.texto}>{agregar?.nombre} · {agregar?.articulo.presentacion}</Text>
      {canasta.canastas.map(c => <Pressable accessibilityRole="button" accessibilityLabel={`Agregar a ${c.nombre}`} key={c.id} style={[s.destino, c.id === canasta.actual?.id && s.destinoActivo]} disabled={canasta.ocupada || canasta.requiereRecarga} onPress={() => { if (agregar) void canasta.agregarEn(c.id, agregar.articulo, 1).then(ok => { if (ok) { setAgregar(undefined); setAviso(`Agregado a «${c.nombre}»`); } }); }}><Ionicons name="basket-outline" size={22} color={colors.button} /><View style={{ flex: 1 }}><Text style={s.nombre}>{c.nombre}</Text><Text style={s.presentacion}>{c.lineas.length} artículos{c.id === canasta.actual?.id ? ' · Activa' : ''}</Text></View><Ionicons name="add-circle-outline" size={26} color={colors.button} /></Pressable>)}
      {canasta.listaCargada && !canasta.canastas.length && <Text style={s.texto}>Crea tu primera canasta para guardar este artículo.</Text>}
      {!canasta.listaCargada && !canasta.error && <ActivityIndicator color={colors.button} accessibilityLabel="Cargando canastas" />}
      {crearCanasta ? <><TextInput style={[s.campo, { flex: undefined }]} accessibilityLabel="Nombre de nueva canasta" placeholder="Ej. Despensa de la quincena" value={nombre} onChangeText={setNombre} maxLength={200} editable={!canasta.ocupada} />
      <BotonAcceso titulo={canasta.ocupada ? 'Creando…' : 'Crear canasta'} disabled={canasta.ocupada || canasta.requiereRecarga || !canasta.listaCargada || !nombre.trim()} onPress={() => { void canasta.crear(nombre).then(ok => { if (ok) { setNombre(''); setCrearCanasta(false); Keyboard.dismiss(); } }); }} /><BotonAcceso titulo="Volver a mis canastas" secundario disabled={canasta.ocupada} onPress={() => { setCrearCanasta(false); Keyboard.dismiss(); }} /></>
        : <BotonAcceso titulo="+ Crear nueva canasta" secundario disabled={canasta.ocupada || canasta.requiereRecarga || !canasta.listaCargada} onPress={() => setCrearCanasta(true)} />}
      {!!canasta.error && <Text accessibilityRole="alert" style={s.texto}>{canasta.error}</Text>}
      {canasta.requiereRecarga && <BotonAcceso titulo="Recuperar canastas" onPress={() => { void canasta.recargar(); }} />}
      <BotonAcceso titulo="Cancelar" secundario disabled={canasta.ocupada} onPress={() => setAgregar(undefined)} />
    </PanelInferior>
  </SafeAreaView>;
}
const s = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colors.background }, lista: { paddingHorizontal: 16, paddingBottom: 24, rowGap: 14 }, cabecera: { gap: 12, paddingTop: 16, paddingBottom: 2 },
  buscador: { flexDirection: 'row', alignItems: 'center', minHeight: 48, backgroundColor: 'white', borderRadius: 16, borderWidth: 1, borderColor: colors.border, boxShadow: '0px 2px 3px rgba(40,35,20,0.08)' },
  entrada: { flex: 1, minHeight: 48, paddingVertical: 10, paddingRight: 8, fontFamily: fonts.regular, fontSize: 13, color: colors.text }, buscar: { width: 40, minHeight: 48, alignItems: 'center', justifyContent: 'center' },
  catalogos: { gap: 8 }, chip: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 8, minHeight: 44, backgroundColor: 'white', borderRadius: 22 },
  chipTexto: { color: colors.text, fontFamily: fonts.semibold, fontSize: 11 }, activo: { backgroundColor: colors.primary }, activoTexto: { color: 'white' },
  herramientas: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 7, paddingVertical: 5 }, ordenar: { color: colors.muted, fontFamily: fonts.semibold, fontSize: 9 }, ordenChip: { minHeight: 40, minWidth: 52, paddingHorizontal: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: 'white', borderRadius: 22, gap: 2 },
  tarjeta: { flex: 1, maxWidth: '50%', borderWidth: 1, borderColor: colors.border, backgroundColor: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0px 2px 3px rgba(40,35,20,0.07)' },
  informacion: { padding: 12, gap: 10, flex: 1 }, nombre: { fontFamily: fonts.semibold, fontSize: 13, lineHeight: 17, color: colors.text }, presentacion: { fontFamily: fonts.regular, fontSize: 11, color: colors.muted, marginTop: 3 },
  precioFila: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto', gap: 4 }, precio: { color: colors.text, fontFamily: fonts.semibold, fontSize: 18 }, mas: { width: 36, height: 36, borderRadius: 11, backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center' },
  pie: { alignItems: 'center', paddingTop: 12, gap: 12 }, nota: { fontFamily: fonts.regular, fontSize: 10, lineHeight: 15, color: '#77746C', textAlign: 'center', fontStyle: 'italic' },
  texto: { fontFamily: fonts.regular, fontSize: 14, color: colors.muted, lineHeight: 21 }, estado: { padding: 20, marginVertical: 8, gap: 12, alignItems: 'center', backgroundColor: 'white', borderRadius: 18, borderWidth: 1, borderColor: colors.border }, estadoTitulo: { fontFamily: fonts.semibold, color: colors.text, fontSize: 19, textAlign: 'center' }, estadoTexto: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 20, textAlign: 'center', color: colors.muted }, avisoPrueba: { fontFamily: fonts.regular, color: colors.button, fontSize: 11 },
  paginas: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 }, campo: { flex: 1, minHeight: 48, padding: 12, borderRadius: 12, borderWidth: 1, borderColor: colors.border, backgroundColor: 'white', fontFamily: fonts.regular, color: colors.text, fontSize: 15 },
  destino: { borderWidth: 1, borderColor: colors.border, padding: 14, borderRadius: 14, flexDirection: 'row', gap: 10, alignItems: 'center', justifyContent: 'space-between' }, destinoActivo: { borderColor: colors.primary, backgroundColor: '#EFFBFA' }, toast: { position: 'absolute', bottom: 16, left: 16, right: 16, borderRadius: 14, backgroundColor: colors.successText, padding: 14, flexDirection: 'row', gap: 8, alignItems: 'center' }, toastTexto: { color: 'white', fontFamily: fonts.semibold, flex: 1 },
});
