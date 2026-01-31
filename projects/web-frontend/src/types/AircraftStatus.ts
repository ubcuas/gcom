import { z } from "zod";
import { Payload } from "./Payload";

/**
 * Schema for the incoming drone data from the mission planner.
 * This matches the format sent over the socket with snake_case fields.
 */
export const incomingDroneDataSchema = z.object({
    timestamp: z.number(),
    latitude: z.number(),
    longitude: z.number(),
    altitude: z.number(),
    relative_altitude: z.number(),
    vertical_velocity: z.number(),
    velocity: z.number(),
    heading: z.number(),
    battery_voltage: z.number(),
    armed: z.boolean(),
    flightmode: z.string().nullable(),
});

/**
 * Schema for the AircraftStatus type used throughout the frontend.
 * This uses camelCase naming convention.
 */
export const aircraftStatusSchema = z.object({
    timestamp: z.number(),
    latitude: z.number(),
    longitude: z.number(),
    altitude: z.number(),
    relativeAltitude: z.number(),
    verticalSpeed: z.number(),
    speed: z.number(),
    heading: z.number(),
    voltage: z.number(),
    armed: z.boolean(),
    flightmode: z.string().nullable(),
    payload: z.array(z.custom<Payload>()).optional(),
});

/**
 * Based on the Drone struct in GCOM-2023.
 * This type is inferred from the Zod schema to ensure consistency.
 */
export type AircraftStatus = z.infer<typeof aircraftStatusSchema>;

/**
 * Transforms incoming drone data (snake_case) to AircraftStatus (camelCase).
 * Validates the incoming data and throws if it doesn't match the expected schema.
 */
export function parseAndTransformDroneData(data: unknown): AircraftStatus {
    const validated = incomingDroneDataSchema.parse(data);

    return {
        timestamp: validated.timestamp,
        latitude: validated.latitude,
        longitude: validated.longitude,
        altitude: validated.altitude,
        relativeAltitude: validated.relative_altitude,
        verticalSpeed: validated.vertical_velocity,
        speed: validated.velocity,
        heading: validated.heading,
        voltage: validated.battery_voltage,
        armed: validated.armed,
        flightmode: validated.flightmode,
    };
}
