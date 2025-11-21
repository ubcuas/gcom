import { Waypoint } from "../types/Waypoint";
import { Route } from "../types/Route";
import api from "./api";

// TODO: Implement new endpoint logic

export const armDrone = async (arm: boolean) => {
    return await api.post("/drone/arm", { arm });
};

export const takeoffDrone = async (altitude?: number) => {
    return await api.post("/drone/takeoff", { altitude });
};

export const postWaypointsToDrone = async (waypoints: Waypoint[]) => {
    return await api.post("/drone/queue", waypoints);
};

export const getGCOM = async (): Promise<Waypoint[]> => {
    return (await api.get("/drone/queue")) as Waypoint[];
};

export const listRoutes = async (): Promise<Route[]> => {
    const response = await api.get("/route/");
    return response.data;
};

export const getRouteById = async (id: number): Promise<Route> => {
    const response = await api.get(`/route/${id}/`);
    return response.data;
};

export const createRoute = async (name: string): Promise<Route> => {
    const response = await api.post("/route/", { name });
    return response.data;
};

export const deleteRoute = async (id: number): Promise<void> => {
    await api.delete(`/route/${id}/`);
};

export const updateRouteName = async (id: number, name: string): Promise<Route> => {
    const response = await api.put(`/route/${id}/`, { name });
    return response.data;
};

export const addWaypointToRoute = async (
    routeId: number,
    waypoint: Omit<Waypoint, "id">,
    order: number,
): Promise<Waypoint> => {
    const response = await api.post("/waypoint/", {
        ...waypoint,
        route: routeId,
        order,
    });
    return response.data;
};

export const reorderWaypoints = async (routeId: number, waypointIds: string[]): Promise<void> => {
    await api.post(`/route/${routeId}/reorder-waypoints/`, waypointIds);
};
