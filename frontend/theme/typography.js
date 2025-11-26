import { COLOURS } from "./colours";
import { SPACING } from "./spacing";

export const TEXT = {
  heading: {
    fontSize: 24,
    fontWeight: "700",
    color: COLOURS.text,
    textAlign: "center",
  },
  body: {
    fontSize: 16,
    color: COLOURS.textMedium,
  },
  subtitle: {
    fontSize: 18,
    color: COLOURS.subtitle,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: COLOURS.textDark,
  },
  header: {
    fontSize: 26,
    fontWeight: "800",
    textAlign: "center",
    color: COLOURS.primaryPurple,
  },
  cardLabel: {
    fontSize: 18,
    fontWeight: "600",
    color: COLOURS.textDark,
    marginBottom: SPACING.xs,
  },
  valueCarbon: {
    fontSize: 25,
    fontWeight: "900",
    color: COLOURS.primary,
    marginVertical: SPACING.xs,
  },
  valueMoney: {
    fontSize: 25,
    fontWeight: "900",
    color: COLOURS.secondaryPurple,
    marginVertical: SPACING.xs,
  },
  cardDescription: {
    fontSize: 14,
    color: COLOURS.textMedium,
    marginTop: SPACING.xs,
    textAlign: "center",
  },
  primaryButtonLabel: {
    fontSize: 16,
    fontWeight: "600",
    color: COLOURS.white,
  },
  highlightPurple: {
    fontSize: 17,
    color: COLOURS.primaryPurple,
    fontWeight: "700",
  },
  subtitleCentered: {
    fontSize: 18,
    fontWeight: "600",
    textAlign: "center",
    color: COLOURS.text,
    marginVertical: SPACING.md,
  },
  overviewWelcome: {
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
    color: COLOURS.textDark,
  },
  infoText: {
    fontSize: 17,
    textAlign: "center",
    color: COLOURS.textMedium,
    marginTop: SPACING.xs,
  },
  userName: {
    fontSize: 27,
    fontWeight: "900",
    color: COLOURS.primaryPurple,
  },
  garageName: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#333",
  },
  garageLocation: {
    fontSize: 14,
    color: "#666",
    marginTop: 4,
  },
  garageSpots: {
    fontSize: 14,
    color: COLOURS.primaryPurple,
    marginTop: 6,
    fontWeight: "600",
  },
  errorText: {
    color: "red",
    textAlign: "center",
    marginTop: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: COLOURS.secondaryPurple,
    textAlign: "center",
    marginBottom: 15,
  },
  modalOptionText: { fontSize: 16, textAlign: "center", color: "#333" },
  sectionTitleCarbon: {
    fontSize: 18,
    fontWeight: "600",
    color: COLOURS.secondaryPurple,
    textAlign: "center",
  },
  topButtonLabel: { fontWeight: "600", textAlign: "center" },
  driverName: { fontSize: 16, fontWeight: "500", color: "#222" },
  driverValue: {
    fontSize: 16,
    fontWeight: "600",
    color: COLOURS.secondaryPurple,
  },
  link: {
    textAlign: "center",
    textDecorationLine: "underline",
    fontSize: 14,
    marginTop: 8,
  },
  authTitle: {
    fontSize: 24,
    fontWeight: "900",
    color: COLOURS.primaryPurple,
    textAlign: "center",
    marginBottom: 6,
  },
  authSubtitle: {
    fontSize: 16,
    color: "#555",
    textAlign: "center",
    marginBottom: 20,
  },
};
