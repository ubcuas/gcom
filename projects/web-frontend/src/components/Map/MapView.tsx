import { Flight, Place } from "@mui/icons-material";
import { Box } from "@mui/material";
import { Fragment, useEffect } from "react";
import Map, { Layer, LayerProps, Marker, Source } from "react-map-gl/maplibre";
import {
    initializeMpsWaypointMapState,
    selectMapCenterCoords,
    selectMpsWaypointMapState,
    toggleMpsWaypointMapState,
} from "../../store/slices/appSlice";
import { selectAircraftStatus, selectMPSWaypoints } from "../../store/slices/dataSlice";
import { useAppDispatch, useAppSelector } from "../../store/store";
import WaypointItem from "../WaypointItem";

export default function MapView() {
    const mpsWaypoints = useAppSelector(selectMPSWaypoints);
    const mpsWaypointMapState = useAppSelector(selectMpsWaypointMapState);
    const aircraftStatus = useAppSelector(selectAircraftStatus);
    const coords = useAppSelector(selectMapCenterCoords);
    const dispatch = useAppDispatch();
    const KEY = import.meta.env.VITE_MAPTILER_KEY as string;

    useEffect(() => {
        dispatch(initializeMpsWaypointMapState(mpsWaypoints.length));
    }, []);

    const routeData: GeoJSON.GeoJSON = {
        type: "LineString",
        coordinates: mpsWaypoints.map((waypoint) => [waypoint.longitude, waypoint.latitude]),
    };
    const routeStyle: LayerProps = {
        id: "mps-route",
        type: "line",
        paint: {
            "line-color": "#ee4455",
            "line-width": 3,
        },
    };

    return (
        <Box
            sx={{
                height: "100%",
                width: "calc(100vw - 56px)", // 56px is the width of the vertical tabs
            }}
        >
            <Map
                initialViewState={{
                    longitude: coords.longitude,
                    latitude: coords.latitude,
                    zoom: 10,
                }}
                mapStyle={
                    window.navigator.onLine
                        ? `https://api.maptiler.com/maps/basic-v2/style.json?key=${KEY}`
                        : "http://localhost:8000/api/map-tiles/osmbright"
                }
                doubleClickZoom={false}
            >
                {mpsWaypoints.map((waypoint, i) => (
                    <Fragment key={i}>
                        <Marker
                            latitude={waypoint.latitude}
                            longitude={waypoint.longitude}
                            onClick={() => dispatch(toggleMpsWaypointMapState(i))}
                            style={{
                                cursor: "pointer",
                            }}
                        >
                            <Place
                                sx={{
                                    color: "#ee4455",
                                    fontSize: "48px",
                                    position: "absolute",
                                    top: "-46px",
                                    left: "-24px",
                                }}
                            />
                            <Box
                                sx={{
                                    background: "#ee4455",
                                    height: "18px",
                                    width: "12px",
                                    position: "absolute",
                                    left: "-6px",
                                    top: "-36px",
                                    textAlign: "center",
                                    fontWeight: "bold",
                                    fontSize: "18px",
                                }}
                            >
                                {i + 1}
                            </Box>
                        </Marker>
                        {mpsWaypointMapState[i] && (
                            <Marker latitude={waypoint.latitude} longitude={waypoint.longitude}>
                                <WaypointItem
                                    sx={{
                                        position: "absolute",
                                        width: "180px",
                                        top: "10px",
                                    }}
                                    waypoint={waypoint}
                                />
                            </Marker>
                        )}
                    </Fragment>
                ))}
                <Marker latitude={aircraftStatus.latitude} longitude={aircraftStatus.longitude}>
                    <Flight
                        sx={{
                            color: "primary.main",
                            rotate: `${aircraftStatus.heading}deg`,
                            fontSize: "48px",
                        }}
                    />
                </Marker>
                <Source type="geojson" data={routeData}>
                    <Layer {...routeStyle} />
                </Source>
            </Map>
        </Box>
    );
}
