import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { AircraftStatus } from "../../types/AircraftStatus";
import { Route } from "../../types/Route";
import { RootState } from "../store";
import { Waypoint } from "../../types/Waypoint";

// DataState holds actual information that is supposed to be aligned with backend.
type DataState = {
    aircraftStatus: AircraftStatus;
    availableRoutes: Route[];
    currentRouteId: number | null;
};

const initialState: DataState = {
    aircraftStatus: {
        timestamp: new Date().getTime(),
        latitude: 0,
        longitude: 0,
        altitude: 100,
        verticalSpeed: 100,
        speed: 100,
        heading: 90,
        voltage: 9,
    },
    availableRoutes: [],
    currentRouteId: null,
};

const dataSlice = createSlice({
    name: "data",
    initialState,
    reducers: {
        updateAircraftStatus: (state, action: PayloadAction<AircraftStatus>) => {
            state.aircraftStatus = action.payload;
        },
        loadAvailableRoutes: (state, action: PayloadAction<Route[]>) => {
            state.availableRoutes = action.payload;
        },
        setCurrentRoute: (state, action: PayloadAction<Route>) => {
            const routeIndex = state.availableRoutes.findIndex((r) => r.id === action.payload.id);
            if (routeIndex !== -1) {
                state.availableRoutes[routeIndex] = action.payload;
            } else {
                state.availableRoutes.push(action.payload);
            }
            state.currentRouteId = action.payload.id;
        },
        addRoute: (state, action: PayloadAction<Route>) => {
            state.availableRoutes.push(action.payload);
        },
        removeRoute: (state, action: PayloadAction<number>) => {
            state.availableRoutes = state.availableRoutes.filter((route) => route.id !== action.payload);
            if (state.currentRouteId === action.payload) {
                state.currentRouteId = null;
            }
        },
        updateRouteInList: (state, action: PayloadAction<Route>) => {
            const index = state.availableRoutes.findIndex((r) => r.id === action.payload.id);
            if (index !== -1) {
                state.availableRoutes[index] = action.payload;
            }
        },
        updateCurrentRouteName: (state, action: PayloadAction<string>) => {
            if (state.currentRouteId !== null) {
                const route = state.availableRoutes.find((r) => r.id === state.currentRouteId);
                if (route) {
                    route.name = action.payload;
                }
            }
        },
        updateCurrentRouteWaypoints: (state, action: PayloadAction<Waypoint[]>) => {
            if (state.currentRouteId !== null) {
                const route = state.availableRoutes.find((r) => r.id === state.currentRouteId);
                if (route) {
                    route.waypoints = action.payload;
                }
            }
        },
        addWaypointToCurrentRoute: (state, action: PayloadAction<Waypoint>) => {
            if (state.currentRouteId !== null) {
                const route = state.availableRoutes.find((r) => r.id === state.currentRouteId);
                if (route) {
                    route.waypoints.push(action.payload);
                }
            }
        },
        editWaypointInCurrentRoute: (state, action: PayloadAction<{ index: number; waypoint: Waypoint }>) => {
            if (state.currentRouteId !== null) {
                const route = state.availableRoutes.find((r) => r.id === state.currentRouteId);
                if (route) {
                    route.waypoints[action.payload.index] = action.payload.waypoint;
                }
            }
        },
        deleteWaypointFromCurrentRoute: (state, action: PayloadAction<number>) => {
            if (state.currentRouteId !== null) {
                const route = state.availableRoutes.find((r) => r.id === state.currentRouteId);
                if (route) {
                    route.waypoints.splice(action.payload, 1);
                }
            }
        },
    },
});

export const {
    updateAircraftStatus,
    loadAvailableRoutes,
    setCurrentRoute,
    addRoute,
    removeRoute,
    updateRouteInList,
    updateCurrentRouteName,
    updateCurrentRouteWaypoints,
    addWaypointToCurrentRoute,
    editWaypointInCurrentRoute,
    deleteWaypointFromCurrentRoute,
} = dataSlice.actions;

export const selectAircraftStatus = (state: RootState) => state.data.aircraftStatus;
export const selectAvailableRoutes = (state: RootState) => state.data.availableRoutes;
export const selectCurrentRoute = (state: RootState) =>
    state.data.availableRoutes.find((r) => r.id === state.data.currentRouteId) ?? null;
export const selectCurrentRouteWaypoints = (state: RootState) =>
    state.data.availableRoutes.find((r) => r.id === state.data.currentRouteId)?.waypoints ?? [];

const dataReducer = dataSlice.reducer;
export default dataReducer;
