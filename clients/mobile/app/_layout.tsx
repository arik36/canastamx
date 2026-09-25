import { Inter_400Regular } from "@expo-google-fonts/inter/400Regular";
import { Inter_600SemiBold } from "@expo-google-fonts/inter/600SemiBold";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { StyleSheet, View } from "react-native";
import { colors, fonts, fontSizes } from "../theme/design-system";

export const unstable_settings = {
  initialRouteName: "(tabs)",
};

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
    <>
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
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="articulo/[id]"
          options={{ title: "", headerBackTitle: "Búsqueda" }}
        />
      </Stack>
    </>
  );
}

const styles = StyleSheet.create({
  loading: { flex: 1, backgroundColor: colors.background },
});