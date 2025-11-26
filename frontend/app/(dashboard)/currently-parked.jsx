import { useEffect, useState } from "react";
import { View, ScrollView, KeyboardAvoidingView, Platform } from "react-native";
import { Button, Card } from "react-native-paper";
import { useRouter } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import Spacer from "../../components/spacer";
import { TEXT, GlobalStyles } from "../../theme";

// Currently Parked screen component
const CurrentlyParked = () => {
  const router = useRouter();
  const [spotLabel, setSpotLabel] = useState(null);

  // Load current parking spot label on component mount
  useEffect(() => {
    const loadSpot = async () => {
      try {
        const storedLabel = await AsyncStorage.getItem("selected_spot_label");
        setSpotLabel(storedLabel);
      } catch (err) {
        console.error("Failed to load current spot", err);
      }
    };
    loadSpot();
  }, []);

  // Handle exit button press
  const handleExit = async () => {
    try {
      const lotIdStr = await AsyncStorage.getItem("selected_lot_id");
      const currentNodeStr = await AsyncStorage.getItem("selected_spot_id");

      const lotId = lotIdStr ? Number(lotIdStr) : null;
      const currentNode = currentNodeStr ? Number(currentNodeStr) : null;

      if (!lotId || !currentNode) {
        router.replace("/(dashboard)/overview");
        return;
      }

      router.push(
        `/navigation?mode=exit&lot_id=${lotId}&current=${currentNode}`,
      );
    } catch (err) {
      console.error("Exit navigation error:", err);
      router.replace("/(dashboard)/overview");
    }
  };

  return (
    <ThemedView style={GlobalStyles.screen}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={GlobalStyles.keyboardFill}
      >
        <ScrollView
          contentContainerStyle={GlobalStyles.centeredScroll}
          showsVerticalScrollIndicator={false}
        >
          <Card style={GlobalStyles.cardLarge}>
            <Card.Content style={GlobalStyles.cardContentCentered}>
              <ThemedText style={TEXT.header}>
                {spotLabel ? `Currently Parked at ${spotLabel}` : "Not Parked"}
              </ThemedText>
              <Spacer height={8} />

              <ThemedText style={TEXT.infoText}>
                Select Exit to Leave Parking Spot
              </ThemedText>
              <Spacer height={25} />
              <View style={{ alignItems: "center", width: "100%" }}>
                <Button
                  mode="contained"
                  onPress={handleExit}
                  style={GlobalStyles.primaryButton}
                  labelStyle={TEXT.primaryButtonLabel}
                  testID="exit-parking-btn"
                >
                  Exit
                </Button>
              </View>
            </Card.Content>
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </ThemedView>
  );
};

export default CurrentlyParked;
