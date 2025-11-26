import { useEffect, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { View, useWindowDimensions, ActivityIndicator } from "react-native";
import * as Location from "expo-location";
import { Button, Card } from "react-native-paper";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import Spacer from "../../components/spacer";
import { useRouter } from "expo-router";
import { API_BASE_URL } from "../../config";
import { COLOURS, SPACING, TEXT, GlobalStyles } from "../../theme";

// Overview screen component for the driver dashboard
const Overview = () => {
  const router = useRouter();
  const { width, height } = useWindowDimensions();
  const [userName, setUserName] = useState("");
  const [nearestLot, setNearestLot] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch user name
  useEffect(() => {
    const loadName = async () => {
      const stored = await AsyncStorage.getItem("user_name");
      if (stored) setUserName(stored);
    };
    loadName();
  }, []);

  // Determine nearest lot
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);

        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== "granted") return;

        const pos = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.High,
        });

        const res = await fetch(
          `${API_BASE_URL}/api/parking/nearest?longitude=${pos.coords.longitude}&latitude=${pos.coords.latitude}`,
        );

        if (!res.ok) throw new Error("Failed nearest lot request");

        const lot = await res.json();
        setNearestLot(lot);
      } catch (err) {
        console.error(err);
        setNearestLot(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleParkingSpotSelect = () => {
    if (!nearestLot) return;
    router.push(`/parking-lot?lot_id=${nearestLot.lot_id}`);
  };

  // Determine the entrance the driver is closest to
  const getEntranceIdA = async (lotId) => {
    const res = await fetch(`${API_BASE_URL}/api/parking/${lotId}/nodes`);
    if (!res.ok) throw new Error("Failed to fetch nodes");

    const data = await res.json();

    const entrance = data.nodes.find(
      (n) =>
        n.type === "CAR_ENTRANCE" &&
        n.label?.toLowerCase() === "car entrance a",
    );

    if (!entrance) throw new Error("Entrance A not found");

    return entrance.id;
  };

  // Handle the spot closest to entrance button
  const handleSpotClosestEntrance = async () => {
    if (!nearestLot) return;

    try {
      const lotId = nearestLot.lot_id;
      const ttl = 15; // reservation in minutes
      const entranceId = await getEntranceIdA(lotId);

      const resSpot = await fetch(
        `${API_BASE_URL}/api/parking/${lotId}/find-spot?entrance_id=${entranceId}`,
      );

      if (!resSpot.ok) throw new Error("Failed to fetch closest spot");

      const data = await resSpot.json();
      const closestSpotId = data.spot_node_id;

      if (!closestSpotId || isNaN(closestSpotId)) {
        console.error("Invalid closest spot ID:", closestSpotId);
        return;
      }

      const mapRes = await fetch(`${API_BASE_URL}/api/parking/${lotId}/nodes`);
      if (!mapRes.ok) throw new Error("Failed to fetch parking lot map");
      const mapData = await mapRes.json();

      const node = mapData.nodes.find((n) => n.id === closestSpotId);
      const closestSpotLabel = node?.label ?? `Spot ${closestSpotId}`;

      await AsyncStorage.setItem("selected_spot_id", closestSpotId.toString());
      await AsyncStorage.setItem("selected_spot_label", closestSpotLabel);
      await AsyncStorage.setItem("selected_lot_id", lotId.toString());

      const resReserve = await fetch(
        `${API_BASE_URL}/api/parking/${lotId}/update_status?node_id=${closestSpotId}&status=RESERVED&ttl=${ttl}`,
        { method: "POST", headers: { "Content-Type": "application/json" } },
      );

      if (!resReserve.ok) throw new Error("Failed to reserve spot");
      const reserveData = await resReserve.json();
      console.log("Spot reserved successfully:", reserveData);

      router.push(
        `/navigation?lot_id=${lotId}&start=${entranceId}&end=${closestSpotId}`,
      );
    } catch (err) {
      console.error("Error handling closest spot:", err);
    }
  };

  const cardWidth = Math.min(width * 0.9, 420);
  const cardPadding = Math.min(height * 0.03, 30);

  return (
    <ThemedView style={GlobalStyles.screenCentered}>
      <Card
        style={[
          GlobalStyles.cardLarge,
          { width: cardWidth, paddingVertical: cardPadding },
        ]}
      >
        <Card.Content style={GlobalStyles.cardContentCentered}>
          <ThemedText style={TEXT.overviewWelcome}>
            Welcome{" "}
            <ThemedText style={TEXT.userName}>
              {userName || "Loading..."}
            </ThemedText>
          </ThemedText>

          <Spacer height={25} />

          {loading ? (
            <View style={{ alignItems: "center" }}>
              <ActivityIndicator size="small" />
              <ThemedText style={TEXT.infoText}>
                Finding the nearest parking lot…
              </ThemedText>
            </View>
          ) : nearestLot ? (
            <>
              <ThemedText style={TEXT.infoText}>
                You are closest to{" "}
                <ThemedText style={TEXT.highlightPurple}>
                  {nearestLot.lot_name}
                </ThemedText>
              </ThemedText>

              <ThemedText style={TEXT.infoText}>
                <ThemedText style={TEXT.highlightPurple}>
                  {nearestLot.num_available}
                </ThemedText>{" "}
                of {nearestLot.total_spots} spots available
              </ThemedText>
            </>
          ) : (
            <ThemedText style={TEXT.infoText}>
              Couldn’t determine your nearest lot.
            </ThemedText>
          )}

          <Spacer height={35} />

          <ThemedText style={TEXT.subtitleCentered}>
            Please select a parking option:
          </ThemedText>

          <View style={GlobalStyles.buttonColumnCenter}>
            <Button
              mode="contained"
              onPress={handleParkingSpotSelect}
              style={GlobalStyles.primaryButton}
              labelStyle={TEXT.primaryButtonLabel}
            >
              Select a Parking Spot
            </Button>

            <Button
              mode="contained"
              onPress={handleSpotClosestEntrance}
              buttonColor={COLOURS.secondaryPurple}
              style={GlobalStyles.secondaryButton}
              labelStyle={TEXT.primaryButtonLabel}
            >
              Spot Closest to Entrance
            </Button>
          </View>
        </Card.Content>
      </Card>
    </ThemedView>
  );
};

export default Overview;
