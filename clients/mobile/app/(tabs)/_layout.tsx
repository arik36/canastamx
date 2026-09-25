import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { colors, fonts, fontSizes, radii, spacing } from "../../theme/design-system";

export default function TabLayout() {
  const insets = useSafeAreaInsets();

  return (
    <Tabs
      initialRouteName="index"
      backBehavior="initialRoute"
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: colors.background },
        tabBarLabelPosition: "beside-icon",
        tabBarIcon: () => null,
        tabBarIconStyle: { display: "none" },
        tabBarActiveTintColor: colors.text,
        tabBarInactiveTintColor: colors.text,
        tabBarActiveBackgroundColor: colors.primary,
        tabBarInactiveBackgroundColor: colors.background,
        tabBarLabelStyle: {
          fontFamily: fonts.semibold,
          fontSize: fontSizes.body,
        },
        tabBarItemStyle: {
          borderRadius: radii.button,
          marginHorizontal: spacing.xs,
          marginVertical: spacing.sm,
          paddingHorizontal: spacing.xs,
        },
        tabBarStyle: {
          backgroundColor: colors.background,
          borderTopWidth: 0,
          elevation: 0,
          height: 64 + insets.bottom,
          paddingHorizontal: spacing.sm,
        },
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