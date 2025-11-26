import { COLOURS } from "./colours";
import { SPACING } from "./spacing";

export const GlobalStyles = {
  screen: {
    flex: 1,
    backgroundColor: COLOURS.mapBackground,
  },
  screenCentered: {
    flex: 1,
    backgroundColor: COLOURS.mapBackground,
    justifyContent: "center",
    alignItems: "center",
  },
  keyboardFill: {
    flex: 1,
    justifyContent: "center",
  },
  centeredScroll: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: SPACING.xl,
    paddingHorizontal: SPACING.md,
  },
  cardContentCentered: {
    alignItems: "center",
    textAlign: "center",
  },
  cardLarge: {
    width: "95%",
    maxWidth: 520,
    backgroundColor: COLOURS.cardBackground,
    borderRadius: 18,
    elevation: 5,
    shadowColor: COLOURS.black,
    shadowOpacity: 0.12,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 4 },
    paddingVertical: SPACING.lg,
  },
  buttonColumnCenter: {
    alignItems: "center",
    width: "100%",
  },
  primaryButton: {
    backgroundColor: COLOURS.primaryPurple,
    width: "85%",
    borderRadius: 8,
    marginTop: SPACING.sm,
  },
  secondaryButton: {
    backgroundColor: COLOURS.secondaryPurple,
    width: "85%",
    borderRadius: 8,
    marginTop: SPACING.md,
  },
  navigationScreen: {
    flex: 1,
    backgroundColor: COLOURS.mapBackground,
  },
  container: {
    flex: 1,
    backgroundColor: COLOURS.background,
    paddingTop: 50,
  },
  searchBar: {
    marginHorizontal: 15,
    marginBottom: 10,
    borderRadius: 8,
    elevation: 2,
  },
  listContainer: {
    paddingBottom: 50,
    paddingHorizontal: 15,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 30,
    paddingHorizontal: 20,
  },
  lotButton: {
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: COLOURS.secondaryPurple,
    backgroundColor: "white",
    width: "100%",
    marginBottom: 12,
  },
  tableRow: {
    flexDirection: "row",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#ddd",
  },
  tableColLeft: {
    flex: 1,
    paddingRight: 10,
    borderRightWidth: 1,
    borderRightColor: "#ccc",
    justifyContent: "center",
  },
  tableColRight: {
    flex: 1,
    paddingLeft: 10,
    justifyContent: "center",
  },

  authPrimaryButton: {
    backgroundColor: COLOURS.primaryPurple,
    borderRadius: 8,
    width: "90%",
    marginTop: 25,
    marginBottom: 15,
  },
  authButtonLabel: {
    fontSize: 16,
    fontWeight: "600",
    color: "#fff",
  },
  formContainer: {
    alignItems: "center",
    width: "100%",
  },
  input: {
    width: "90%",
    marginVertical: 8,
  },
  logoutButton: {
    borderColor: COLOURS.primaryPurple,
    width: "90%",
    borderRadius: 8,
  },
  logoutLabel: {
    fontSize: 16,
    color: COLOURS.primaryPurple,
    fontWeight: "600",
  },
};
