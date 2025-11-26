import { useRef, useState, useEffect, useMemo } from "react";
import {
  View,
  TouchableOpacity,
  Animated,
  PanResponder,
  Dimensions,
} from "react-native";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import Spacer from "../../components/spacer";
import { Button } from "react-native-paper";
import { useRouter, useLocalSearchParams } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import RNEventSource from "react-native-sse";
import { API_BASE_URL } from "../../config";
import { COLOURS, PARKINGLOT } from "../../theme";

const CELL_SIZE = 60;
const step = (n) => n * CELL_SIZE;
const cellToPx = (i) => i * CELL_SIZE;

const MIN_ZOOM = 0.3;
const MAX_ZOOM = 2.0;

const ROAD_THICKNESS = 8;
const BASE_LINE_THICKNESS = ROAD_THICKNESS * 0.6;
const EDGE_SHORTEN = 30;
const ARROW_TAIL_LENGTH = 12;
const ARROW_SIZE = 8;
const ARROW_LENGTH = 14;

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

// Parse parking lot JSON into grid format
function parseLot(json) {
  if (!json || !json.nodes) return [[]];

  const maxRow = Math.max(...json.nodes.map((n) => n.x)) + 1;
  const maxCol = Math.max(...json.nodes.map((n) => n.y)) + 1;

  const grid = Array.from({ length: maxRow }, () =>
    Array.from({ length: maxCol }, () => ({ type: "wall" })),
  );

  for (const node of json.nodes) {
    const { id, type, x, y, label, status, orientation } = node;
    if (x >= maxRow || y >= maxCol) continue;

    let normalType = "road";
    if (type === "CAR_ENTRANCE") normalType = "entry";
    else if (type === "CAR_EXIT") normalType = "exit";
    else if (type === "PARKING_SPOT") normalType = "spot";

    grid[x][y] = {
      id,
      type: normalType,
      label,
      occupied: status === "OCCUPIED",
      reserved: status === "RESERVED",
      orientation: orientation ?? 0,
    };
  }

  return grid;
}

