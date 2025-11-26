import { useState, useEffect } from "react";
import { StyleSheet, FlatList, ActivityIndicator, View } from "react-native";
import { Searchbar, Card } from "react-native-paper";
import { useRouter } from "expo-router";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import Spacer from "../../components/spacer";
import { API_BASE_URL } from "../../config";
import { COLOURS } from "../../theme/colours";
import { CardStyles, GlobalStyles, TEXT } from "../../theme";

const OverviewPO = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [lots, setLots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch summary of parking lots
  useEffect(() => {
    const fetchLots = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`${API_BASE_URL}/api/parking/multilot/summary`);
        if (!res.ok) throw new Error("Failed to fetch parking data");

        const data = await res.json();
        setLots(data.lots_summary ?? []);
      } catch (err) {
        console.error("Error fetching lots:", err);
        setError("Error loading parking data. Try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchLots();
  }, []);

  // Filter lots based on search query
  const filteredLots = lots.filter(
    (lot) =>
      lot.lot_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      lot.location.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // Handle parking lot selection
  const handleParkingLotSelect = (lotId) => {
    router.push(`/parking-lot-po?lot_id=${lotId}`);
  };

  // Render each parking lot item
  const renderLot = ({ item }) => (
    <Card
      style={CardStyles.cardpo}
      onPress={() => handleParkingLotSelect(item.lot_id)}
      testID={`lot-item-${item.lot_id}`}
    >
      <Card.Content>
        <ThemedText
          style={TEXT.garageName}
          numberOfLines={1}
          ellipsizeMode="tail"
        >
          {item.lot_name}
        </ThemedText>
        <ThemedText
          style={TEXT.garageLocation}
          numberOfLines={1}
          ellipsizeMode="tail"
        >
          {item.location}
        </ThemedText>

        <ThemedText style={TEXT.garageSpots}>
          {item.num_available} of {item.total_spots} spots available
        </ThemedText>
      </Card.Content>
    </Card>
  );

  return (
    <ThemedView style={GlobalStyles.container}>
      <Spacer height={10} />

      <Searchbar
        placeholder="Search for a parking area..."
        onChangeText={setSearchQuery}
        value={searchQuery}
        style={GlobalStyles.searchBar}
        icon="magnify"
        testID="searchbar"
      />

      <Spacer height={10} />

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLOURS.primaryPurple} />
        </View>
      ) : error ? (
        <ThemedText style={TEXT.errorText}>{error}</ThemedText>
      ) : (
        <FlatList
          data={filteredLots}
          keyExtractor={(item) => item.lot_id.toString()}
          renderItem={renderLot}
          contentContainerStyle={GlobalStyles.listContainer}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <ThemedText style={styles.noResults}>
              No parking lots found.
            </ThemedText>
          }
        />
      )}
    </ThemedView>
  );
};

export default OverviewPO;

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  noResults: {
    textAlign: "center",
    color: "#666",
    marginTop: 30,
  },
});
