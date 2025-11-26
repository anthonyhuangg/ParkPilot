import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import PropTypes from "prop-types";

// RoleSelection component for selecting user role
const RoleSelection = ({ role, setRole }) => {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>Select Your Role</Text>

      <View style={styles.row}>
        <TouchableOpacity
          style={[styles.card, role === "dr" && styles.cardSelected]}
          onPress={() => setRole("dr")}
          activeOpacity={0.85}
        >
          <MaterialCommunityIcons
            name="car"
            size={26}
            color={role === "dr" ? "#fff" : "#333"}
          />
          <Text
            style={[
              styles.cardTitle,
              role === "dr" && styles.cardTitleSelected,
            ]}
          >
            Driver
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.card, role === "po" && styles.cardSelected]}
          onPress={() => setRole("po")}
          activeOpacity={0.85}
        >
          <MaterialCommunityIcons
            name="parking"
            size={26}
            color={role === "po" ? "#fff" : "#333"}
          />
          <Text
            style={[
              styles.cardTitle,
              role === "po" && styles.cardTitleSelected,
            ]}
          >
            Parking Operator
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

RoleSelection.propTypes = {
  role: PropTypes.oneOf(["dr", "po"]).isRequired,
  setRole: PropTypes.func.isRequired,
};

export default RoleSelection;

const styles = StyleSheet.create({
  container: {
    width: "100%",
    marginTop: 10,
    marginBottom: 10,
    alignItems: "center",
  },
  label: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 10,
    textAlign: "center",
    color: "#333",
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-evenly",
    width: "100%",
  },
  card: {
    width: "42%",
    backgroundColor: "#f8f8f8",
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.2,
    borderColor: "#ddd",
    elevation: 1,
  },
  cardSelected: {
    backgroundColor: "#5A36C8",
    borderColor: "#5A36C8",
    elevation: 3,
  },
  cardTitle: {
    fontSize: 13.5,
    fontWeight: "600",
    color: "#333",
    marginTop: 5,
  },
  cardTitleSelected: {
    color: "#fff",
  },
});
