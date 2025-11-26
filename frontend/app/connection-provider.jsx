import { createContext, useState, useEffect, useRef, useCallback } from "react";
import NetInfo from "@react-native-community/netinfo";
import { Alert } from "react-native";
import PropTypes from "prop-types";

export const ConnectionContext = createContext(true);

// Connection provider component to monitor internet connectivity
export const ConnectionProvider = ({ children }) => {
  const [isConnected, setIsConnected] = useState(true);
  const previousState = useRef(true);
  const checkConnection = useCallback(async () => {
    const state = await NetInfo.fetch();
    if (!state.isConnected) {
      Alert.alert(
        "No Internet",
        "Your connection has been lost.",
        [
          { text: "Refresh", onPress: checkConnection },
          { text: "Close", style: "cancel" },
        ],
        { cancelable: true },
      );
    }
  }, []);

  // Subscribe to network state changes
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsConnected(state.isConnected);

      if (previousState.current === true && state.isConnected === false) {
        Alert.alert(
          "No Internet",
          "Your connection has been lost.",
          [
            { text: "Refresh", onPress: checkConnection },
            { text: "Close", style: "cancel" },
          ],
          { cancelable: true },
        );
      }

      previousState.current = state.isConnected;
    });

    return () => unsubscribe();
  }, [checkConnection]);

  return (
    <ConnectionContext.Provider value={isConnected}>
      {children}
    </ConnectionContext.Provider>
  );
};

ConnectionProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ConnectionProvider;
