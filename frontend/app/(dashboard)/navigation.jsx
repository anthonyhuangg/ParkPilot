import { useEffect, useState, useRef, useCallback } from "react";
import {
  StyleSheet,
  View,
  Dimensions,
  Animated,
  Easing,
  Alert,
} from "react-native";
import Svg, { Polygon, Polyline } from "react-native-svg";
import ThemedView from "../../components/themed-view";
import ThemedText from "../../components/themed-text";
import { API_BASE_URL } from "../../config";
import { useLocalSearchParams, useRouter } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { COLOURS, GlobalStyles } from "../../theme";

const CELL_SIZE = 60;
const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");
const lerp = (a, b, t) => a + (b - a) * t;

// Navigation screen component
export default function Navigation() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const mode = (params.mode || "spot").toString();
  const lotId = Number(params.lot_id);
  const startId = params.start ? Number(params.start) : null;
  const endId = params.end ? Number(params.end) : null;
  const currentId = params.current ? Number(params.current) : null;

  const [mapData, setMapData] = useState([]);
  const [routeCoords, setRouteCoords] = useState([]);
  const [visibleRouteCoords, setVisibleRouteCoords] = useState([]);
  const routeRef = useRef([]);

  const [loading, setLoading] = useState(true);
  const [arrived, setArrived] = useState(false);
  const wrongTurnHitRef = useRef(false);
  const [frame, setFrame] = useState({ x: 0, y: 0, angle: 0 });

  const progress = useRef(new Animated.Value(0)).current;
  const animatedAngle = useRef(new Animated.Value(0)).current;
  const segIndex = useRef(0);
  const stepTimer = useRef(null);

  const freedRef = useRef(false);
  const selectedSpotId = mode === "exit" ? currentId : endId;

  // Update routeRef when routeCoords change
  useEffect(() => {
    routeRef.current = routeCoords;
  }, [routeCoords]);

  // Get node at specific grid coordinates
  const nodeAt = useCallback((x, y) => mapData?.[x]?.[y] ?? null, [mapData]);

  // Calculate world rotation between two points
  const worldRotation = useCallback((prev, next) => {
    const [x1, y1] = prev;
    const [x2, y2] = next;
    const dx = y2 - y1;
    const dy = x2 - x1;
    const heading = Math.atan2(dy, dx);
    return -heading - Math.PI / 2;
  }, []);

  // Free spot if needed (on exit)
  const freeSpotIfNeeded = useCallback(async () => {
    if (freedRef.current || mode !== "exit" || !selectedSpotId) return;
    try {
      freedRef.current = true;
      const res = await fetch(
        `${API_BASE_URL}/api/parking/${lotId}/update_status?node_id=${selectedSpotId}&status=AVAILABLE&ttl=0`,
        { method: "POST", headers: { "Content-Type": "application/json" } },
      );
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`Free spot failed: ${res.status} ${t}`);
      }
      await AsyncStorage.multiRemove([
        "selected_spot_id",
        "selected_spot_label",
        "selected_lot_id",
      ]);
    } catch (err) {
      console.error("Error freeing spot:", err);
    }
  }, [mode, selectedSpotId, lotId]);

  // Mark spot as occupied (on parking)
  const markSpotOccupied = useCallback(async () => {
    if (!selectedSpotId) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/parking/${lotId}/update_status?node_id=${selectedSpotId}&status=OCCUPIED&ttl=0`,
        { method: "POST", headers: { "Content-Type": "application/json" } },
      );
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`Failed to mark occupied: ${res.status} ${t}`);
      }
    } catch (err) {
      console.error("Error marking spot occupied:", err);
    }
  }, [selectedSpotId, lotId]);

  // Simulate driver's next step (with possible wrong-turn injection)
  const getDriverNextStep = useCallback((prev, suggestedNext) => {
    if (!Array.isArray(prev) || !Array.isArray(suggestedNext)) {
      console.warn("Invalid next step:", prev, suggestedNext);
      return suggestedNext ?? prev ?? [0, 0];
    }
    if (prev[0] === 3 && prev[1] === 13 && !wrongTurnHitRef.current) {
      wrongTurnHitRef.current = true;
      return [4, 13];
    }
    return suggestedNext;
  }, []);

  // Fetch route from a given node ID
  const fetchRouteFromNodeId = useCallback(
    async (startNodeId) => {
      try {
        let url;
        if (mode === "exit") {
          url = `${API_BASE_URL}/api/parking/${lotId}/route-to-exit?current_node=${startNodeId}`;
        } else {
          url = `${API_BASE_URL}/api/parking/${lotId}/route?start=${startNodeId}&end=${endId}`;
        }
        const res = await fetch(url);
        const json = await res.json();
        if (json?.coords?.length > 0) {
          setRouteCoords(json.coords);
          setVisibleRouteCoords(json.coords);
          routeRef.current = json.coords;
          if (json.coords.length >= 2) {
            const initAngle = worldRotation(json.coords[0], json.coords[1]);
            animatedAngle.setValue(initAngle);
            setFrame({
              x: json.coords[0][0],
              y: json.coords[0][1],
              angle: initAngle,
            });
            segIndex.current = 0;
          } else if (json.coords.length === 1) {
            setFrame((f) => ({
              ...f,
              x: json.coords[0][0],
              y: json.coords[0][1],
            }));
            segIndex.current = 0;
          }
          return true;
        } else {
          setRouteCoords([]);
          setVisibleRouteCoords([]);
          routeRef.current = [];
          return false;
        }
      } catch (e) {
        console.error("Error fetching route:", e);
        return false;
      }
    },
    [mode, lotId, endId, worldRotation, animatedAngle],
  );

  // Animate a segment of the route
  const animateSegment = useCallback(
    async (i) => {
      const route = routeRef.current;
      if (!route || route.length < 2) {
        const startX = Math.round(frame.x);
        const startY = Math.round(frame.y);
        const curr = nodeAt(startX, startY);
        if (curr?.id) {
          const ok = await fetchRouteFromNodeId(curr.id);
          if (ok) requestAnimationFrame(() => animateSegmentRef.current(0));
        }
        return;
      }
      if (i >= route.length - 1) {
        const finalNode = route[route.length - 1];
        setFrame((f) => ({ ...f, x: finalNode[0], y: finalNode[1] }));
        setArrived(true);
        if (mode === "exit") {
          Alert.alert("Exit Complete", "You have exited the carpark.", [
            {
              text: "Return to Dashboard",
              onPress: () => router.replace("/home"),
            },
          ]);
        } else {
          await markSpotOccupied();
          setTimeout(
            () => router.replace("/(dashboard)/currently-parked"),
            800,
          );
        }
        return;
      }

      const prev = route[i];
      const suggestedNext = route[i + 1];
      if (!Array.isArray(prev) || !Array.isArray(suggestedNext)) return;

      const driverNext = getDriverNextStep(prev, suggestedNext);
      if (!Array.isArray(driverNext) || driverNext.length < 2) return;

      // Rotate towards next step
      const targetAngle = worldRotation(prev, driverNext);
      Animated.timing(animatedAngle, {
        toValue: targetAngle,
        duration: 100,
        easing: Easing.inOut(Easing.ease),
        useNativeDriver: false,
      }).start();
      const angleListener = animatedAngle.addListener(({ value }) =>
        setFrame((f) => ({ ...f, angle: value })),
      );

      // Move along segment
      progress.setValue(0);
      setFrame((f) => ({ ...f, x: prev[0], y: prev[1] }));

      const moveListener = progress.addListener(({ value }) => {
        const x = lerp(prev[0], driverNext[0], value);
        const y = lerp(prev[1], driverNext[1], value);
        setFrame((f) => ({ ...f, x, y }));

        // Trim visible route so only future path remains
        const newCoords = route.slice(i);
        newCoords[0] = [x, y];
        setVisibleRouteCoords(newCoords);

        if (i === 0 && value > 0.02) freeSpotIfNeeded();
      });

      Animated.timing(progress, {
        toValue: 1,
        duration: 600,
        easing: Easing.inOut(Easing.ease),
        useNativeDriver: false,
      }).start(async ({ finished }) => {
        progress.removeListener(moveListener);
        animatedAngle.removeListener(angleListener);
        if (!finished) return;

        // Snap to arrived grid cell
        const arrivedX = Math.round(driverNext[0]);
        const arrivedY = Math.round(driverNext[1]);
        const arrivedNode = nodeAt(arrivedX, arrivedY);

        // Deviation check
        const intendedNode = nodeAt(suggestedNext[0], suggestedNext[1]);
        const deviated =
          !arrivedNode?.id ||
          !intendedNode?.id ||
          arrivedNode.id !== intendedNode.id;

        if (deviated) {
          if (arrivedNode?.id) {
            const ok = await fetchRouteFromNodeId(arrivedNode.id);
            if (ok) {
              segIndex.current = 0;
              requestAnimationFrame(() => animateSegmentRef.current(0));
            }
            return;
          } else {
            requestAnimationFrame(() => animateSegmentRef.current(i));
            return;
          }
        }

        // Continue along route
        segIndex.current = i + 1;
        requestAnimationFrame(() =>
          animateSegmentRef.current(segIndex.current),
        );
      });
    },
    [
      frame.x,
      frame.y,
      nodeAt,
      getDriverNextStep,
      worldRotation,
      animatedAngle,
      progress,
      freeSpotIfNeeded,
      router,
      markSpotOccupied,
      fetchRouteFromNodeId,
      mode,
    ],
  );

  const animateSegmentRef = useRef(animateSegment);
  useEffect(() => {
    animateSegmentRef.current = animateSegment;
  }, [animateSegment]);

  // Initial data fetch on mount
  useEffect(() => {
    let cancelled = false;
    const fetchData = async () => {
      try {
        // Map
        const lotRes = await fetch(
          `${API_BASE_URL}/api/parking/${lotId}/nodes`,
        );
        const lotJson = await lotRes.json();

        const maxRow = Math.max(...lotJson.nodes.map((n) => n.x)) + 1;
        const maxCol = Math.max(...lotJson.nodes.map((n) => n.y)) + 1;
        const grid = Array.from({ length: maxRow }, () =>
          Array.from({ length: maxCol }, () => null),
        );
        for (const n of lotJson.nodes) grid[n.x][n.y] = n;
        if (cancelled) return;
        setMapData(grid);

        // Route
        let routeRes;
        if (mode === "exit") {
          routeRes = await fetch(
            `${API_BASE_URL}/api/parking/${lotId}/route-to-exit?current_node=${currentId}`,
          );
        } else {
          routeRes = await fetch(
            `${API_BASE_URL}/api/parking/${lotId}/route?start=${startId}&end=${endId}`,
          );
        }
        const routeJson = await routeRes.json();
        if (cancelled) return;

        if (routeJson.coords && routeJson.coords.length > 0) {
          setRouteCoords(routeJson.coords);
          setVisibleRouteCoords(routeJson.coords);
          routeRef.current = routeJson.coords;

          if (routeJson.coords.length >= 2) {
            const initAngle = worldRotation(
              routeJson.coords[0],
              routeJson.coords[1],
            );
            animatedAngle.setValue(initAngle);
            setFrame({
              x: routeJson.coords[0][0],
              y: routeJson.coords[0][1],
              angle: initAngle,
            });
          } else {
            setFrame((f) => ({
              ...f,
              x: routeJson.coords[0][0],
              y: routeJson.coords[0][1],
            }));
          }
        }
      } catch (e) {
        console.error("Fetch error:", e);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchData();

    return () => {
      cancelled = true;
      if (stepTimer.current) clearTimeout(stepTimer.current);
    };
  }, [lotId, mode, startId, endId, currentId, worldRotation, animatedAngle]);

  // Start animation when routeCoords are ready
  useEffect(() => {
    if (routeCoords.length < 1 || loading || arrived) return;
    segIndex.current = 0;
    if (routeCoords.length >= 2) {
      const initAngle = worldRotation(routeCoords[0], routeCoords[1]);
      animatedAngle.setValue(initAngle);
      setFrame({
        x: routeCoords[0][0],
        y: routeCoords[0][1],
        angle: initAngle,
      });
    } else {
      setFrame((f) => ({
        ...f,
        x: routeCoords[0][0],
        y: routeCoords[0][1],
      }));
    }
    requestAnimationFrame(() => animateSegmentRef.current(0));
  }, [routeCoords, loading, arrived, worldRotation, animatedAngle]);

  // Render the map and route
  const renderMap = () => {
    if (!mapData.length) return null;

    const { x: driverX, y: driverY, angle: driverAngle } = frame;
    const cosA = Math.cos(driverAngle);
    const sinA = Math.sin(driverAngle);
    const elements = [];

    for (let r = 0; r < mapData.length; r++) {
      for (let c = 0; c < mapData[r].length; c++) {
        const node = mapData[r][c];
        if (!node) continue;

        const dx = (c - driverY) * CELL_SIZE;
        const dy = (r - driverX) * CELL_SIZE;
        const rotX = dx * cosA - dy * sinA;
        const rotY = dx * sinA + dy * cosA;

        const baseLeft = SCREEN_WIDTH / 2 + rotX;
        const baseTop = SCREEN_HEIGHT / 2 + rotY;

        let bg = COLOURS.mapBackground;
        if (node.type === "PARKING_SPOT")
          bg =
            node.status === "OCCUPIED" ? COLOURS.occupied : COLOURS.available;
        else if (node.type === "CAR_ENTRANCE") bg = COLOURS.entrancePurple;
        else if (node.type === "CAR_EXIT") bg = COLOURS.exitDark;
        else if (node.type === "ROAD") bg = COLOURS.roadGrey;

        if (node.type === "PARKING_SPOT") {
          const orientation = node.orientation ?? 0;
          let width = CELL_SIZE;
          let height = CELL_SIZE;
          let offsetX = 0;
          let offsetY = 0;

          if (driverAngle === 0 || driverAngle * (180 / Math.PI) === -180) {
            const orientation2 =
              (orientation - driverAngle * (180 / Math.PI)) % 360;
            switch (orientation2) {
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
          } else if (driverAngle * (180 / Math.PI) === -90) {
            switch (orientation) {
              case 0:
                height = CELL_SIZE * 2;
                offsetY = -CELL_SIZE / 2;
                offsetX = -CELL_SIZE / 2;
                break;
              case 180:
                height = CELL_SIZE * 2;
                offsetY = -CELL_SIZE / 2;
                offsetX = CELL_SIZE / 2;
                break;
              case 90:
                width = CELL_SIZE * 2;
                offsetY = -CELL_SIZE / 2;
                offsetX = -CELL_SIZE / 2;
                break;
              case 270:
                width = CELL_SIZE * 2;
                offsetY = CELL_SIZE / 2;
                offsetX = -CELL_SIZE / 2;
                break;
            }
          } else {
            switch (orientation) {
              case 0:
                height = CELL_SIZE * 2;
                offsetY = -CELL_SIZE / 2;
                offsetX = CELL_SIZE / 2;
                break;
              case 180:
                height = CELL_SIZE * 2;
                offsetY = -CELL_SIZE / 2;
                offsetX = -CELL_SIZE / 2;
                break;
              case 90:
                width = CELL_SIZE * 2;
                offsetY = CELL_SIZE / 2;
                offsetX = -CELL_SIZE / 2;
                break;
              case 270:
                width = CELL_SIZE * 2;
                offsetY = -CELL_SIZE / 2;
                offsetX = -CELL_SIZE / 2;
                break;
            }
          }

          const totalRotate = -driverAngle + (Math.PI / 180) * 180;

          elements.push(
            <View
              key={`spot-${r}-${c}`}
              style={{
                position: "absolute",
                left: baseLeft + offsetX - CELL_SIZE / 2,
                top: baseTop + offsetY - CELL_SIZE / 2,
                width,
                height,
                backgroundColor: bg,
                borderWidth: 1,
                borderColor: COLOURS.black,
                borderRadius: 0,
                transform: [{ rotate: `${totalRotate}rad` }],
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              {!!node.label && (
                <ThemedText
                  style={{
                    fontWeight: "bold",
                    fontSize: 12,
                    color: COLOURS.textDark,
                  }}
                >
                  {node.label}
                </ThemedText>
              )}
            </View>,
          );
        } else {
          elements.push(
            <View
              key={`cell-${r}-${c}`}
              style={{
                position: "absolute",
                left: baseLeft - CELL_SIZE / 2,
                top: baseTop - CELL_SIZE / 2,
                width: CELL_SIZE,
                height: CELL_SIZE,
                backgroundColor: bg,
                borderWidth: node.type === "ROAD" ? 0 : 0.5,
                borderColor: COLOURS.black,
              }}
            />,
          );
        }
      }
    }

    if (visibleRouteCoords.length > 1) {
      const pathPoints = visibleRouteCoords.map(([rx, ry]) => {
        const dx = (ry - driverY) * CELL_SIZE;
        const dy = (rx - driverX) * CELL_SIZE;
        const rotX = dx * cosA - dy * sinA;
        const rotY = dx * sinA + dy * cosA;
        const px = SCREEN_WIDTH / 2 + rotX;
        const py = SCREEN_HEIGHT / 2 + rotY;
        return `${px},${py}`;
      });

      elements.push(
        <Svg
          key="route-line"
          style={StyleSheet.absoluteFill}
          pointerEvents="none"
        >
          <Polyline
            points={pathPoints.join(" ")}
            fill="none"
            stroke={COLOURS.routeBlue}
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </Svg>,
      );
    }

    return elements;
  };

  // Render driver's directional arrow
  const renderArrow = () => {
    const size = 35;
    const cx = SCREEN_WIDTH / 2;
    const cy = SCREEN_HEIGHT / 2;
    return (
      <View
        style={{
          position: "absolute",
          left: cx - size / 2,
          top: cy - size / 2,
          zIndex: 1000,
        }}
      >
        <Svg width={size} height={size} viewBox="0 0 24 24">
          <Polygon
            points="12,2 22,22 12,17 2,22"
            fill={COLOURS.routeBlue}
            stroke={COLOURS.white}
            strokeWidth="1"
          />
        </Svg>
      </View>
    );
  };

  return (
    <ThemedView style={GlobalStyles.navigationScreen}>
      {loading ? (
        <ThemedText>Loading route...</ThemedText>
      ) : (
        <>
          {renderMap()}
          {renderArrow()}
        </>
      )}
    </ThemedView>
  );
}