// Parking lot screen component for the driver to select a spot
export default function ParkingLot() {
  const router = useRouter();
  const { lot_id } = useLocalSearchParams();
  const lotId = Number(lot_id) || 1;
  const [selectedSpotId, setSelectedSpotId] = useState(null);
  const [selectedSpotLabel, setSelectedSpotLabel] = useState(null);
  const [mapData, setMapData] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userPosition, setUserPosition] = useState({
    row: 0,
    col: 0,
    nodeId: undefined,
  });
  const [mapRotation, setMapRotation] = useState("0deg");
  const animatedScale = useRef(new Animated.Value(1));
  const translateX = useRef(new Animated.Value(0));
  const translateY = useRef(new Animated.Value(0));
  const lastOffset = useRef({ x: 0, y: 0 });
  const initialDistance = useRef(null);
  const initialZoomRef = useRef(1);
  const currentScaleValue = useRef(1);

  // Fetch and set up parking lot map on mount
  useEffect(() => {
    const fetchAndSetupMap = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/parking/${lotId}/nodes`);
        const json = await res.json();

        const parsed = parseLot(json);
        setMapData(parsed);

        const entrance = json.nodes.find((n) => n.type === "CAR_ENTRANCE");
        if (entrance) {
          setUserPosition({
            row: entrance.x,
            col: entrance.y,
            nodeId: entrance.id,
          });
        }

        const width = step(parsed[0]?.length || 1);
        const height = step(parsed.length || 1);

        const isSpecial = [1, 4].includes(lotId);
        setMapRotation(isSpecial ? "0deg" : "90deg");

        const scaleBase =
          Math.min(SCREEN_WIDTH / width, SCREEN_HEIGHT / height, 1) * 0.85;

        const adjusted = isSpecial ? scaleBase : scaleBase * 1.6;

        animatedScale.current.setValue(adjusted);
        currentScaleValue.current = adjusted;

        const initX = isSpecial ? -150 : -675;
        const initY = isSpecial ? 50 : -175;
        translateX.current.setValue(initX);
        translateY.current.setValue(initY);
        lastOffset.current = { x: initX, y: initY };

        // fetch edges
        try {
          const edgeRes = await fetch(
            `${API_BASE_URL}/api/parking/${lotId}/road-edges`,
          );
          const edgesJson = await edgeRes.json();

          const mappedEdges = edgesJson.map((e) => ({
            from: e.from_node_id,
            to: e.to_node_id,
            status: e.status,
            bidirectional: e.bidirectional,
          }));

          setEdges(mappedEdges);
        } catch (edgeErr) {
          console.error("Edge error:", edgeErr);
          setEdges([]);
        }
      } catch (err) {
        console.error("Map fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAndSetupMap();
  }, [lotId]);

  // Set up SSE for real-time spot updates
  useEffect(() => {
    if (!mapData.length) return;

    const ev = new RNEventSource(`${API_BASE_URL}/api/sse?lot_id=${lotId}`);
    ev.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data);
        setMapData((prev) =>
          prev.map((row) =>
            row.map((cell) =>
              cell?.id === data.node_id && cell.type === "spot"
                ? {
                    ...cell,
                    occupied:
                      data.status === "OCCUPIED" || data.status === "RESERVED",
                  }
                : cell,
            ),
          ),
        );
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    });

    ev.addEventListener("error", (err) => {
      console.warn("SSE error:", err);
      ev.close();
    });

    return () => ev.close();
  }, [mapData, lotId]);

  // Pinch zoom handlers
  const getDistance = (touches) => {
    if (touches.length < 2) return null;
    const [t1, t2] = touches;
    const dx = t1.pageX - t2.pageX;
    const dy = t1.pageY - t2.pageY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  // Touch handlers for pinch zoom
  const handleTouchStart = (e) => {
    const touches = e.nativeEvent.touches;
    if (touches.length === 2) {
      initialDistance.current = getDistance(touches);
      initialZoomRef.current = currentScaleValue.current;
    }
  };

  // Handle touch move for pinch zoom
  const handleTouchMove = (e) => {
    const touches = e.nativeEvent.touches;
    if (touches.length === 2 && initialDistance.current) {
      const dist = getDistance(touches);
      if (!dist) return;

      const ratio = dist / initialDistance.current;
      let newScale = initialZoomRef.current * ratio;
      newScale = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, newScale));
      animatedScale.current.setValue(newScale);
      currentScaleValue.current = newScale;
    }
  };

  // Handle touch end for pinch zoom
  const handleTouchEnd = () => {
    initialDistance.current = null;
  };

  // Pan responder for dragging the map
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: () => {
        translateX.current.setOffset(lastOffset.current.x);
        translateY.current.setOffset(lastOffset.current.y);
        translateX.current.setValue(0);
        translateY.current.setValue(0);
      },
      onPanResponderMove: Animated.event(
        [null, { dx: translateX.current, dy: translateY.current }],
        { useNativeDriver: false },
      ),
      onPanResponderRelease: () => {
        translateX.current.flattenOffset();
        translateY.current.flattenOffset();
        lastOffset.current = {
          x: translateX.current.__getValue(),
          y: translateY.current.__getValue(),
        };
      },
    }),
  ).current;

  // Spot selection
  const handleSpotPress = (spot) => {
    if (spot.type !== "spot" || spot.occupied) return;

    setSelectedSpotId(spot.id === selectedSpotId ? null : spot.id);
    setSelectedSpotLabel(spot.label === selectedSpotLabel ? null : spot.label);
  };

  // Confirm spot
  const handleConfirmSpot = async () => {
    if (!selectedSpotId) return;

    try {
      const ttl = 60;

      await fetch(
        `${API_BASE_URL}/api/parking/${lotId}/update_status?node_id=${selectedSpotId}&status=RESERVED&ttl=${ttl}`,
        { method: "POST", headers: { "Content-Type": "application/json" } },
      );

      await AsyncStorage.setItem("selected_spot_id", String(selectedSpotId));
      await AsyncStorage.setItem(
        "selected_spot_label",
        selectedSpotLabel || "",
      );
      await AsyncStorage.setItem("selected_lot_id", String(lotId));

      const userId = await AsyncStorage.getItem("user_id");

      const carbonPayload = {
        user_id: Number(userId),
        lot_id: lotId,
        distance_traveled_m: 150,
      };

      await fetch(`${API_BASE_URL}/carbon/record-saving`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(carbonPayload),
      });

      router.push(
        `/navigation?mode=spot&lot_id=${lotId}&start=${userPosition.nodeId}&end=${selectedSpotId}`,
      );
    } catch (err) {
      console.error("Confirm spot error:", err);
    }
  };

  const handleGoBack = () => router.back();

  const ROWS = mapData.length || 1;
  const COLS = mapData[0]?.length || 1;

  // Precompute node positions for edge rendering
  const nodePositions = useMemo(() => {
    const pos = {};
    for (let r = 0; r < mapData.length; r++) {
      for (let c = 0; c < (mapData[r]?.length || 0); c++) {
        const cell = mapData[r][c];
        if (cell?.id != null) pos[cell.id] = { row: r, col: c };
      }
    }
    return pos;
  }, [mapData]);

  // Render edges between nodes
  const renderEdges = () => {
    if (!edges.length) return null;

    const elements = [];
    let arrowCount = 0;

    edges.forEach((edge, idx) => {
      const fromPos = nodePositions[edge.from];
      const toPos = nodePositions[edge.to];
      if (!fromPos || !toPos) return;

      const x1 = cellToPx(fromPos.col) + CELL_SIZE / 2;
      const y1 = cellToPx(fromPos.row) + CELL_SIZE / 2;
      const x2 = cellToPx(toPos.col) + CELL_SIZE / 2;
      const y2 = cellToPx(toPos.row) + CELL_SIZE / 2;

      const isBidirectional = !!edge.bidirectional;
      const isOpen = edge.status !== "CLOSED";
      const colour = isOpen ? COLOURS.white : COLOURS.subtitle;

      const isHorizontal = y1 === y2;
      const isVertical = x1 === x2;

      let shouldArrow = false;
      const arrowEligible =
        !isBidirectional && isOpen && (isHorizontal || isVertical);

      if (arrowEligible) {
        if (arrowCount % 5 === 0) shouldArrow = true;
        arrowCount++;
      }

      if (isHorizontal) {
        const isLTR = x2 > x1;
        const minX = Math.min(x1, x2);
        const fullWidth = Math.abs(x2 - x1);

        const left = minX + 4;
        const width = Math.max(0, fullWidth - EDGE_SHORTEN);
        const top = y1 - BASE_LINE_THICKNESS / 2;

        if (shouldArrow) {
          const midX = (x1 + x2) / 2;
          const arrowBaseX = isLTR ? midX - ARROW_SIZE : midX + ARROW_SIZE;

          const tailLeft = isLTR ? arrowBaseX - ARROW_TAIL_LENGTH : arrowBaseX;

          elements.push(
            <View
              key={`edge-${idx}-h-tail`}
              style={[
                PARKINGLOT.edgeTailHorizontal,
                {
                  left: tailLeft,
                  top,
                  width: ARROW_TAIL_LENGTH,
                  height: BASE_LINE_THICKNESS * 0.75,
                  backgroundColor: colour,
                },
              ]}
            />,
          );

          elements.push(
            <View
              key={`edge-${idx}-h-arrow`}
              style={[
                PARKINGLOT.edgeArrowHorizontal,
                {
                  left: midX - ARROW_SIZE,
                  top: y1 - ARROW_SIZE,
                  borderLeftWidth: isLTR ? ARROW_LENGTH : 0,
                  borderRightWidth: isLTR ? 0 : ARROW_LENGTH,
                  borderLeftColor: isLTR ? colour : "transparent",
                  borderRightColor: isLTR ? "transparent" : colour,
                },
              ]}
            />,
          );
        } else {
          elements.push(
            <View
              key={`edge-${idx}-h-line`}
              style={[
                PARKINGLOT.edgeHorizontalLine,
                {
                  left,
                  top,
                  width,
                  height: BASE_LINE_THICKNESS,
                  backgroundColor: colour,
                },
              ]}
            />,
          );
        }
      }

      if (isVertical) {
        const isTTB = y2 > y1;
        const minY = Math.min(y1, y2);
        const fullHeight = Math.abs(y2 - y1);

        const top = minY + 4;
        const height = Math.max(0, fullHeight - EDGE_SHORTEN);
        const left = x1 - BASE_LINE_THICKNESS / 2;

        if (shouldArrow) {
          const midY = (y1 + y2) / 2;
          const arrowBaseY = isTTB ? midY - ARROW_SIZE : midY + ARROW_SIZE;

          const tailTop = isTTB ? arrowBaseY - ARROW_TAIL_LENGTH : arrowBaseY;

          elements.push(
            <View
              key={`edge-${idx}-v-tail`}
              style={[
                PARKINGLOT.edgeTailVertical,
                {
                  left,
                  top: tailTop,
                  height: ARROW_TAIL_LENGTH,
                  width: BASE_LINE_THICKNESS * 0.75,
                  backgroundColor: colour,
                },
              ]}
            />,
          );

          elements.push(
            <View
              key={`edge-${idx}-v-arrow`}
              style={[
                PARKINGLOT.edgeArrowVertical,
                {
                  left: x1 - ARROW_SIZE,
                  top: midY - ARROW_SIZE,
                  borderTopWidth: isTTB ? ARROW_LENGTH : 0,
                  borderBottomWidth: isTTB ? 0 : ARROW_LENGTH,
                  borderTopColor: isTTB ? colour : "transparent",
                  borderBottomColor: isTTB ? "transparent" : colour,
                },
              ]}
            />,
          );
        } else {
          elements.push(
            <View
              key={`edge-${idx}-v-line`}
              style={[
                PARKINGLOT.edgeVerticalLine,
                {
                  left,
                  top,
                  height,
                  width: BASE_LINE_THICKNESS,
                  backgroundColor: colour,
                },
              ]}
            />,
          );
        }
      }
    });

    return elements;
  };

  // Render parking lot cells
  const renderCells = () => {
    const items = [];
    const spotItems = [];

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const cell = mapData[r]?.[c];
        if (!cell) continue;

        const left = cellToPx(c);
        const top = cellToPx(r);

        let bg = COLOURS.mapBackground;
        if (cell.type === "spot") {
          if (cell.occupied) bg = COLOURS.occupied;
          else if (cell.reserved) bg = COLOURS.reserved;
          else bg = COLOURS.available;
        } else if (cell.type === "entry" || cell.type === "exit") {
          bg = COLOURS.entrancePurple;
        } else if (cell.type === "road") {
          bg = COLOURS.roadGrey;
        }

        if (cell.type === "spot") {
          const isSelected = cell.id === selectedSpotId;
          const orientation = cell.orientation ?? 0;

          let width = CELL_SIZE;
          let height = CELL_SIZE;
          let offsetX = 0;
          let offsetY = 0;

          switch (orientation) {
            case 0:
              height = CELL_SIZE * 2;
              offsetY = -CELL_SIZE;
              break;
            case 90:
              width = CELL_SIZE * 2;
              break;
            case 180:
              height = CELL_SIZE * 2;
              break;
            case 270:
              width = CELL_SIZE * 2;
              offsetX = -CELL_SIZE;
              break;
          }

          spotItems.push(
            <TouchableOpacity
              key={`spot-${r}-${c}`}
              testID={`spot-${cell.label}`}
              onPress={() => handleSpotPress(cell)}
              disabled={cell.occupied}
              style={[
                PARKINGLOT.cell,
                PARKINGLOT.spotCell,
                {
                  left: left + offsetX,
                  top: top + offsetY,
                  width,
                  height,
                  backgroundColor: isSelected ? COLOURS.routeBlue : bg,
                  borderWidth: 1,
                  borderColor: COLOURS.black,
                },
              ]}
            >
              <View
                style={{
                  transform: [
                    { rotate: [1, 4].includes(lotId) ? "0deg" : "-90deg" },
                  ],
                  width: "100%",
                  alignItems: "center",
                }}
              >
                <ThemedText
                  style={[
                    PARKINGLOT.spotLabel,
                    { color: isSelected ? COLOURS.white : COLOURS.textDark },
                  ]}
                >
                  {cell.label}
                </ThemedText>
              </View>
            </TouchableOpacity>,
          );
        } else {
          items.push(
            <View
              key={`cell-${r}-${c}`}
              style={[
                PARKINGLOT.cell,
                PARKINGLOT.baseCell,
                {
                  left,
                  top,
                  width: CELL_SIZE,
                  height: CELL_SIZE,
                  backgroundColor: bg,
                },
              ]}
            >
              {(cell.type === "entry" || cell.type === "exit") && (
                <ThemedText style={PARKINGLOT.entryExitLabel}>
                  {cell.type === "entry" ? "ENTRY" : "EXIT"}
                </ThemedText>
              )}
            </View>,
          );
        }
      }
    }

    return [...items, ...spotItems];
  };

  return (
    <ThemedView style={PARKINGLOT.container}>
      {loading ? (
        <ThemedText>Loading parking lot…</ThemedText>
      ) : (
        <Animated.View
          {...panResponder.panHandlers}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          style={[
            PARKINGLOT.canvas,
            {
              width: step(COLS),
              height: step(ROWS),
              transform: [
                { translateX: translateX.current },
                { translateY: translateY.current },
                { scale: animatedScale.current },
                { rotate: mapRotation },
              ],
            },
          ]}
        >
          {renderEdges()}
          {renderCells()}

          {/* User marker */}
          <View
            style={[
              PARKINGLOT.userMarker,
              {
                left: cellToPx(userPosition.col) + CELL_SIZE / 2 - 12,
                top: cellToPx(userPosition.row) + CELL_SIZE / 2 - 12,
              },
            ]}
          />
        </Animated.View>
      )}

      {/* Back button overlay */}
      <View style={PARKINGLOT.topOverlay}>
        <Spacer height={70} />
        <View style={PARKINGLOT.topControlRow}>
          <Button
            mode="text"
            icon="chevron-left"
            onPress={handleGoBack}
            style={PARKINGLOT.backButton}
            labelStyle={PARKINGLOT.backButtonLabel}
          >
            Back
          </Button>
        </View>
      </View>

      {/* Confirm spot overlay */}
      <View style={PARKINGLOT.bottomOverlay}>
        <Button
          mode="contained"
          disabled={!selectedSpotId}
          onPress={handleConfirmSpot}
          style={[
            PARKINGLOT.primaryActionButton,
            !selectedSpotId && PARKINGLOT.confirmButtonDisabled,
          ]}
          buttonColor={COLOURS.secondaryPurple}
          contentStyle={{ width: "100%" }}
          labelStyle={PARKINGLOT.confirmLabel}
        >
          {selectedSpotId
            ? `Confirm Spot ${selectedSpotLabel}`
            : "Select a Spot"}
        </Button>
      </View>
    </ThemedView>
  );
}
