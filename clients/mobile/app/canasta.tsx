import { useRouter } from "expo-router";
import { Button, StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function Canasta() {
  const router = useRouter();

  function volverABusqueda() {
    if (router.canGoBack()) {
      router.back();
    } else {
      router.replace("/");
    }
  }

  return (
    <SafeAreaView style={styles.container} edges={["bottom", "left", "right"]}>
      <Text style={styles.title}>Mi canasta</Text>
      <Button title="Volver a búsqueda" onPress={volverABusqueda} color="#125c3e" />
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
  title: { fontSize: 24, fontWeight: "600" },
});
