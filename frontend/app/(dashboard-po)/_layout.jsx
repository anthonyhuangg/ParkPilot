import { Slot } from "expo-router";
import { View, StyleSheet } from "react-native";

// Layout component for the Parking Operator dashboard
export default function DashboardLayoutPO() {
  return (
    <View style={styles.container}>
      <Slot />
    </View>
  );
}

const styles = StyleSheet.create({ container: { flex: 1 } });
