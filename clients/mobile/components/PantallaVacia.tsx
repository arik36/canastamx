import type { ReactNode } from "react";
import { StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors, fonts, fontSizes, spacing } from "../theme/design-system";

type Props = {
  title: string;
  children?: ReactNode;
  withHeader?: boolean;
};

export function PantallaVacia({ title, children, withHeader = false }: Props) {
  return (
    <SafeAreaView
      style={styles.container}
      edges={withHeader ? ["bottom", "left", "right"] : ["top", "left", "right"]}
    >
      <Text accessibilityRole="header" style={styles.title}>{title}</Text>
      {children}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    gap: spacing.xl,
    padding: spacing.xxl,
    backgroundColor: colors.background,
  },
  title: {
    fontFamily: fonts.semibold,
    fontSize: fontSizes.title,
    lineHeight: 32,
    color: colors.text,
    textAlign: "center",
  },
});