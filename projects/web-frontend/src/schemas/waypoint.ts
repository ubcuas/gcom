import { z } from "zod";

export const WaypointSchema = z.object({
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
    order: z.number().optional(),
    route: z.number().optional(),
});

export const PartialWaypointSchema = WaypointSchema.omit({ id: true }).partial();

export const RouteSchema = z.object({
    id: z.number(),
    name: z.string(),
    waypoints: z.array(WaypointSchema),
});

export type Waypoint = z.infer<typeof WaypointSchema>;
export type PartialWaypoint = z.infer<typeof PartialWaypointSchema>;
export type Route = z.infer<typeof RouteSchema>;
