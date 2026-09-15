import { useRouter } from "expo-router";
import { Button, StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function BusquedaDeArticulos() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container} edges={["top", "left", "right"]}>
      <Text style={styles.title}>Búsqueda de artículos</Text>
      <Button
        title="Probar detalle de artículo"
        onPress={() =>
          router.push({
            pathname: "/articulo/[id]",
            // Identificador de navegación; no representa un artículo del catálogo.
            params: { id: "prueba" },
          })
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    gap: 16,
    padding: 24,
    backgroundColor: "#ffffff",
  },
  title: { fontSize: 24, fontWeight: "600", textAlign: "center" },
});