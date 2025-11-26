import { useState, useEffect } from "react";
import { BottomNavigation } from "react-native-paper";
import { View, Alert } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useRouter } from "expo-router";
import Overview from "./overview-po";
import Carbon from "./carbon-po";
import Profile from "../(auth)/profile";
import { GlobalStyles } from "../../theme";

// DashboardScreenPO component manages the bottom navigation for the parking operator dashboard
export default function DashboardScreenPO() {
  const router = useRouter();
  const [token, setToken] = useState(null);
  const [index, setIndex] = useState(0);
  const routes = [
    {
      key: "overview",
      title: "Overview",
      focusedIcon: "map-marker",
      component: Overview,
    },
    {
      key: "carbon",
      title: "Carbon",
      focusedIcon: "leaf",
      component: Carbon,
      testID: "nav-carbon-po"
    },
    {
      key: "profile",
      title: "Profile",
      focusedIcon: "account",
      component: Profile,
      testID: "nav-profile-po"
    },
  ];

  // Check for authentication token on component mount
  useEffect(() => {
    const checkToken = async () => {
      try {
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
      } catch (err) {
        console.error("Error checking token:", err);
      }
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
