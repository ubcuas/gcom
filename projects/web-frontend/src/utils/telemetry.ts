import { AircraftStatus } from "../types/AircraftStatus";

export const roundValues = (
    data: Omit<AircraftStatus, "verticalSpeed" | "speed" | "armed"> & {
        vertical_velocity: number;
        velocity: number;
        armed: boolean;
    },
) => {
    return {
        timestamp: Math.round(data.timestamp),
        latitude: Math.round(data.latitude * 1000000) / 1000000,
        longitude: Math.round(data.longitude * 1000000) / 1000000,
        altitude: Math.round(data.altitude),
        verticalSpeed: Math.round(data.vertical_velocity * 100) / 100,
        speed: Math.round(data.velocity * 100) / 100,
        heading: Math.round(data.heading),
        voltage: Math.round(data.voltage * 100) / 100,
        armed: data.armed,
        flightmode: data.flightmode,
    } satisfies AircraftStatus;
};
