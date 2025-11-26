import { StyleSheet } from "react-native";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";

// UserSpecification component prompts users to specify their intended use of the app
const UserSpecification = () => {
  return (
    <ThemedView style={styles.container}>
      <ThemedText style={styles.title} title={true}>
        How will you be using ParkPilot?
      </ThemedText>
      <ThemedText>Driver</ThemedText>
      <ThemedText>Parking Operater</ThemedText>
    </ThemedView>
  );
};

export default UserSpecification;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontWeight: "bold",
    fontSize: 18,
  },
});
