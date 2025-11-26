import { useState, useEffect } from "react";
import { BottomNavigation } from "react-native-paper";
import { View, Alert } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import Overview from "./overview";
import Carbon from "./carbon";
import Profile from "../(auth)/profile";
import { GlobalStyles } from "../../theme";

// Main dashboard screen with bottom navigation
export default function DashboardScreen() {
  const router = useRouter();
  const [token, setToken] = useState(null);
  const [index, setIndex] = useState(0);
  const routes = [
    {
      key: "overview",
      title: "Overview",
      focusedIcon: "map-marker",
      component: Overview,
      testID: "nav-overview",
    },
    {
      key: "carbon",
      title: "Carbon",
      focusedIcon: "leaf",
      component: Carbon,
      testID: "nav-carbon",
    },
    {
      key: "profile",
      title: "Profile",
      focusedIcon: "account",
      component: Profile,
      testID: "nav-profile",
    },
  ];

  // Check for authentication token on mount
  useEffect(() => {
    const checkToken = async () => {
      const savedToken = await AsyncStorage.getItem("access_token");

      if (!savedToken) {
        Alert.alert(
          "Unauthorized",
          "You must be logged in to access the dashboard.",
        );
        router.replace("/login");
        return;
      }

      setToken(savedToken);
    };

    checkToken();
  }, [router]);

  if (!token) return null;

  const renderScene = ({ route }) => {
    const Component = route.component;
    return <Component />;
  };

  return (
    <View style={GlobalStyles.screen}>
      <BottomNavigation
        navigationState={{ index, routes }}
        onIndexChange={setIndex}
        renderScene={renderScene}
      />
    </View>
  );
}
