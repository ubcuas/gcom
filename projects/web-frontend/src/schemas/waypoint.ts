import { z } from "zod";

// Frontend waypoint format (using lat, long, alt)
export const FrontendWaypointSchema = z.object({
    id: z.string(),
    name: z.string().optional(),
    lat: z.number(),
    long: z.number(),
    alt: z.number().optional(),
    radius: z.number().optional(),
    remarks: z.string().optional(),
    command: z.string().optional(),
    param1: z.number().optional(),
    param2: z.number().optional(),
    param3: z.number().optional(),
    param4: z.number().optional(),
    order: z.number().optional(),
    route: z.number().optional(),
});

// Backend waypoint format (using latitude, longitude, altitude)
const BackendWaypointSchema = z.object({
    id: z.string(),
    name: z.string().optional(),
    latitude: z.number(),
    longitude: z.number(),
    altitude: z.number().optional(),
    radius: z.number().optional(),
    remarks: z.string().optional(),
    command: z.string().optional(),
    param1: z.number().optional(),
    param2: z.number().optional(),
    param3: z.number().optional(),
    param4: z.number().optional(),
    order: z.number(),
    route: z.number(),
});

// Serialize frontend format to backend format
export const serializeWaypoint = FrontendWaypointSchema.transform((data) => ({
    id: data.id,
    name: data.name,
    latitude: data.lat,
    longitude: data.long,
    altitude: data.alt,
    radius: data.radius,
    remarks: data.remarks,
    command: data.command,
    param1: data.param1,
    param2: data.param2,
    param3: data.param3,
    param4: data.param4,
    order: data.order,
    route: data.route,
}));

// Deserialize backend format to frontend format
export const deserializeWaypoint = BackendWaypointSchema.transform((data) => ({
    id: data.id,
    name: data.name,
    lat: data.latitude,
    long: data.longitude,
    alt: data.altitude,
    radius: data.radius,
    remarks: data.remarks,
    command: data.command,
    param1: data.param1,
    param2: data.param2,
    param3: data.param3,
    param4: data.param4,
    order: data.order,
    route: data.route,
}));

// For partial waypoint data (when creating/updating)
export const PartialFrontendWaypointSchema = FrontendWaypointSchema.omit({ id: true }).partial();

export const serializePartialWaypoint = PartialFrontendWaypointSchema.transform((data) => {
    const result: Record<string, unknown> = {};

    if (data.name !== undefined) result.name = data.name;
    if (data.lat !== undefined) result.latitude = data.lat;
    if (data.long !== undefined) result.longitude = data.long;
    if (data.alt !== undefined) result.altitude = data.alt;
    if (data.radius !== undefined) result.radius = data.radius;
    if (data.remarks !== undefined) result.remarks = data.remarks;
    if (data.command !== undefined) result.command = data.command;
    if (data.param1 !== undefined) result.param1 = data.param1;
    if (data.param2 !== undefined) result.param2 = data.param2;
    if (data.param3 !== undefined) result.param3 = data.param3;
    if (data.param4 !== undefined) result.param4 = data.param4;
    if (data.order !== undefined) result.order = data.order;
    if (data.route !== undefined) result.route = data.route;

    return result;
});

// Route schemas
const BackendRouteSchema = z.object({
    id: z.number(),
    name: z.string(),
    waypoints: z.array(BackendWaypointSchema),
});

export const deserializeRoute = BackendRouteSchema.transform((data) => ({
    id: data.id,
    name: data.name,
    waypoints: data.waypoints.map((wp) => deserializeWaypoint.parse(wp)),
}));

// Type exports
export type FrontendWaypoint = z.infer<typeof FrontendWaypointSchema>;
export type BackendWaypoint = z.infer<typeof BackendWaypointSchema>;
export type BackendWaypointInput = z.input<typeof deserializeWaypoint>;
export type FrontendWaypointOutput = z.output<typeof serializeWaypoint>;
