import { useRef, useState, useEffect } from "react";
import { View, Animated, PanResponder, Dimensions } from "react-native";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import { Button } from "react-native-paper";
import { useRouter, useLocalSearchParams } from "expo-router";
import Spacer from "../../components/spacer";
import { API_BASE_URL } from "../../config";
import RNEventSource from "react-native-sse";
import PropTypes from "prop-types";
import { PARKINGLOT } from "../../theme";
import { COLOURS } from "../../theme/colours";

const CELL_SIZE = 60;
const step = (n) => n * CELL_SIZE;
const cellToPx = (index) => index * CELL_SIZE;

const MIN_ZOOM = 0.3;
const MAX_ZOOM = 2.0;

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

// ParkingLotPO component displays the parking lot map for parking operators
const ParkingLotPO = () => {
  const router = useRouter();
  const { lot_id } = useLocalSearchParams();
  const [mapData, setMapData] = useState([]);
  const [loading, setLoading] = useState(true);
  const animatedScale = useRef(new Animated.Value(1.0)).current;
  const translateX = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(0)).current;
  const lastOffset = useRef({ x: 0, y: 0 });
  const initialDistance = useRef(null);
  const currentScaleValue = useRef(1.0);
  const initialZoomRef = useRef(1.0);
  const [mapRotation, setMapRotation] = useState("0deg");

  // Parse parking lot data into a grid format
  const parseLot = (lot) => {
    const maxRow = Math.max(...lot.nodes.map((n) => n.x)) + 1;
    const maxCol = Math.max(...lot.nodes.map((n) => n.y)) + 1;

    const rows = Math.max(lot.dimensions?.rows ?? 0, maxRow);
    const cols = Math.max(lot.dimensions?.cols ?? 0, maxCol);

    const grid = Array.from({ length: rows }, () =>
      Array.from({ length: cols }, () => ({ type: "wall" })),
    );

    for (const node of lot.nodes) {
      const { id, type, x, y, label, status, orientation } = node;

      if (x >= rows || y >= cols) continue;

      let normalised = "road";
      if (type === "CAR_ENTRANCE") normalised = "entry";
      else if (type === "CAR_EXIT") normalised = "exit";
      else if (type === "PARKING_SPOT") normalised = "spot";

      grid[x][y] = {
        id,
        type: normalised,
        label,
        occupied: status === "OCCUPIED",
        reserved: status === "RESERVED",
        orientation: orientation ?? 0,
      };
    }

    return grid;
  };

  // Fetch parking lot data on component mount
  useEffect(() => {
    const fetchLot = async () => {
      try {
        if (!lot_id) return;

        const res = await fetch(`${API_BASE_URL}/api/parking/${lot_id}/nodes`);
        const json = await res.json();

        const parsed = parseLot(json);
        setMapData(parsed);

        const mapWidth = step(parsed[0]?.length || 1);
        const mapHeight = step(parsed.length || 1);

        const scaleX = SCREEN_WIDTH / mapWidth;
        const scaleY = SCREEN_HEIGHT / mapHeight;

        const initialScale = Math.min(scaleX, scaleY, 1) * 0.85;
        animatedScale.setValue(initialScale);
        currentScaleValue.current = initialScale;

        const special = ["1", "4"].includes(String(lot_id));
        const initialX = special ? -92.5 : -745;
        const initialY = special ? 100 : -415;

        setMapRotation(special ? "0deg" : "90deg");

        const finalScale = special ? initialScale : initialScale * 1.6;
        animatedScale.setValue(finalScale);
        currentScaleValue.current = finalScale;

        translateX.setValue(initialX);
        translateY.setValue(initialY);
        lastOffset.current = { x: initialX, y: initialY };
      } catch (err) {
        console.error("Error loading parking lot:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchLot();
  }, [lot_id]);

  // Set up Server-Sent Events (SSE) for real-time updates
  useEffect(() => {
    if (!mapData.length || !lot_id) return;

    const eventSource = new RNEventSource(
      `${API_BASE_URL}/api/sse?lot_id=${lot_id}`,
    );

    eventSource.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data);

        setMapData((prev) => {
          const newMap = prev.map((r) => r.map((c) => ({ ...c })));

          for (let r = 0; r < newMap.length; r++) {
            for (let c = 0; c < newMap[r].length; c++) {
              if (
                newMap[r][c]?.id === data.node_id &&
                newMap[r][c].type === "spot"
              ) {
                newMap[r][c].occupied = data.status === "OCCUPIED";
                newMap[r][c].reserved = data.status === "RESERVED";
              }
            }
          }

          return newMap;
        });
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    });

    eventSource.addEventListener("error", () => {
      console.warn("SSE error (PO)");
      eventSource.close();
    });

    return () => eventSource.close();
  }, [mapData, lot_id]);

  // Helper to calculate distance between two touch points
  const getDistance = (touches) => {
    if (touches.length < 2) return null;
    const [t1, t2] = touches;
    return Math.sqrt((t1.pageX - t2.pageX) ** 2 + (t1.pageY - t2.pageY) ** 2);
  };

  // Handle pinch-to-zoom gestures
  const handleTouchStart = (e) => {
    const touches = e.nativeEvent.touches;
    if (touches.length === 2) {
      initialDistance.current = getDistance(touches);
      initialZoomRef.current = currentScaleValue.current;
    }
  };

  // Handle pinch-to-zoom gestures
  const handleTouchMove = (e) => {
    const touches = e.nativeEvent.touches;
    if (touches.length === 2 && initialDistance.current) {
      const currentDistance = getDistance(touches);
      const ratio = currentDistance / initialDistance.current;
      let newScale = initialZoomRef.current * ratio;

      newScale = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, newScale));

      animatedScale.setValue(newScale);
      currentScaleValue.current = newScale;
    }
  };

  // Reset pinch-to-zoom state
  const handleTouchEnd = () => {
    initialDistance.current = null;
  };

  // Set up pan responder for dragging the map
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: () => {
        translateX.setOffset(lastOffset.current.x);
        translateY.setOffset(lastOffset.current.y);
        translateX.setValue(0);
        translateY.setValue(0);
      },
      onPanResponderMove: Animated.event(
        [null, { dx: translateX, dy: translateY }],
        { useNativeDriver: false },
      ),
      onPanResponderRelease: () => {
        translateX.flattenOffset();
        translateY.flattenOffset();

        lastOffset.current = {
          x: translateX.__getValue(),
          y: translateY.__getValue(),
        };
      },
    }),
  ).current;

  const handleGoBack = () => router.back();

  // Navigate to historic occupancy page
  const handleViewHistoric = () => {
    router.push({
      pathname: "/historic-occupancy",
      params: { lot_id },
    });
  };

  const ROWS = mapData.length || 1;
  const COLS = mapData[0]?.length || 1;

  const MAP_PX_WIDTH = step(COLS);
  const MAP_PX_HEIGHT = step(ROWS);

  // Render the parking lot cells
  const renderCells = () => {
    const items = [];

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

        if (cell.type === "entry" || cell.type === "exit") {
          items.push(
            <View
              key={`entry-${r}-${c}`}
              style={[PARKINGLOT.cell, { left, top, backgroundColor: bg }]}
            >
              <ThemedText style={PARKINGLOT.entryExitLabel}>
                {cell.type === "entry" ? "ENTRY" : "EXIT"}
              </ThemedText>
            </View>,
          );
          continue;
        }

        if (cell.type === "spot") {
          const orientation = cell.orientation ?? 0;

          let width = CELL_SIZE;
          let height = CELL_SIZE;
          let offsetX = 0;
          let offsetY = 0;

          if (orientation === 0) {
            height = CELL_SIZE * 2;
            offsetY = -CELL_SIZE;
          } else if (orientation === 90) {
            width = CELL_SIZE * 2;
          } else if (orientation === 180) {
            height = CELL_SIZE * 2;
          } else if (orientation === 270) {
            width = CELL_SIZE * 2;
            offsetX = -CELL_SIZE;
          }

          items.push(
            <View
              key={`spot-${r}-${c}`}
              style={[
                PARKINGLOT.cell,
                PARKINGLOT.spotCell,
                {
                  left: left + offsetX,
                  top: top + offsetY,
                  width,
                  height,
                  backgroundColor: bg,
                },
              ]}
            >
              <View
                style={{
                  transform: [
                    {
                      rotate: ["1", "4"].includes(String(lot_id))
                        ? "0deg"
                        : "-90deg",
                    },
                  ],
                  width: "100%",
                  alignItems: "center",
                }}
              >
                <ThemedText style={PARKINGLOT.spotLabel}>
                  {cell.label}
                </ThemedText>
              </View>
            </View>,
          );
          continue;
        }

        items.push(
          <View
            key={`cell-${r}-${c}`}
            style={[PARKINGLOT.cell, { left, top, backgroundColor: bg }]}
          />,
        );
      }
    }

    return items;
  };

  return (
    <ThemedView style={PARKINGLOT.container}>
      {loading ? (
        <ThemedText>Loading parking lot...</ThemedText>
      ) : (
        <Animated.View
          {...panResponder.panHandlers}
          style={[
            PARKINGLOT.canvas,
            {
              width: MAP_PX_WIDTH,
              height: MAP_PX_HEIGHT,
              transform: [
                { translateX },
                { translateY },
                { scale: animatedScale },
                { rotate: mapRotation },
              ],
            },
          ]}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          {renderCells()}
        </Animated.View>
      )}

      {/* Overlay Regions */}
      <View style={PARKINGLOT.overlay} pointerEvents="box-none">
        {/* Top controls */}
        <View style={PARKINGLOT.topOverlay}>
          <Spacer height={70} />
          <View style={PARKINGLOT.topControlRow}>
            <Button
              mode="text"
              onPress={handleGoBack}
              icon="chevron-left"
              labelStyle={PARKINGLOT.backButtonLabel}
              style={PARKINGLOT.backButton}
              testID="pl-back-btn"
            >
              Back
            </Button>
          </View>
        </View>

        {/* Bottom controls */}
        <View style={PARKINGLOT.bottomOverlay}>
          <Button
            mode="contained"
            style={PARKINGLOT.primaryActionButton}
            labelStyle={PARKINGLOT.primaryLabel}
            onPress={handleViewHistoric}
            testID="histocc-btn"
          >
            View Historic Occupancy
          </Button>
        </View>
      </View>
    </ThemedView>
  );
};

ParkingLotPO.propTypes = {
  lot_id: PropTypes.string,
};

export default ParkingLotPO;
