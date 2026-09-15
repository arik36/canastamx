import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack>
        <Stack.Screen name="index" options={{ title: "Búsqueda" }} />
        <Stack.Screen name="canasta" options={{ title: "Mi canasta" }} />
      </Stack>
    </>
  );
}
