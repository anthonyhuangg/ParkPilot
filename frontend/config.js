import Constants from "expo-constants";

// Detect Expo’s host URI (real device on LAN)
const host = Constants.expoConfig?.hostUri?.split(":")[0];

// Special handling for Android Emulator
const isAndroidEmulator =
  Constants.platform?.android && !host?.startsWith("192.");

// API base
export const API_BASE_URL = isAndroidEmulator
  ? "http://10.0.2.2:8000"
  : host
    ? `http://${host}:8000`
    : "http://localhost:8000";

console.log("Backend URL:", API_BASE_URL);
