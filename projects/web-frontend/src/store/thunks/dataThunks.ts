import { createAsyncThunk } from "@reduxjs/toolkit";
import {
    listRoutes,
    getRouteById,
    createRoute as apiCreateRoute,
    deleteRoute as apiDeleteRoute,
    updateRouteName,
    addWaypointToRoute,
    updateWaypoint,
    deleteWaypoint as apiDeleteWaypoint,
    reorderWaypoints,
} from "../../api/endpoints";
import { loadAvailableRoutes, setCurrentRoute, addRoute, removeRoute } from "../slices/dataSlice";
import { RootState } from "../store";
import { Waypoint } from "../../types/Waypoint";
import { extractAxiosError } from "../../utils/errorHandling";

export const fetchAllRoutes = createAsyncThunk("data/fetchAllRoutes", async (_, { dispatch, rejectWithValue }) => {
    try {
        const routes = await listRoutes();
        dispatch(loadAvailableRoutes(routes));
        return routes;
    } catch (error) {
        return rejectWithValue(extractAxiosError(error));
    }
});

export const fetchRouteById = createAsyncThunk(
    "data/fetchRouteById",
    async (id: number, { dispatch, rejectWithValue }) => {
        try {
            const route = await getRouteById(id);
            dispatch(setCurrentRoute(route));
            return route;
        } catch (error) {
            return rejectWithValue(extractAxiosError(error));
        }
    },
);

export const createNewRoute = createAsyncThunk(
    "data/createNewRoute",
    async (name: string, { dispatch, rejectWithValue }) => {
        try {
            const route = await apiCreateRoute(name);
            dispatch(addRoute(route));
            return route;
        } catch (error) {
            return rejectWithValue(extractAxiosError(error));
        }
    },
);

export const deleteRouteById = createAsyncThunk(
    "data/deleteRouteById",
    async (id: number, { dispatch, rejectWithValue }) => {
        try {
            await apiDeleteRoute(id);
            dispatch(removeRoute(id));
        } catch (error) {
            return rejectWithValue(extractAxiosError(error));
        }
    },
);

export const switchToRoute = createAsyncThunk(
    "data/switchToRoute",
    async (id: number, { dispatch, rejectWithValue }) => {
        try {
            const route = await getRouteById(id);
            dispatch(setCurrentRoute(route));
            return route;
        } catch (error) {
            return rejectWithValue(extractAxiosError(error));
        }
    },
);

export const saveCurrentRouteToBackend = createAsyncThunk(
    "data/saveCurrentRouteToBackend",
    async (_, { getState, dispatch, rejectWithValue }) => {
        try {
            const state = getState() as RootState;
            const currentRoute = state.data.currentRoute;

            if (!currentRoute) {
                return rejectWithValue({ message: "No current route to save" });
            }

            const routeId = currentRoute.id;
            const existingRoute = state.data.availableRoutes.find((r) => r.id === routeId);

            if (!existingRoute) {
                return rejectWithValue({ message: "Current route not found in available routes" });
            }

            // Update route name if changed
            if (currentRoute.name !== existingRoute.name) {
                await updateRouteName(routeId, currentRoute.name);
            }

            // Sync waypoints
            const updatedWaypoints: Waypoint[] = [];
            for (let i = 0; i < currentRoute.waypoints.length; i++) {
                const waypoint = currentRoute.waypoints[i];
                let savedWaypoint: Waypoint;

                // Check if waypoint is new (id is "-1" or negative number as string)
                if (waypoint.id === "-1" || parseInt(waypoint.id) < 0) {
                    // Create new waypoint
                    const { id: _id, ...waypointData } = waypoint;
                    savedWaypoint = await addWaypointToRoute(routeId, waypointData, i);
                } else {
                    // Update existing waypoint
                    const { id: _id, ...waypointData } = waypoint;
                    savedWaypoint = await updateWaypoint(waypoint.id, {
                        ...waypointData,
                        order: i,
                        route: routeId,
                    });
                }
                updatedWaypoints.push(savedWaypoint);
            }

            // Handle deleted waypoints by checking what was in the backend vs what's in local state
            const currentWaypointIds = new Set(currentRoute.waypoints.map((w) => w.id));
            const deletedWaypoints = existingRoute.waypoints.filter(
                (w) => w.id !== "-1" && parseInt(w.id) >= 0 && !currentWaypointIds.has(w.id),
            );

            for (const waypoint of deletedWaypoints) {
                await apiDeleteWaypoint(waypoint.id);
            }

            // Reorder waypoints with the new IDs
            await reorderWaypoints(
                routeId,
                updatedWaypoints.map((w) => w.id),
            );

            // Fetch the updated route from backend to ensure consistency
            const updatedRoute = await getRouteById(routeId);
            dispatch(setCurrentRoute(updatedRoute));

            return updatedRoute;
        } catch (error) {
            return rejectWithValue(extractAxiosError(error));
        }
    },
);
