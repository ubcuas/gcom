import { Waypoint } from "../types/Waypoint";
import { Route } from "../types/Route";
import api from "./api";
import {
    serializeWaypoint,
    deserializeWaypoint,
    deserializeRoute,
    serializePartialWaypoint,
} from "../schemas/waypoint";

// TODO: Implement new endpoint logic

export const armDrone = async (arm: boolean) => {
    return await api.post("/drone/arm", { arm });
};

export const takeoffDrone = async (altitude?: number) => {
    return await api.post("/drone/takeoff", { altitude });
};

export const postWaypointsToDrone = async (waypoints: Waypoint[]) => {
    const backendWaypoints = waypoints.map((wp) => serializeWaypoint.parse(wp));
    return await api.post("/drone/queue", backendWaypoints);
};

export const getGCOM = async (): Promise<Waypoint[]> => {
    const response = await api.get("/drone/queue");
    return response.data.map((wp: unknown) => deserializeWaypoint.parse(wp));
};

export const listRoutes = async (): Promise<Route[]> => {
    const response = await api.get("/route/");
    return response.data.map((route: unknown) => deserializeRoute.parse(route));
};

export const getRouteById = async (id: number): Promise<Route> => {
    const response = await api.get(`/route/${id}/`);
    return deserializeRoute.parse(response.data);
};

export const createRoute = async (name: string): Promise<Route> => {
    const response = await api.post("/route/", { name });
    return deserializeRoute.parse(response.data);
};

export const deleteRoute = async (id: number): Promise<void> => {
    await api.delete(`/route/${id}/`);
};

export const updateRouteName = async (id: number, name: string): Promise<Route> => {
    const response = await api.put(`/route/${id}/`, { name });
    return deserializeRoute.parse(response.data);
};

export const addWaypointToRoute = async (
    routeId: number,
    waypoint: Omit<Waypoint, "id">,
    order: number,
): Promise<Waypoint> => {
    const backendWaypoint = serializePartialWaypoint.parse(waypoint);
    console.log("Adding waypoint to route via API", routeId, backendWaypoint, order);
    const response = await api.post("/waypoint/", {
        ...backendWaypoint,
        route: routeId,
        order,
    });
    return deserializeWaypoint.parse(response.data);
};

export const updateWaypoint = async (
    waypointId: string,
    waypoint: Partial<Omit<Waypoint, "id">>,
): Promise<Waypoint> => {
    const backendWaypoint = serializePartialWaypoint.parse(waypoint);
    console.log("Updating waypoint via API", waypointId, backendWaypoint);
    const response = await api.put(`/waypoint/${waypointId}/`, backendWaypoint);
    return deserializeWaypoint.parse(response.data);
};

export const deleteWaypoint = async (waypointId: string): Promise<void> => {
    await api.delete(`/waypoint/${waypointId}/`);
};

export const reorderWaypoints = async (routeId: number, waypointIds: string[]): Promise<void> => {
    await api.post(`/route/${routeId}/reorder-waypoints/`, waypointIds);
};
