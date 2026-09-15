import { StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function DetalleDeArticulo() {
  return (
    <SafeAreaView style={styles.container} edges={["bottom", "left", "right"]}>
      <Text style={styles.title}>Detalle de artículo</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    backgroundColor: "#ffffff",
  },
  title: { fontSize: 24, fontWeight: "600", textAlign: "center" },
});