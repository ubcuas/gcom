import { Waypoint } from "../types/Waypoint";
import { Route } from "../types/Route";
import api from "./api";
import { WaypointSchema, RouteSchema, PartialWaypointSchema } from "../schemas/waypoint";

// TODO: Implement new endpoint logic

export const armDrone = async (arm: boolean) => {
    return await api.put("/drone/arm", { arm });
};

export const takeoffDrone = async (altitude?: number) => {
    return await api.post("/drone/takeoff", { altitude });
};

export const prepareTakeoffDrone = async (altitude: number) => {
    return await api.post("/drone/prepare_takeoff", { altitude });
};

export const returnToLaunch = async () => {
    return await api.post("/drone/rtl");
};

export const postWaypointsToDrone = async (waypoints: Waypoint[]) => {
    console.log("Preparing to post waypoints to drone via API", waypoints);
    return await api.post("/drone/queue", waypoints);
};

export const getGCOM = async (): Promise<Waypoint[]> => {
    const response = await api.get("/drone/queue");
    return response.data.map((wp: unknown) => WaypointSchema.parse(wp));
};

export const listRoutes = async (): Promise<Route[]> => {
    const response = await api.get("/route/");
    return response.data.map((route: unknown) => RouteSchema.parse(route));
};

export const getRouteById = async (id: number): Promise<Route> => {
    const response = await api.get(`/route/${id}/`);
    return RouteSchema.parse(response.data);
};

export const createRoute = async (name: string): Promise<Route> => {
    const response = await api.post("/route/", { name });
    return RouteSchema.parse(response.data);
};

export const deleteRoute = async (id: number): Promise<void> => {
    await api.delete(`/route/${id}/`);
};

export const updateRouteName = async (id: number, name: string): Promise<Route> => {
    const response = await api.put(`/route/${id}/`, { name });
    return RouteSchema.parse(response.data);
};

export const addWaypointToRoute = async (
    routeId: number,
    waypoint: Omit<Waypoint, "id">,
    order: number,
): Promise<Waypoint> => {
    console.log("Adding waypoint to route via API", routeId, waypoint, order);
    const validatedWaypoint = PartialWaypointSchema.parse(waypoint);
    const response = await api.post("/waypoint/", {
        ...validatedWaypoint,
        route: routeId,
        order,
    });
    return WaypointSchema.parse(response.data);
};

export const updateWaypoint = async (
    waypointId: string,
    waypoint: Partial<Omit<Waypoint, "id">>,
): Promise<Waypoint> => {
    console.log("Updating waypoint via API", waypointId, waypoint);
    const validatedWaypoint = PartialWaypointSchema.parse(waypoint);
    const response = await api.put(`/waypoint/${waypointId}/`, validatedWaypoint);
    return WaypointSchema.parse(response.data);
};

export const deleteWaypoint = async (waypointId: string): Promise<void> => {
    await api.delete(`/waypoint/${waypointId}/`);
};

export const reorderWaypoints = async (routeId: number, waypointIds: string[]): Promise<void> => {
    await api.post(`/route/${routeId}/reorder-waypoints/`, waypointIds);
};

export const syncRouteWaypoints = async (routeId: number, waypoints: Waypoint[]): Promise<Route> => {
    console.log("Syncing waypoints via API", routeId, waypoints);
    const response = await api.post(`/route/${routeId}/sync-waypoints/`, waypoints);
    return RouteSchema.parse(response.data);
};

export const getDroneParameter = async (
    paramId: string,
): Promise<{ param_id: string; param_value: number; param_type: number }> => {
    const response = await api.get(`/drone/parameters/${paramId}`);
    return response.data;
};

export const getFlightMode = async (): Promise<{ mode: string }> => {
    const response = await api.get("/drone/flightmode");
    return response.data;
};
