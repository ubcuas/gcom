import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { AircraftStatus } from "../../types/AircraftStatus";
import { Route } from "../../types/Route";
import { RootState } from "../store";
import { Waypoint } from "../../types/Waypoint";

// DataState holds actual information that is supposed to be aligned with backend.
type DataState = {
    aircraftStatus: AircraftStatus;
    availableRoutes: Route[];
    currentRoute: Route | null;
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
    currentRoute: null,
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
            state.currentRoute = action.payload;
        },
        addRoute: (state, action: PayloadAction<Route>) => {
            state.availableRoutes.push(action.payload);
        },
        removeRoute: (state, action: PayloadAction<number>) => {
            state.availableRoutes = state.availableRoutes.filter((route) => route.id !== action.payload);
            if (state.currentRoute?.id === action.payload) {
                state.currentRoute = null;
            }
        },
        updateCurrentRouteName: (state, action: PayloadAction<string>) => {
            if (state.currentRoute) {
                state.currentRoute.name = action.payload;
                const routeIndex = state.availableRoutes.findIndex((r) => r.id === state.currentRoute!.id);
                if (routeIndex !== -1) {
                    state.availableRoutes[routeIndex].name = action.payload;
                }
            }
        },
        updateCurrentRouteWaypoints: (state, action: PayloadAction<Waypoint[]>) => {
            if (state.currentRoute) {
                state.currentRoute.waypoints = action.payload;
                const routeIndex = state.availableRoutes.findIndex((r) => r.id === state.currentRoute!.id);
                if (routeIndex !== -1) {
                    state.availableRoutes[routeIndex].waypoints = action.payload;
                }
            }
        },
        addWaypointToCurrentRoute: (state, action: PayloadAction<Waypoint>) => {
            if (state.currentRoute) {
                state.currentRoute.waypoints.push(action.payload);
                const routeIndex = state.availableRoutes.findIndex((r) => r.id === state.currentRoute!.id);
                if (routeIndex !== -1) {
                    state.availableRoutes[routeIndex].waypoints.push(action.payload);
                }
            }
        },
        editWaypointInCurrentRoute: (state, action: PayloadAction<{ index: number; waypoint: Waypoint }>) => {
            if (state.currentRoute) {
                state.currentRoute.waypoints[action.payload.index] = action.payload.waypoint;
                const routeIndex = state.availableRoutes.findIndex((r) => r.id === state.currentRoute!.id);
                if (routeIndex !== -1) {
                    state.availableRoutes[routeIndex].waypoints[action.payload.index] = action.payload.waypoint;
                }
            }
        },
        deleteWaypointFromCurrentRoute: (state, action: PayloadAction<number>) => {
            if (state.currentRoute) {
                state.currentRoute.waypoints.splice(action.payload, 1);
                const routeIndex = state.availableRoutes.findIndex((r) => r.id === state.currentRoute!.id);
                if (routeIndex !== -1) {
                    state.availableRoutes[routeIndex].waypoints.splice(action.payload, 1);
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
    updateCurrentRouteName,
    updateCurrentRouteWaypoints,
    addWaypointToCurrentRoute,
    editWaypointInCurrentRoute,
    deleteWaypointFromCurrentRoute,
} = dataSlice.actions;

export const selectAircraftStatus = (state: RootState) => state.data.aircraftStatus;
export const selectAvailableRoutes = (state: RootState) => state.data.availableRoutes;
export const selectCurrentRoute = (state: RootState) => state.data.currentRoute;
export const selectCurrentRouteWaypoints = (state: RootState) => state.data.currentRoute?.waypoints ?? [];

const dataReducer = dataSlice.reducer;
export default dataReducer;
