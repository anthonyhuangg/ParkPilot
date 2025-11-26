import { View, useColorScheme } from "react-native";
import { Colors } from "../constants/component-theme";
import PropTypes from "prop-types";

// ThemedView component for consistent theming of view containers
const ThemedView = ({ style, ...props }) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme] ?? Colors.light;

  return (
    <View style={[{ backgroundColor: theme.background }, style]} {...props} />
  );
};

ThemedView.propTypes = {
  style: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.array,
    PropTypes.number,
  ]),
};

export default ThemedView;
