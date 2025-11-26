import { useState } from "react";
import { StyleSheet, Alert, Pressable, View, ScrollView } from "react-native";
import { TextInput } from "@react-native-material/core";
import { Button, Card } from "react-native-paper";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ThemedText from "../../components/themed-text";
import { useRouter } from "expo-router";
import { TEXT, GlobalStyles, CardStyles } from "../../theme";
import { API_BASE_URL } from "../../config";

// Login component deals with previously registered drivers and parking operators
const Login = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailInvalid, setEmailInvalid] = useState(false);

  // Function to handle login
  const handleLogin = async () => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await fetch(`${API_BASE_URL}/api/users/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Login failed");
      }

      const data = await response.json();

      await AsyncStorage.setItem("access_token", data.access_token);
      await AsyncStorage.setItem("user_role", data.user.role);
      await AsyncStorage.setItem("user_name", data.user.name);
      await AsyncStorage.setItem("user_email", data.user.email);
      await AsyncStorage.setItem("user_car_reg", data.user.car_reg);
      await AsyncStorage.setItem("user_id", data.user.id.toString());

      const role = data.user.role?.toLowerCase();
      router.replace(role === "dr" ? "/home" : "/home-po");

      Alert.alert("Success", "User logged in successfully!");
    } catch (err) {
      console.error(err);
      Alert.alert("Error", err.message);
    }
  };

  // Render the login form
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Card style={CardStyles.authCard}>
        <Card.Content>
          <ThemedText style={TEXT.authTitle}>Login</ThemedText>
          <ThemedText style={TEXT.authSubtitle}>
            Please sign in to access your account
          </ThemedText>

          <View style={GlobalStyles.formContainer}>
            <TextInput
              label="Email"
              variant="outlined"
              value={email}
              onChangeText={(text) => {
                setEmail(text);
                setEmailInvalid(!text.includes("@"));
              }}
              style={GlobalStyles.input}
              keyboardType="email-address"
              testID="email-input"
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
              style={GlobalStyles.input}
              secureTextEntry
              testID="password-input"
            />

            <Button
              mode="contained"
              onPress={handleLogin}
              style={GlobalStyles.authPrimaryButton}
              labelStyle={GlobalStyles.authButtonLabel}
              disabled={emailInvalid || !email || !password}
              testID="login-button"
            >
              Login
            </Button>

            <Pressable onPress={() => router.push("/register")}>
              {({ pressed }) => (
                <ThemedText
                  style={[
                    TEXT.link,
                    { color: pressed ? "#7B5AF0" : "#5A36C8" },
                  ]}
                >
                  Don’t have an account? Register now
                </ThemedText>
              )}
            </Pressable>
          </View>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

export default Login;

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
    backgroundColor: "#f0f0f0",
  },
});
