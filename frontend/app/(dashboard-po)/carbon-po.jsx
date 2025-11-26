import { useEffect, useState, useCallback } from "react";
import {
  StyleSheet,
  View,
  ScrollView,
  ActivityIndicator,
  SafeAreaView,
  Modal,
  TouchableOpacity,
} from "react-native";
import { Button, Card, Divider } from "react-native-paper";
import { DatePickerModal, registerTranslation } from "react-native-paper-dates";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import Spacer from "../../components/spacer";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { format } from "date-fns";
import { API_BASE_URL } from "../../config";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { COLOURS, TEXT, GlobalStyles, CardStyles } from "../../theme";

// Register English translations for the date picker
registerTranslation("en", {
  save: "Save",
  selectSingle: "Select date",
  selectMultiple: "Select dates",
  selectRange: "Select period",
  notAccordingToDateFormat: (inputFormat) =>
    `Date format must be ${inputFormat}`,
  mustBeHigherThan: (minDate) => `Must be later than ${minDate}`,
  mustBeLowerThan: (maxDate) => `Must be earlier than ${maxDate}`,
  mustBeBetween: (minDate, maxDate) =>
    `Must be between ${minDate} - ${maxDate}`,
  typeInDate: "Type in date",
  close: "Close",
  confirm: "OK",
  cancel: "Cancel",
  previous: "Previous",
  next: "Next",
});

// Helper function to truncate long driver names
const truncateName = (name) => {
  if (!name) return "";
  return name.length > 10 ? name.substring(0, 10) + "..." : name;
};

