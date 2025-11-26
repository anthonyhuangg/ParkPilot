import { useState, useEffect } from "react";
import {
  View,
  ScrollView,
  ActivityIndicator,
  Dimensions,
  StyleSheet,
  SafeAreaView,
} from "react-native";
import { Button, DataTable } from "react-native-paper";
import { useRouter, useLocalSearchParams } from "expo-router";
import { DatePickerModal } from "react-native-paper-dates";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import Spacer from "../../components/spacer";
import { LineChart } from "react-native-chart-kit";
import { format } from "date-fns";
import { API_BASE_URL } from "../../config";
import AsyncStorage from "@react-native-async-storage/async-storage";
import {
  COLOURS,
  SPACING,
  TEXT,
  GlobalStyles,
  CardStyles,
  PARKINGLOT,
} from "../../theme";

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

// HistoricOccupancy component displays historical occupancy data for a parking lot
const HistoricOccupancy = () => {
  const router = useRouter();
  const { lot_id } = useLocalSearchParams();
  const [date, setDate] = useState(new Date());
  const [showPicker, setShowPicker] = useState(false);
  const [occupancyData, setOccupancyData] = useState([]);
  const [totalSpots, setTotalSpots] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Fetch total spots summary on component mount
  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/parking/multilot/summary`);
        const json = await res.json();

        const match = json.lots_summary.find(
          (l) => String(l.lot_id) === String(lot_id),
        );

        setTotalSpots(match?.total_spots ?? 40);
      } catch (e) {
        console.error("Failed to load summary:", e);
        setTotalSpots(40);
      }
    };

    if (lot_id) fetchSummary();
  }, [lot_id]);

  // Fetch occupancy data when date or lot_id changes
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError("");

        const token = await AsyncStorage.getItem("access_token");
        const formatted = format(date, "yyyy-MM-dd");

        const res = await fetch(
          `${API_BASE_URL}/api/parking/occupancy/hourly?lot_id=${lot_id}&date=${formatted}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          },
        );

        if (!res.ok)
          throw new Error(`Failed to fetch occupancy data (${res.status})`);

        const data = await res.json();
        if (!Array.isArray(data)) throw new Error("Unexpected API response");

        setOccupancyData(data);
      } catch (err) {
        console.error("Error fetching occupancy data:", err);
        setError("Error loading data.");
        setOccupancyData([]);
      } finally {
        setLoading(false);
      }
    };

    if (lot_id) fetchData();
  }, [date, lot_id]);

  const formattedDate = format(date, "yyyy-MM-dd");

  // Prepare data for the chart
  const times = occupancyData.map((item) => item.time);
  const values = occupancyData.map((item) => {
    const used = item.used ?? 0;
    const total = totalSpots ?? 40;
    return total > 0 ? used / total : 0;
  });

  const displayedLabels = times.map((t, i) => (i % 4 === 0 ? t : ""));
  
  const handleGoBack = () => router.back();

  // Handle date selection from date picker
  const handleConfirmDate = (params) => {
    setShowPicker(false);
    if (params.date) setDate(params.date);
  };

  // Render the HistoricOccupancy component
  return (
    <ThemedView style={GlobalStyles.container}>
      <SafeAreaView style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          {/* Top bar */}
          <View>
            <View style={styles.topBar}>
              <Button
                mode="text"
                icon="chevron-left"
                onPress={handleGoBack}
                style={PARKINGLOT.backButton}
                labelStyle={PARKINGLOT.backButtonLabel}
                testID="ho-back-btn"
              >
                Back
              </Button>

              <Button
                mode="outlined"
                testID="po-histocc-date-picker-btn"
                onPress={() => setShowPicker(true)}
                style={[
                  styles.dateButton,
                  { borderColor: COLOURS.primaryPurple },
                ]}
                labelStyle={[
                  TEXT.primaryButtonLabel,
                  { color: COLOURS.primaryPurple },
                ]}
              >
                {formattedDate}
              </Button>
            </View>
          </View>

          {/* Date picker */}
          <DatePickerModal
            locale="en"
            mode="single"
            visible={showPicker}
            date={date}
            onDismiss={() => setShowPicker(false)}
            onConfirm={handleConfirmDate}
            saveLabel="OK"
            label=" "
          />

          <Spacer height={SPACING.xl} />

          {/* Titles */}
          <ThemedText style={TEXT.heading}>Historic Occupancy</ThemedText>

          <Spacer height={SPACING.xs} />

          <ThemedText style={TEXT.infoText}>
            Occupancy ratio over time for {formattedDate}
          </ThemedText>

          <Spacer height={SPACING.xl} />

          {/* Display states */}
          {loading ? (
            <ActivityIndicator size="large" color={COLOURS.primaryPurple} />
          ) : error ? (
            <ThemedText style={TEXT.errorText}>{error}</ThemedText>
          ) : occupancyData.length === 0 ? (
            <ThemedText>No data available for this date.</ThemedText>
          ) : (
            <>
              {/* Chart card */}
              <View style={[CardStyles.card, { alignItems: "center" }]}>
                <ThemedText
                  style={[TEXT.cardLabel, { color: COLOURS.primaryPurple }]}
                >
                  Occupancy Ratio vs Time
                </ThemedText>

                <Spacer height={SPACING.md} />

                <LineChart
                  data={{
                    labels: displayedLabels,
                    datasets: [{ data: values }],
                  }}
                  width={SCREEN_WIDTH - 60}
                  height={SCREEN_HEIGHT * 0.3}
                  fromZero
                  yAxisInterval={0.2}
                  chartConfig={{
                    backgroundGradientFrom: "#FFFFFF",
                    backgroundGradientTo: "#FFFFFF",
                    color: (opacity = 1) => `rgba(123, 97, 255, ${opacity})`,
                    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                    decimalPlaces: 2,
                    propsForDots: {
                      r: "5",
                      strokeWidth: "2",
                      stroke: COLOURS.secondaryPurple,
                    },
                    propsForBackgroundLines: {
                      strokeDasharray: [],
                    },
                  }}
                  withVerticalLines={true}
                  withHorizontalLines={true}
                  verticalLabelRotation={0}
                />

                <ThemedText style={styles.xAxisLabel}>Time (hh:mm)</ThemedText>
              </View>

              <Spacer height={40} />

              {/* Table card */}
              <View style={CardStyles.card}>
                <ThemedText
                  style={[TEXT.cardLabel, { color: COLOURS.primaryPurple }]}
                  testID="histocc-title"
                >
                  Occupancy Data
                </ThemedText>

                <Spacer height={SPACING.md} />

                <DataTable>
                  <DataTable.Header>
                    <DataTable.Title>Time</DataTable.Title>
                    <DataTable.Title numeric>Ratio</DataTable.Title>
                  </DataTable.Header>

                  {occupancyData.map((item, index) => {
                    const used = item.used ?? 0;
                    const ratio = totalSpots > 0 ? used / totalSpots : 0;

                    return (
                      <DataTable.Row key={index}>
                        <DataTable.Cell>{item.time}</DataTable.Cell>
                        <DataTable.Cell numeric>
                          {ratio.toFixed(2)}
                        </DataTable.Cell>
                      </DataTable.Row>
                    );
                  })}
                </DataTable>
              </View>
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    </ThemedView>
  );
};

export default HistoricOccupancy;

const styles = StyleSheet.create({
  scrollContainer: {
    flexGrow: 1,
    paddingVertical: SPACING.xl,
    paddingHorizontal: SPACING.md,
  },

  topBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },

  dateButton: {
    borderWidth: 1.5,
    backgroundColor: COLOURS.white,
  },

  xAxisLabel: {
    fontSize: 12,
    color: COLOURS.textMedium,
    marginTop: 10,
    fontStyle: "italic",
    textAlign: "center",
  },
});
