module.exports = {
  root: true,
  parser: "@babel/eslint-parser",
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: "module",
    ecmaFeatures: {
      jsx: true, // Enable JSX parsing
    },
    requireConfigFile: false, // No need for external babel config
    babelOptions: {
      presets: ["@babel/preset-react"], // Add this for JSX parsing
    },
  },
  extends: [
    "@react-native-community",
    "plugin:react/recommended",
    "plugin:prettier/recommended",
  ],
  plugins: ["react", "prettier"],
  rules: {
    "prettier/prettier": ["error"], // Show Prettier issues as ESLint errors
    "react/react-in-jsx-scope": "off", // Not needed in React Native
    "react-hooks/exhaustive-deps": "warn",
  },
  settings: {
    react: {
      version: "detect",
    },
  },
};
