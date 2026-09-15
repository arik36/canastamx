import { Tabs } from "expo-router";

export default function TabLayout() {
  return (
    <Tabs
      initialRouteName="index"
      backBehavior="initialRoute"
      screenOptions={{
        headerShown: false,
        tabBarLabelPosition: "beside-icon",
        tabBarIcon: () => null,
        tabBarIconStyle: { display: "none" },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: "Búsqueda de artículos", tabBarLabel: "Búsqueda" }}
      />
      <Tabs.Screen name="canasta" options={{ title: "Mi canasta" }} />
      <Tabs.Screen name="alertas" options={{ title: "Alertas" }} />
    </Tabs>
  );
}