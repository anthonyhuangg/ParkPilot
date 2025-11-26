import { StyleSheet, View, Dimensions } from "react-native";
import { Button, Card } from "react-native-paper";
import { useRouter } from "expo-router";
import ThemedView from "../components/themed-view";
import Spacer from "../components/spacer";
import ThemedText from "../components/themed-text";

import { COLOURS} from "./theme";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

// Home screen component upon starting the app
const Home = () => {
  const router = useRouter();

  return (
    <ThemedView style={styles.container}>
      <View style={styles.cardWrapper}>
        <Card style={styles.card}>
          <Card.Content>
            <ThemedText style={styles.title}>Welcome to ParkPilot!</ThemedText>
            <ThemedText style={styles.subtitle}>
              Your smart parking assistant
            </ThemedText>

            <Spacer height={12} />

            <View style={styles.buttonContainer}>
              <Button
                mode="contained"
                onPress={() => router.replace("/login")}
                style={styles.primaryButton}
                labelStyle={styles.buttonLabel}
                testID="welcome-login-button"
              >
                Login
              </Button>

              <Button
                mode="contained"
                onPress={() => router.replace("/register")}
                style={styles.secondaryButton}
                labelStyle={styles.buttonLabel}
                testID="welcome-register-button"
              >
                Register
              </Button>
            </View>
          </Card.Content>
        </Card>
      </View>
    </ThemedView>
  );
};

export default Home;

const styles = StyleSheet.create({
  container: {
    flex: 1, // fill screen
    backgroundColor: COLOURS.background,
  },
  cardWrapper: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    width: "100%",
    paddingHorizontal: 20,
  },
  card: {
    width: Math.min(SCREEN_WIDTH * 0.9, 520), // dynamically adapt to screen
    backgroundColor: COLOURS.white,
    borderRadius: 18,
    elevation: 5,
    shadowColor: COLOURS.black,
    shadowOpacity: 0.12,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 4 },
    paddingVertical: 30,
    alignItems: "center",
  },
  title: {
    fontSize: 26,
    fontWeight: "900",
    color: COLOURS.primaryPurple,
    textAlign: "center",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: "#555",
    textAlign: "center",
    marginBottom: 10,
  },
  buttonContainer: {
    width: "100%",
    alignItems: "center",
  },
  primaryButton: {
    backgroundColor: COLOURS.primaryPurple,
    borderRadius: 8,
    width: "85%",
    marginTop: 5,
  },
  secondaryButton: {
    backgroundColor: COLOURS.secondaryPurple,
    borderRadius: 8,
    width: "85%",
    marginTop: 10,
  },
  buttonLabel: {
    fontSize: 16,
    fontWeight: "600",
    color: COLOURS.white,
  },
});
