import { StyleSheet } from "react-native";
import { COLOURS } from "./colours";
import { SPACING } from "./spacing";

export const PARKINGLOT = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLOURS.mapBackground,
  },
  canvas: {
    position: "relative",
    backgroundColor: COLOURS.mapBackground,
  },
  cell: {
    position: "absolute",
    width: 60,
    height: 60,
    justifyContent: "center",
    alignItems: "center",
  },
  baseCell: {
    justifyContent: "center",
    alignItems: "center",
  },
  entryExitLabel: {
    color: COLOURS.white,
    fontWeight: "bold",
    fontSize: 12,
  },
  spotCell: {
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1,
    borderColor: COLOURS.black,
    zIndex: 10,
    position: "absolute",
  },
  spotLabel: {
    fontSize: 14,
    fontWeight: "bold",
    color: COLOURS.textDark,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    paddingHorizontal: SPACING.md,
    pointerEvents: "box-none",
  },
  topOverlay: {
    position: "absolute",
    top: 0,
    left: SPACING.md,
    right: SPACING.md,
  },
  topControlRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  backButton: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(255,255,255,0.7)",
    elevation: 2,
  },
  backButtonLabel: {
    fontSize: 16,
    fontWeight: "600",
    color: COLOURS.secondaryPurple,
  },
  bottomOverlay: {
    position: "absolute",
    bottom: 30,
    left: SPACING.md,
    right: SPACING.md,
    alignItems: "center",
  },
  primaryActionButton: {
    width: "90%",
    height: 50,
    justifyContent: "center",
    backgroundColor: COLOURS.secondaryPurple,
    borderRadius: 10,
  },
  primaryLabel: {
    fontSize: 18,
    fontWeight: "bold",
    color: COLOURS.white,
  },
  confirmButtonDisabled: {
    opacity: 0.5,
    backgroundColor: COLOURS.secondaryPurple,
  },
  confirmLabel: {
    fontSize: 18,
    fontWeight: "600",
    color: COLOURS.white,
  },
  edgeHorizontalLine: {
    position: "absolute",
    borderRadius: 4,
    opacity: 0.9,
    zIndex: 4,
  },
  edgeVerticalLine: {
    position: "absolute",
    borderRadius: 4,
    opacity: 0.9,
    zIndex: 4,
  },
  edgeTailHorizontal: {
    position: "absolute",
    borderRadius: 4,
    opacity: 0.9,
    zIndex: 4,
  },
  edgeTailVertical: {
    position: "absolute",
    borderRadius: 4,
    opacity: 0.9,
    zIndex: 4,
  },
  edgeArrowHorizontal: {
    position: "absolute",
    width: 0,
    height: 0,
    borderTopWidth: 8,
    borderBottomWidth: 8,
    borderStyle: "solid",
    borderTopColor: "transparent",
    borderBottomColor: "transparent",
    zIndex: 5,
  },
  edgeArrowVertical: {
    position: "absolute",
    width: 0,
    height: 0,
    borderLeftWidth: 8,
    borderRightWidth: 8,
    borderStyle: "solid",
    borderLeftColor: "transparent",
    borderRightColor: "transparent",
    zIndex: 5,
  },
  userMarker: {
    position: "absolute",
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: COLOURS.routeBlue,
    borderWidth: 3,
    borderColor: COLOURS.white,
    zIndex: 9999,
  },
});
