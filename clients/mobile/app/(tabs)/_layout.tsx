import { Tabs, useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, useWindowDimensions, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useSesion } from "../../session/SesionProvider";
import { useCanasta } from "../../canasta/CanastaProvider";
import { useRegion } from "../../components/RegionProvider";
import { colors, fonts } from "../../theme/design-system";

function Encabezado() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const sesion = useSesion();
  const region = useRegion();
  const [ano, mes, parte] = region.quincena.split('-');
  const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const periodo = mes ? `${meses[Number(mes) - 1]} de ${ano} · ${parte === 'Q1' ? '1.ª' : '2.ª'} quincena` : '';
  return <View style={[s.encabezado, { paddingTop: insets.top + 12 }]}>
    <View style={s.fila}>
      <Pressable accessibilityRole="button" accessibilityLabel={`Cambiar entidad: ${region.entidad}`} onPress={region.elegir} style={s.region}>
        <Ionicons name="location-outline" size={20} color="white" /><View style={{ flexShrink: 1 }}><Text style={s.pequeno}>Estado</Text><View style={s.nombreFila}><Text numberOfLines={1} style={s.entidad}>{region.entidad}</Text><Ionicons name="chevron-down" size={12} color="white" /></View></View>
      </Pressable>
      <Pressable accessibilityRole="button" hitSlop={4} accessibilityLabel="Mi cuenta" onPress={() => router.push('/cuenta')} style={s.avatar}>
        {sesion.cuenta ? <Text style={s.inicial}>{sesion.cuenta.correo.charAt(0).toUpperCase()}</Text> : <Ionicons name="person-outline" size={19} color="white" />}
      </Pressable>
    </View>
    <Text numberOfLines={2} style={s.contexto}>{periodo ? `Precios registrados en ${region.entidad} · ${periodo}` : `Artículos y precios registrados en ${region.entidad}`}</Text>
  </View>;
}
export default function TabLayout() {
  const insets = useSafeAreaInsets();
  const { fontScale } = useWindowDimensions();
  const c = useCanasta();
  const cantidad = c.actual?.lineas.length ?? 0;
  const icono = (nombre: React.ComponentProps<typeof Ionicons>['name'], focused: boolean, color: string) => <View style={s.icono}>{focused && <View style={s.indicador} />}<Ionicons name={nombre} color={color} size={23} /></View>;
  return <Tabs initialRouteName="index" backBehavior="initialRoute" screenOptions={{
    header: () => <Encabezado />,
    sceneStyle: { backgroundColor: colors.background }, tabBarLabelPosition: 'below-icon',
    tabBarActiveTintColor: colors.button, tabBarInactiveTintColor: colors.muted,
    tabBarLabelStyle: { fontFamily: fonts.semibold, fontSize: 10, marginTop: 2 },
    tabBarItemStyle: { paddingTop: 8, paddingBottom: 4 },
    tabBarStyle: { backgroundColor: 'white', borderTopColor: colors.border, height: 65 + insets.bottom + Math.max(0, fontScale - 1) * 24, paddingBottom: Math.max(8, insets.bottom), elevation: 0 },
  }}>
    <Tabs.Screen name="index" options={{ title: 'Inicio', tabBarIcon: ({ focused, color }) => icono('search-outline', focused, color) }} />
    <Tabs.Screen name="descubrir" options={{ title: 'Descubrir', tabBarIcon: ({ focused, color }) => icono('grid-outline', focused, color) }} />
    <Tabs.Screen name="canasta" options={{ title: 'Canasta', tabBarBadge: cantidad || undefined, tabBarBadgeStyle: { backgroundColor: colors.primary, color: 'white', fontSize: 9 }, tabBarIcon: ({ focused, color }) => icono('basket-outline', focused, color) }} />
    <Tabs.Screen name="cuenta" options={{ title: 'Cuenta', tabBarIcon: ({ focused, color }) => icono('person-outline', focused, color) }} />
  </Tabs>;
}
const s = StyleSheet.create({
  encabezado: { backgroundColor: colors.primary, paddingHorizontal: 16, paddingBottom: 12, gap: 7 }, fila: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  region: { flexDirection: 'row', gap: 7, minHeight: 44, alignItems: 'center', maxWidth: '82%' }, nombreFila: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  pequeno: { fontFamily: fonts.regular, fontSize: 10, color: '#E0FAF8' }, entidad: { fontFamily: fonts.semibold, color: 'white', fontSize: 14, flexShrink: 1 }, contexto: { fontFamily: fonts.regular, color: '#E0FAF8', fontSize: 10, lineHeight: 14 },
  avatar: { width: 36, height: 36, borderRadius: 18, borderWidth: 1, borderColor: '#91DEDC', backgroundColor: '#4CC7C4', alignItems: 'center', justifyContent: 'center' }, inicial: { fontFamily: fonts.semibold, color: 'white', fontSize: 14 },
  icono: { width: 40, alignItems: 'center' }, indicador: { position: 'absolute', top: -10, width: 28, height: 3, borderRadius: 3, backgroundColor: colors.primary },
});
