import { useEffect, useState } from "react";
import { View, ActivityIndicator } from "react-native";
import { Card } from "react-native-paper";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import Spacer from "../../components/spacer";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { API_BASE_URL } from "../../config";
import { SPACING, TEXT, GlobalStyles } from "../../theme";

// Carbon impact screen component
const Carbon = () => {
  const [carbonSaved, setCarbonSaved] = useState(null);
  const [moneySaved, setMoneySaved] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch carbon data on component mount
  useEffect(() => {
    const fetchCarbonData = async () => {
      try {
        setLoading(true);

        const token = await AsyncStorage.getItem("access_token");
        const userId = await AsyncStorage.getItem("user_id");

        if (!userId) {
          setCarbonSaved(0);
          setMoneySaved(0);
          return;
        }

        const res = await fetch(`${API_BASE_URL}/carbon/user/${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        const data = await res.json();
        setCarbonSaved(data.total_co2_saved_kg ?? 0);
        setMoneySaved(data.total_money_saved_usd ?? 0);
      } catch (err) {
        console.error("Error fetching carbon:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchCarbonData();
  }, []);

  // Show loading indicator while fetching data
  if (loading) {
    return (
      <ThemedView style={GlobalStyles.screenCentered}>
        <ActivityIndicator size="large" />
      </ThemedView>
    );
  }

  return (
    <ThemedView style={GlobalStyles.screenCentered}>
      <ThemedText
        variant="titleLarge"
        style={TEXT.header}
        testID="driver-carbon-title"
      >
        Your Carbon Impact
      </ThemedText>

      <Spacer size={SPACING.xl} />

      <View style={{ width: "90%", alignItems: "center" }}>
        
        {/* Carbon Saved */}
        <Card style={GlobalStyles.cardLarge} mode="elevated">
          <Card.Content style={GlobalStyles.cardContentCentered}>
            <ThemedText variant="titleMedium" style={TEXT.cardLabel}>
              Total Carbon Saved
            </ThemedText>

            <ThemedText variant="displayMedium" style={TEXT.valueCarbon}>
              {carbonSaved.toFixed(2)} kg CO₂
            </ThemedText>

            <ThemedText variant="bodyMedium" style={TEXT.cardDescription}>
              Reduced emissions through smarter parking.
            </ThemedText>
          </Card.Content>
        </Card>

        {/* Money Saved */}
        <Card style={[GlobalStyles.cardLarge, { marginTop: SPACING.lg }]}>
          <Card.Content style={GlobalStyles.cardContentCentered}>
            <ThemedText variant="titleMedium" style={TEXT.cardLabel}>
              Estimated Money Saved
            </ThemedText>

            <ThemedText variant="displayMedium" style={TEXT.valueMoney}>
              ${moneySaved.toFixed(2)}
            </ThemedText>

            <ThemedText variant="bodyMedium" style={TEXT.cardDescription}>
              Based on reduced fuel use and travel time.
            </ThemedText>
          </Card.Content>
        </Card>
      </View>
    </ThemedView>
  );
};

export default Carbon;
