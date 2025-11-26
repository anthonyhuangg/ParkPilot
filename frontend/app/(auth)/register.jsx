import { useState, useEffect } from "react";
import {
  StyleSheet,
  View,
  Alert,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from "react-native";
import { TextInput } from "@react-native-material/core";
import { Button, Card } from "react-native-paper";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import { useRouter } from "expo-router";
import { API_BASE_URL } from "../../config";
import RoleSelection from "../../components/role-selection";
import { TEXT, GlobalStyles, CardStyles } from "../../theme";

// Register component handles new user registrations for drivers and parking opertors
const Register = () => {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [carReg, setCarReg] = useState("");
  const [role, setRole] = useState("dr");
  const [isValid, setIsValid] = useState(false);
  const [passwordMismatch, setPasswordMismatch] = useState(false);
  const [emailInvalid, setEmailInvalid] = useState(false);
  const [passwordInvalid, setPasswordInvalid] = useState(false);

  // Function to validate password strength
  const isPasswordValid = (pw) => {
    return (
      pw.length >= 8 && /[A-Z]/.test(pw) && /[a-z]/.test(pw) && /\d/.test(pw)
    );
  };

  // Effect to validate form inputs
  useEffect(() => {
    const allFieldsFilled =
      name && email && password && confirmPassword && carReg;

    const passwordsMatch = password === confirmPassword;
    const emailHasAt = email.includes("@");
    const passwordStrong = isPasswordValid(password);

    setPasswordMismatch(confirmPassword && !passwordsMatch);
    setEmailInvalid(email && !emailHasAt);
    setPasswordInvalid(password && !passwordStrong);

    setIsValid(
      allFieldsFilled && passwordsMatch && emailHasAt && passwordStrong,
    );
  }, [name, email, password, confirmPassword, carReg]);

  // Function to handle registration
  const handleRegister = async () => {
    try {
      const payload = {
        name,
        email,
        password,
        car_reg: carReg,
        role,
      };

      const response = await fetch(`${API_BASE_URL}/api/users/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(`Server returned invalid JSON: ${text}`);
      }

      if (!response.ok) {
        throw new Error(data.detail || "Failed to register");
      }

      await AsyncStorage.setItem("access_token", data.access_token);
      await AsyncStorage.setItem("user_role", data.user.role);
      await AsyncStorage.setItem("user_name", data.user.name);
      await AsyncStorage.setItem("user_email", data.user.email);
      await AsyncStorage.setItem("user_car_reg", data.user.car_reg);
      await AsyncStorage.setItem("user_id", data.user.id.toString());

      const userRole = data.user.role?.toLowerCase();
      router.replace(userRole === "dr" ? "/home" : "/home-po");
      Alert.alert("Success", "User registered successfully!");
    } catch (err) {
      console.error(err);
      Alert.alert("Error", err.message);
    }
  };

  return (
    <ThemedView style={styles.outerContainer}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.keyboardContainer}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContainer}
          showsVerticalScrollIndicator={false}
        >
          <Card style={CardStyles.authCard}>
            <Card.Content>
              <ThemedText style={TEXT.authTitle}>Create Account</ThemedText>
              <ThemedText style={TEXT.authSubtitle}>
                Please fill in your details to register
              </ThemedText>

              <View style={GlobalStyles.formContainer}>
                <TextInput
                  label="Username"
                  variant="outlined"
                  value={name}
                  onChangeText={setName}
                  style={GlobalStyles.input}
                />
                <TextInput
                  label="Email"
                  variant="outlined"
                  value={email}
                  onChangeText={setEmail}
                  style={GlobalStyles.input}
                  keyboardType="email-address"
                />
                {emailInvalid && (
                  <ThemedText
                    style={{
                      color: "red",
                      fontSize: 13,
                      marginTop: -5,
                      marginBottom: 8,
                    }}
                  >
                    Please enter a valid email address
                  </ThemedText>
                )}
                <TextInput
                  label="Password"
                  variant="outlined"
                  value={password}
                  onChangeText={setPassword}
                  style={[
                    GlobalStyles.input,
                    passwordInvalid && { borderColor: "red" },
                  ]}
                  secureTextEntry
                />
                {passwordInvalid && (
                  <ThemedText
                    style={{
                      color: "red",
                      fontSize: 13,
                      marginTop: -5,
                      marginBottom: 8,
                      textAlign: "center",
                      width: "100%",
                    }}
                  >
                    Use at least 8 characters, one uppercase letter, one
                    lowercase letter, and one number
                  </ThemedText>
                )}
                <TextInput
                  label="Confirm Password"
                  variant="outlined"
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  style={[
                    GlobalStyles.input,
                    passwordMismatch && { borderColor: "red" },
                  ]}
                  secureTextEntry
                />
                {passwordMismatch && (
                  <ThemedText
                    style={{
                      color: "red",
                      fontSize: 13,
                      marginTop: -5,
                      marginBottom: 8,
                    }}
                  >
                    Passwords do not match
                  </ThemedText>
                )}
                <TextInput
                  label="Vehicle Registration"
                  variant="outlined"
                  value={carReg}
                  onChangeText={setCarReg}
                  style={GlobalStyles.input}
                />

                <RoleSelection role={role} setRole={setRole} />

                <Button
                  mode="contained"
                  onPress={handleRegister}
                  disabled={!isValid}
                  style={[
                    GlobalStyles.authPrimaryButton,
                    !isValid && { backgroundColor: "#b5a8e5" },
                  ]}
                  labelStyle={GlobalStyles.authButtonLabel}
                >
                  Register
                </Button>

                <Pressable onPress={() => router.push("/login")}>
                  {({ pressed }) => (
                    <ThemedText
                      style={[
                        TEXT.link,
                        { color: pressed ? "#7B5AF0" : "#5A36C8" },
                      ]}
                    >
                      Already have an account? Login now
                    </ThemedText>
                  )}
                </Pressable>
              </View>
            </Card.Content>
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </ThemedView>
  );
};

export default Register;

const styles = StyleSheet.create({
  outerContainer: {
    flex: 1,
  },
  keyboardContainer: {
    flex: 1,
    justifyContent: "center",
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 30,
    paddingHorizontal: 20,
  },
});
