import { Link } from "expo-router";
import { StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export default function Busqueda() {
  return (
    <SafeAreaView style={styles.container} edges={["bottom", "left", "right"]}>
      <Text style={styles.title}>Búsqueda</Text>
      <Link href="/canasta" style={styles.link}>
        Ir a mi canasta
      </Link>
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
  link: { fontSize: 18, color: "#125c3e", padding: 12, textDecorationLine: "underline" },
});
