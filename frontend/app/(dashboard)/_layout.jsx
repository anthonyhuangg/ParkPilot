import { Slot } from "expo-router";
import { View, StyleSheet } from "react-native";
import { GlobalStyles } from "../../theme";

// Dashboard layout component
export default function DashboardLayout() {
  return (
    <View style={GlobalStyles.screen}>
      <Slot />
    </View>
  );
}
