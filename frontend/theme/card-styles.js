import { COLOURS } from "./colours";
import { SPACING } from "./spacing";

export const CardStyles = {
  card: {
    backgroundColor: COLOURS.white,
    borderRadius: 16,
    padding: SPACING.lg,
    width: "95%",
    alignSelf: "center",
    elevation: 3,
    shadowColor: COLOURS.black,
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    marginVertical: 8,
  },
  cardpo: {
    marginVertical: 8,
    borderRadius: 10,
    backgroundColor: "#fff",
    elevation: 3,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 3,
    shadowOffset: { width: 0, height: 2 },
  },
  cardContent: {
    alignItems: "center",
  },
  tableRow: {
    flexDirection: "row",
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLOURS.subtitle,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.4)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalCard: {
    width: "85%",
    backgroundColor: "white",
    borderRadius: 16,
    padding: 20,
    elevation: 5,
  },
  modalOption: { paddingVertical: 10 },
  modalCloseBtn: {
    borderRadius: 10,
    backgroundColor: "rgba(138,92,246,0.1)",
  },
  authCard: {
    width: "95%",
    maxWidth: 520,
    backgroundColor: "#fff",
    borderRadius: 18,
    elevation: 5,
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 4 },
    paddingVertical: 25,
  },
};
