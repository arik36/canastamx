import { useEffect, useRef, useState } from "react";
import { useRouter } from "expo-router";
import { ActivityIndicator, FlatList, Keyboard, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { buscarArticulos, CriteriosBusqueda, ErrorAnalitica, esUrlDeSimulador, ResultadoDeBusqueda } from "../../api/analitica";
import { BotonAcceso } from "../../components/ControlesAcceso";
import { EstadoDominio } from "../../components/EstadoDominio";
import { colors, fonts, fontSizes, radii, spacing } from "../../theme/design-system";

type Estado = { tipo: "inicio" } | { tipo: "cargando" } | { tipo: "respuesta"; datos: ResultadoDeBusqueda }
  | { tipo: "error"; error: ErrorAnalitica };

export default function Inicio() {
  const router = useRouter();
  const [termino, setTermino] = useState("");
  const [entidad, setEntidad] = useState("Guanajuato");
  const [estado, setEstado] = useState<Estado>({ tipo: "inicio" });
  const [criterios, setCriterios] = useState<CriteriosBusqueda>();
  const [validacion, setValidacion] = useState("");
  const [simulador, setSimulador] = useState(esUrlDeSimulador);
  const [mostrarDominio, setMostrarDominio] = useState(false);
  const solicitud = useRef<{ numero: number; controller?: AbortController }>({ numero: 0 });
  useEffect(() => () => { solicitud.current.numero++; solicitud.current.controller?.abort(); }, []);

  function editar(campo: "q" | "entidad", valor: string) {
    solicitud.current.numero++;
    solicitud.current.controller?.abort();
    if (campo === "q") setTermino(valor); else setEntidad(valor);
    setEstado({ tipo: "inicio" });
    setCriterios(undefined);
    setValidacion("");
  }

  async function consultar(nuevos: CriteriosBusqueda) {
    if (nuevos.q.trim().length < 2 || !nuevos.entidad.trim()) {
      setValidacion("Escribe al menos dos caracteres y la entidad que deseas consultar."); return;
    }
    Keyboard.dismiss();
    solicitud.current.controller?.abort();
    const numero = ++solicitud.current.numero;
    const controller = new AbortController();
    solicitud.current.controller = controller;
    setValidacion(""); setCriterios(nuevos); setEstado({ tipo: "cargando" });
    try {
      const respuesta = await buscarArticulos(nuevos, controller.signal);
      if (numero !== solicitud.current.numero || controller.signal.aborted) return;
      setSimulador(respuesta.simulador);
      setEstado({ tipo: "respuesta", datos: respuesta.datos });
    } catch (error) {
      if (numero !== solicitud.current.numero || controller.signal.aborted) return;
      setEstado({ tipo: "error", error: error instanceof ErrorAnalitica ? error : new ErrorAnalitica("No pudimos completar la búsqueda.") });
    }
  }

  const cargando = estado.tipo === "cargando";
  const datos = estado.tipo === "respuesta" ? estado.datos : undefined;
  const conDatos = datos?.cobertura === true ? datos : undefined;
  const pagina = criterios?.offset ?? 0;
  return <SafeAreaView style={styles.fondo} edges={["bottom", "left", "right"]}>
    <View style={styles.origen}><Text style={styles.origenTexto}>{simulador ? "Simulador · datos de prueba" : "Interfaz analítica"}</Text></View>
    <FlatList
      data={conDatos?.resultados ?? []}
      keyExtractor={item => JSON.stringify([item.articulo.producto, item.articulo.presentacion])}
      keyboardShouldPersistTaps="handled"
      contentContainerStyle={styles.lista}
      ListHeaderComponent={<View style={styles.formulario}>

        <Text accessibilityRole="header" style={styles.titulo}>Busca artículos</Text>
        <Text style={styles.texto}>Consulta precios típicos en la entidad de tu interés.</Text>
        <Text nativeID="termino-etiqueta" style={styles.etiqueta}>¿Qué artículo buscas?</Text>
        <TextInput accessibilityLabel="Artículo que buscas" accessibilityLabelledBy="termino-etiqueta" style={styles.campo}
          value={termino} onChangeText={valor => editar("q", valor)} placeholder="Ej. leche" placeholderTextColor={colors.muted}
          returnKeyType="search" autoCorrect={false} onSubmitEditing={() => { void consultar({ q: termino, entidad }); }} />
        <Text nativeID="entidad-etiqueta" style={styles.etiqueta}>Entidad federativa</Text>
        <TextInput accessibilityLabel="Entidad federativa" accessibilityLabelledBy="entidad-etiqueta" style={styles.campo}
          value={entidad} onChangeText={valor => editar("entidad", valor)} autoCorrect={false} placeholder="Entidad federativa"
          placeholderTextColor={colors.muted} returnKeyType="search" onSubmitEditing={() => { void consultar({ q: termino, entidad }); }} />
        {validacion ? <Text accessibilityRole="alert" style={styles.texto}>{validacion}</Text> : null}
        <BotonAcceso titulo={cargando ? "Buscando…" : "Buscar artículos"} disabled={cargando} onPress={() => { void consultar({ q: termino, entidad }); }} />
        <View accessibilityLiveRegion="polite" style={styles.estado}>
          {cargando && <><ActivityIndicator color={colors.button} accessibilityLabel="Buscando artículos" /><Text style={styles.texto}>Consultando artículos…</Text></>}
          {estado.tipo === "inicio" && <Text style={styles.texto}>Escribe un artículo y pulsa Buscar artículos.</Text>}
          {conDatos && <>
            <Text style={styles.etiqueta}>Mostrando artículos de {conDatos.entidad}</Text>
            <Text style={styles.texto}>Quincena: {conDatos.quincena}</Text>
            <Text style={styles.texto}>{conDatos.total === 0 ? "Sin resultados" : `${conDatos.total} artículos encontrados`}</Text>
          </>}
          {conDatos?.total === 0 && <View style={styles.aviso}>
            <Text accessibilityRole="header" style={styles.subtitulo}>No encontramos coincidencias</Text>
            <Text style={styles.texto}>No hay artículos para «{criterios?.q.trim()}» en {conDatos.entidad}. Cambia el término o la entidad e intenta otra vez.</Text>
          </View>}
          {datos?.cobertura === false && <View style={styles.aviso}>
            <Text accessibilityRole="header" style={styles.subtitulo}>Entidad sin cobertura</Text>
            <Text style={styles.texto}>Todavía no ofrecemos datos para {datos.entidad}. Es una limitación de cobertura.</Text>
            <Text style={styles.etiqueta}>Entidades con cobertura declarada</Text>
            <Text style={styles.texto}>{datos.entidadesCubiertas.join(", ")}. Elige otra entidad para consultar.</Text>
          </View>}
          {estado.tipo === "error" && <View accessibilityRole="alert" style={styles.aviso}>
            <Text style={styles.subtitulo}>{estado.error.problema?.title ?? "No pudimos consultar"}</Text>
            <Text style={styles.texto}>{estado.error.problema?.detail ?? estado.error.message}</Text>
            {estado.error.problema && <Text style={styles.meta}>HTTP {estado.error.problema.status}</Text>}
            <BotonAcceso titulo="Reintentar" secundario onPress={() => { if (criterios) void consultar(criterios); }} />
          </View>}
        </View>
      </View>}
      renderItem={({ item }) => <View style={styles.tarjeta}>
        <Text style={styles.catalogo}>{item.catalogo}</Text>
        <Text accessibilityRole="header" style={styles.subtitulo}>{item.nombre}</Text>
        <Text style={styles.texto}>{item.articulo.presentacion}</Text>
        <Text style={styles.meta}>Precio típico (mediana)</Text>
        <Text style={styles.precio}>${item.precioTipico.monto} {item.precioTipico.moneda}</Text>
        <Text style={styles.meta}>{conDatos?.entidad} · {conDatos?.quincena}</Text>
        <Text style={styles.meta}>Población: {item.observaciones} observaciones de precio</Text>
      </View>}
      ListFooterComponent={<View style={styles.pie}>
        {conDatos && conDatos.total > 0 && criterios && <>
          <Text style={styles.meta}>Mostrando {pagina + 1}–{pagina + conDatos.resultados.length} de {conDatos.total}</Text>
          <View style={styles.paginacion}>
            <BotonAcceso titulo="Anterior" secundario disabled={cargando || pagina === 0} onPress={() => { void consultar({ ...criterios, offset: Math.max(0, pagina - 20) }); }} />
            <BotonAcceso titulo="Siguiente" secundario disabled={cargando || pagina + conDatos.resultados.length >= conDatos.total} onPress={() => { void consultar({ ...criterios, offset: pagina + 20 }); }} />
          </View>
        </>}
        <Text style={styles.meta}>Precios observados en QQP; no garantizan precio ni existencia en caja.</Text>
        <Pressable accessibilityRole="button" style={styles.enlace} onPress={() => router.push({ pathname: "/articulo/[id]", params: { id: "prueba" } })}>
          <Text style={styles.enlaceTexto}>Probar detalle de artículo</Text>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityState={{ expanded: mostrarDominio }} style={styles.enlace} onPress={() => setMostrarDominio(valor => !valor)}>
          <Text style={styles.enlaceTexto}>{mostrarDominio ? "Ocultar" : "Ver"} estado del servicio de cuenta</Text>
        </Pressable>
        {mostrarDominio && <EstadoDominio />}
      </View>}
    />
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  fondo: { flex: 1, backgroundColor: colors.background },
  lista: { padding: spacing.xl, gap: spacing.lg, paddingBottom: spacing.xxl },
  formulario: { gap: spacing.md },
  origen: { alignSelf: "flex-start", marginHorizontal: spacing.xl, marginTop: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: radii.button, backgroundColor: colors.surface },
  origenTexto: { fontFamily: fonts.semibold, color: colors.button, fontSize: fontSizes.body },
  titulo: { fontFamily: fonts.semibold, color: colors.text, fontSize: fontSizes.title },
  subtitulo: { fontFamily: fonts.semibold, color: colors.text, fontSize: fontSizes.subtitle },
  texto: { fontFamily: fonts.regular, color: colors.text, fontSize: fontSizes.body, lineHeight: 21 },
  etiqueta: { fontFamily: fonts.semibold, color: colors.text, fontSize: fontSizes.body },
  campo: { minHeight: 48, padding: spacing.md, borderWidth: 1, borderColor: colors.muted, borderRadius: radii.button, backgroundColor: colors.surface, fontFamily: fonts.regular, color: colors.text, fontSize: fontSizes.body },
  estado: { gap: spacing.sm, marginVertical: spacing.sm },
  aviso: { backgroundColor: colors.surface, borderRadius: radii.card, padding: spacing.lg, gap: spacing.md },
  tarjeta: { backgroundColor: colors.surface, borderRadius: radii.card, padding: spacing.lg, gap: spacing.sm },
  catalogo: { fontFamily: fonts.semibold, color: colors.button, fontSize: fontSizes.metadata },
  precio: { fontFamily: fonts.semibold, color: colors.text, fontSize: fontSizes.title },
  meta: { fontFamily: fonts.regular, color: colors.muted, fontSize: fontSizes.body, lineHeight: 20 },
  pie: { gap: spacing.lg },
  paginacion: { flexDirection: "row", justifyContent: "space-between", gap: spacing.md },
  enlace: { minHeight: 48, justifyContent: "center", paddingVertical: spacing.sm },
  enlaceTexto: { fontFamily: fonts.semibold, color: colors.button, fontSize: fontSizes.body, textDecorationLine: "underline" },
});
