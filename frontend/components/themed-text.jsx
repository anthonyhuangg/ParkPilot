import { Text, useColorScheme, StyleSheet } from "react-native";
import { Colors } from "../constants/component-theme";
import PropTypes from "prop-types";

// ThemedText component for consistent theming of text elements
const ThemedText = ({ style, title = false, ...props }) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme] ?? Colors.light;

  return (
    <Text
      style={[
        { color: title ? theme.title : theme.text },
        title ? styles.title : styles.text,
        style,
      ]}
      {...props}
    />
  );
};

const styles = StyleSheet.create({
  title: {
    fontSize: 30,
  },
  text: {
    fontSize: 14,
  },
});

ThemedText.propTypes = {
  style: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.array,
    PropTypes.number,
  ]),
  title: PropTypes.bool,
};

export default ThemedText;
