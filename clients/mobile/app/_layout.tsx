import { Inter_400Regular } from "@expo-google-fonts/inter/400Regular";
import { Inter_600SemiBold } from "@expo-google-fonts/inter/600SemiBold";
import { useFonts } from "expo-font";
import { Stack, usePathname, useRootNavigationState, useRouter } from "expo-router";
import { useEffect, useRef } from "react";
import { SesionProvider, useSesion } from "../session/SesionProvider";
import { CanastaProvider } from "../canasta/CanastaProvider";
import { RegionProvider } from "../components/RegionProvider";
import { StatusBar } from "expo-status-bar";
import { StyleSheet, View } from "react-native";
import { colors, fonts, fontSizes } from "../theme/design-system";

export const unstable_settings = {
  initialRouteName: "(tabs)",
};

function EntradaInicial() {
  const { estado } = useSesion();
  const ruta = usePathname();
  const navegacion = useRootNavigationState();
  const router = useRouter();
  const revisado = useRef(false);
  useEffect(() => {
    if (revisado.current || !navegacion?.key || estado === "cargando") return;
    revisado.current = true;
    if (estado === "invitado" && ruta === "/") router.replace("/acceso");
  }, [estado, ruta, navegacion?.key, router]);
  return null;
}

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Inter_400Regular,
    Inter_600SemiBold,
  });

  if (fontError) {
    throw fontError;
  }

  // Evita mostrar las pantallas con la tipografía predeterminada mientras carga Inter.
  if (!fontsLoaded) {
    return <View style={styles.loading} />;
  }

  return (
    <SesionProvider>
      <CanastaProvider><RegionProvider>
      <EntradaInicial />
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          contentStyle: { backgroundColor: colors.background },
          headerStyle: { backgroundColor: colors.background },
          headerTintColor: colors.text,
          headerShadowVisible: false,
          headerTitleStyle: {
            fontFamily: fonts.semibold,
            fontSize: fontSizes.subtitle,
          },
          headerBackTitleStyle: {
            fontFamily: fonts.regular,
            fontSize: fontSizes.body,
          },
        }}
      >
        <Stack.Screen name="acceso" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="alertas"
          options={{ title: "", headerBackTitle: "Volver" }}
        />
        <Stack.Screen
          name="articulo/[id]"
          options={{ headerShown: false }}
        />
      </Stack>
      </RegionProvider></CanastaProvider>
    </SesionProvider>
  );
}

const styles = StyleSheet.create({
  loading: { flex: 1, backgroundColor: colors.background },
});
