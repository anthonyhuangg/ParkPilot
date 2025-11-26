import { useEffect, useState } from "react";
import {
  StyleSheet,
  View,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { TextInput } from "@react-native-material/core";
import { Button, Card } from "react-native-paper";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import { API_BASE_URL } from "../../config";
import { TEXT, GlobalStyles, CardStyles } from "../../theme";

// Profile component allows users to view and update their profile information
const Profile = () => {
  const router = useRouter();
  const [userId, setUserId] = useState(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [carReg, setCarReg] = useState("");
  const [role, setRole] = useState("");

  const [storedName, setStoredName] = useState("");
  const [storedEmail, setStoredEmail] = useState("");
  const [storedCarReg, setStoredCarReg] = useState("");
  const [storedRole, setStoredRole] = useState("");

  // Track profile edits, validate email input, and display role in a human-readable format
  const [isChanged, setIsChanged] = useState(false);
  const [emailInvalid, setEmailInvalid] = useState(false);
  const displayRole =
    role === "dr" ? "Driver" : role === "po" ? "Parking Operator" : "";

  // Email regex check (LIVE validation)
  const validateEmail = (text) => {
    setEmail(text);
    setEmailInvalid(!text.includes("@"));
  };

  // Load user data from storage
  useEffect(() => {
    const loadUserData = async () => {
      try {
        const id = await AsyncStorage.getItem("user_id");
        const sn = await AsyncStorage.getItem("user_name");
        const se = await AsyncStorage.getItem("user_email");
        const scr = await AsyncStorage.getItem("user_car_reg");
        const sr = await AsyncStorage.getItem("user_role");

        setUserId(Number(id));
        setName(sn || "");
        setEmail(se || "");
        setCarReg(scr || "");
        setRole(sr || "dr");

        setStoredName(sn || "");
        setStoredEmail(se || "");
        setStoredCarReg(scr || "");
        setStoredRole(sr || "dr");
      } catch (err) {
        console.error("Failed to load user data", err);
        Alert.alert("Error", "Could not load profile information.");
      }
    };

    loadUserData();
  }, []);

  // Enable Save button when changes exist AND email valid
  useEffect(() => {
    const changed =
      name !== storedName ||
      email !== storedEmail ||
      carReg !== storedCarReg ||
      role !== storedRole;

    setIsChanged(changed && !emailInvalid);
  }, [
    name,
    email,
    carReg,
    role,
    storedName,
    storedEmail,
    storedCarReg,
    storedRole,
    emailInvalid,
  ]);

  // Handle saving updated profile information
  const handleSave = async () => {
    if (emailInvalid) {
      Alert.alert("Invalid Email", "Please enter a valid email address.");
      return;
    }

    try {
      const payload = {
        name,
        email,
        role,
        car_reg: carReg,
      };

      const res = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to update user profile.");
      }

      const data = await res.json();
      console.log("Profile updated:", data);

      await AsyncStorage.setItem("user_name", data.name);
      await AsyncStorage.setItem("user_email", data.email);
      await AsyncStorage.setItem("user_car_reg", data.car_reg);

      setStoredName(data.name);
      setStoredEmail(data.email);
      setStoredCarReg(data.car_reg);

      setIsChanged(false);
      Alert.alert("Success", "Profile updated successfully!");
    } catch (err) {
      console.error("Error saving profile:", err);
      Alert.alert("Error", err.message);
    }
  };

  // Handle user logout
  const handleLogout = async () => {
    await AsyncStorage.multiRemove([
      "access_token",
      "user_role",
      "user_name",
      "user_email",
      "user_car_reg",
      "user_id",
    ]);
    router.replace("/");
  };

  return (
    <ThemedView style={GlobalStyles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.keyboardContainer}
      >
        <ScrollView
          contentContainerStyle={GlobalStyles.scrollContainer}
          showsVerticalScrollIndicator={false}
        >
          <Card style={CardStyles.authCard}>
            <Card.Content>
              <ThemedText style={TEXT.authTitle}>Your Profile</ThemedText>
              <ThemedText style={TEXT.authSubtitle}>
                Update your account details
              </ThemedText>

              <View style={GlobalStyles.formContainer}>
                <TextInput
                  label="Username"
                  variant="outlined"
                  value={name}
                  onChangeText={setName}
                  style={GlobalStyles.input}
                  testID="change-name"
                />
                <TextInput
                  label="Email"
                  variant="outlined"
                  value={email}
                  onChangeText={validateEmail}
                  style={GlobalStyles.input}
                  keyboardType="email-address"
                  testID="change-email"
                />
                {emailInvalid && (
                  <ThemedText
                    style={{
                      color: "red",
                      fontSize: 13,
                      marginTop: -5,
                      marginBottom: 8,
                      textAlign: "center",
                    }}
                  >
                    Please enter a valid email address
                  </ThemedText>
                )}
                <TextInput
                  label="Vehicle Registration"
                  variant="outlined"
                  value={carReg}
                  onChangeText={setCarReg}
                  style={GlobalStyles.input}
                  testID="change-reg"
                />
                <TextInput
                  label="Role"
                  variant="outlined"
                  value={displayRole}
                  style={GlobalStyles.input}
                  editable={false}
                />

                <Button
                  mode="contained"
                  onPress={handleSave}
                  disabled={!isChanged}
                  style={[
                    GlobalStyles.authPrimaryButton,
                    !isChanged && { backgroundColor: "#b5a8e5" },
                  ]}
                  labelStyle={GlobalStyles.authButtonLabel}
                  testID="save-changes-btn"
                >
                  Save Changes
                </Button>

                <Button
                  mode="outlined"
                  onPress={handleLogout}
                  style={GlobalStyles.logoutButton}
                  labelStyle={GlobalStyles.logoutLabel}
                  testID="logout-btn"
                >
                  Logout
                </Button>
              </View>
            </Card.Content>
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </ThemedView>
  );
};

export default Profile;

const styles = StyleSheet.create({
  outerContainer: { flex: 1 },
  keyboardContainer: { flex: 1, justifyContent: "center" },
});