// CarbonPO component displays carbon savings data for parking operators
const CarbonPO = () => {
  const [lots, setLots] = useState([]);

  // Default: lot_id = 1, name fetched from backend
  const [selectedLot, setSelectedLot] = useState({
    lot_id: 1,
    lot_name: null,
  });

  const [date, setDate] = useState(new Date());
  const [showPicker, setShowPicker] = useState(false);
  const [showLotModal, setShowLotModal] = useState(false);
  const [contributors, setContributors] = useState([]);
  const [totalSavedCarbon, setTotalSavedCarbon] = useState(0);
  const [totalSavedMoney, setTotalSavedMoney] = useState(0);
  const [loading, setLoading] = useState(false);

  const formattedDate = format(date, "yyyy-MM-dd");

  // Function to fetch carbon data for the selected lot and date
  const fetchCarbonData = useCallback(
    async (lotId) => {
      try {
        setLoading(true);
        const token = await AsyncStorage.getItem("access_token");

        const response = await fetch(
          `${API_BASE_URL}/carbon/operator/lot/${lotId}?date=${formattedDate}`,
          { headers: { Authorization: `Bearer ${token}` } },
        );

        if (!response.ok)
          throw new Error("Failed to fetch operator carbon data");

        const data = await response.json();

        const contributorsList =
          data.contributors?.map((c) => ({
            driver_name: c.user_name,
            carbon_saved: c.total_co2_saved_kg,
          })) ?? [];

        setContributors(contributorsList);
        setTotalSavedCarbon(data.total_co2_saved_kg || 0);
        setTotalSavedMoney(data.total_money_saved_usd || 0);
      } catch (err) {
        console.error("Error fetching operator carbon:", err);

        // Reset data on error
        setContributors([]);
        setTotalSavedCarbon(0);
        setTotalSavedMoney(0);
      } finally {
        setLoading(false);
      }
    },
    [formattedDate],
  );

  // Function to handle exporting carbon data as CSV
  const handleExportCSV = async () => {
    try {
      const lotName = selectedLot?.lot_name || "Unknown Lot";

      let csv =
        "\uFEFFParking Lot,Date,Driver Name,Carbon Saved (kg),Estimated Money Saved (USD),Total Carbon Saved (kg)\n";

      contributors.forEach((c) => {
        csv += `${lotName},${formattedDate},${c.driver_name},${c.carbon_saved.toFixed(
          2,
        )},${totalSavedMoney.toFixed(2)},${totalSavedCarbon.toFixed(2)}\n`;
      });

      const fileUri =
        FileSystem.documentDirectory + `carbon_report_${Date.now()}.csv`;

      await FileSystem.writeAsStringAsync(fileUri, csv, {
        encoding: FileSystem.EncodingType.UTF8,
      });

      await Sharing.shareAsync(fileUri, {
        mimeType: "text/csv",
        dialogTitle: "Export Carbon Report",
        UTI: "public.comma-separated-values-text",
      });
    } catch (error) {
      console.error("CSV export error:", error);
      alert("Failed to export CSV");
    }
  };

  // Fetch parking lots on component mount
  useEffect(() => {
    const fetchLots = async () => {
      try {
        const token = await AsyncStorage.getItem("access_token");
        const res = await fetch(
          `${API_BASE_URL}/api/parking/multilot/summary`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );

        const data = await res.json();
        setLots(data.lots_summary ?? []);

        if (data.lots_summary?.length) {
          const backendLot = data.lots_summary.find(
            (lot) => lot.lot_id === selectedLot.lot_id,
          );
          if (backendLot) setSelectedLot(backendLot);
        }
      } catch (err) {
        console.error("Error loading lots:", err);
      }
    };

    fetchLots();
  }, [selectedLot.lot_id]);

  // Fetch carbon data when selected lot or date changes
  useEffect(() => {
    if (selectedLot?.lot_id) {
      fetchCarbonData(selectedLot.lot_id);
    }
  }, [selectedLot, date, fetchCarbonData]);

  // Handle date selection from date picker
  const handleConfirmDate = (params) => {
    setShowPicker(false);
    if (params.date) setDate(params.date);
  };

  // Handle lot selection from modal
  const handleSelectLot = (lot) => {
    setSelectedLot(lot);
    setShowLotModal(false);
  };

  // Render the CarbonPO component
  return (
    <ThemedView style={GlobalStyles.container}>
      <SafeAreaView style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={GlobalStyles.scrollContainer}>
          
          {/* Top bar with lot selection & date picker */}
          <View style={styles.topBarWrapper}>          
            <Button
              mode="outlined"
              onPress={() => setShowLotModal(true)}
              testID="show-lot-option-modal-btn"
              style={GlobalStyles.lotButton}
              labelStyle={[
                GlobalStyles.topButtonLabel,
                { color: COLOURS.secondaryPurple },
              ]}
            >
              {selectedLot?.lot_name ?? "Loading lot..."}
            </Button>
            <View style={styles.rowBelow}>
              <Button
                mode="contained"
                style={[
                  styles.topButton,
                  { backgroundColor: COLOURS.secondaryPurple },
                ]}
                labelStyle={styles.topButtonLabel}
                onPress={handleExportCSV}
              >
                Export CSV
              </Button>
              <Button
                mode="outlined"
                onPress={() => setShowPicker(true)}
                testID="po-carbon-date-picker-btn"
                style={styles.topButton}
                labelStyle={[
                  styles.topButtonLabel,
                  { color: COLOURS.secondaryPurple },
                ]}
              >
                {formattedDate}
              </Button>
            </View>
          </View>

          {/* Date picker modal & lot selection modal */}
          <DatePickerModal
            locale="en"
            mode="single"
            testID="po-carbon-date-picker-modal"
            visible={showPicker}
            onDismiss={() => setShowPicker(false)}
            date={date}
            onConfirm={handleConfirmDate}
            saveLabel="OK"
            label=" "
          />
          <Modal
            transparent
            visible={showLotModal}
            animationType="slide"
            onRequestClose={() => setShowLotModal(false)}
          >
            <View style={CardStyles.modalOverlay}>
              <View style={CardStyles.modalCard}>
                <ThemedText style={TEXT.modalTitle}>
                  Select Parking Lot
                </ThemedText>
                <ScrollView style={{ maxHeight: 350 }}>
                  {lots.map((lot, i) => (
                    <TouchableOpacity
                      key={lot.lot_id}
                      style={CardStyles.modalOption}
                      onPress={() => handleSelectLot(lot)}
                      testID={`lot-option-${lot.lot_id}`}
                    >
                      <ThemedText style={TEXT.modalOptionText}>
                        {lot.lot_name}
                      </ThemedText>
                      {i !== lots.length - 1 && <Divider />}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
                <Spacer height={10} />
                <Button
                  textColor={COLOURS.secondaryPurple}
                  style={CardStyles.modalCloseBtn}
                  onPress={() => setShowLotModal(false)}
                >
                  Cancel
                </Button>
              </View>
            </View>
          </Modal>
          <Spacer height={30} />

          {/* Header */}
          <ThemedText style={TEXT.heading} testID="po-carbon-title" >Carbon Savings Dashboard</ThemedText>

          <Spacer height={8} />
          <ThemedText style={styles.subText}>
            {selectedLot?.lot_name ?? "Loading..."} — {formattedDate}
          </ThemedText>
          <Spacer height={25} />
          
          {/* Contributors card */}
          <Card style={CardStyles.card}>
            <Card.Content>
              <ThemedText style={TEXT.sectionTitleCarbon}>
                Contributors
              </ThemedText>
              <Spacer height={10} />
              {loading ? (
                <ActivityIndicator
                  size="large"
                  color={COLOURS.secondaryPurple}
                />
              ) : contributors.length === 0 ? (
                <ThemedText style={{ textAlign: "center", opacity: 0.6 }}>
                  No contributors for this date.
                </ThemedText>
              ) : (
                contributors.map((c, i) => (
                  <View key={i} style={GlobalStyles.tableRow}>
                    <View style={GlobalStyles.tableColLeft}>
                      <ThemedText style={TEXT.driverName}>
                        {truncateName(c.driver_name)}
                      </ThemedText>
                    </View>
                    <View style={GlobalStyles.tableColRight}>
                      <ThemedText style={TEXT.driverValue}>
                        {c.carbon_saved.toFixed(2)} kg CO₂
                      </ThemedText>
                    </View>
                  </View>
                ))
              )}
            </Card.Content>
          </Card>
          <Spacer height={25} />

          {/* Metrcs card */}
          <Card style={CardStyles.card}>
            <Card.Content style={{ alignItems: "center" }}>
              <ThemedText style={TEXT.sectionTitleCarbon}>
                Total Saved ({formattedDate})
              </ThemedText>
              <Spacer height={15} />
              <View style={styles.metric}>
                <ThemedText style={styles.metricLabel}>
                  Estimated Money Saved
                </ThemedText>
                <ThemedText style={TEXT.valueMoney}>
                  ${totalSavedMoney.toFixed(2)}
                </ThemedText>
              </View>
              <Spacer height={10} />
              <View style={styles.metric}>
                <ThemedText style={styles.metricLabel}>
                  Total Carbon Saved
                </ThemedText>
                <ThemedText style={TEXT.valueCarbon}>
                  {totalSavedCarbon.toFixed(2)} kg CO₂
                </ThemedText>
              </View>
            </Card.Content>
          </Card>
        </ScrollView>
      </SafeAreaView>
    </ThemedView>
  );
};

export default CarbonPO;

const styles = StyleSheet.create({
  topBarWrapper: {
    marginTop: 40,
    width: "100%",
    marginBottom: 15,
    alignItems: "center",
  },
  rowBelow: {
    flexDirection: "row",
    justifyContent: "space-between",
    width: "100%",
    gap: 10,
  },
  topButton: {
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: COLOURS.secondaryPurple,
    backgroundColor: "white",
    flex: 1,
  },

  metric: { alignItems: "center" },
  metricLabel: { fontSize: 15, opacity: 0.8, marginBottom: 4 },
});
