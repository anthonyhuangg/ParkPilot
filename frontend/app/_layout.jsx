// app/_layout.jsx
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { Provider as PaperProvider, MD3LightTheme } from "react-native-paper";
import { ConnectionProvider } from "./connection-provider";
import { COLOURS } from "../theme/colours";

// Custom theme for React Native Paper
const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: COLOURS.primaryPurple,
    secondary: COLOURS.secondaryPurple,
    background: COLOURS.background,
    surface: COLOURS.white,
    onSurface: COLOURS.textDark,
  },
};

// Root layout component
export default function RootLayout() {
  return (
    <ConnectionProvider>
      <PaperProvider theme={theme}>
        <StatusBar style="auto" />

        <Stack
          screenOptions={{
            headerShown: false,
          }}
        />
      </PaperProvider>
    </ConnectionProvider>
  );
}
