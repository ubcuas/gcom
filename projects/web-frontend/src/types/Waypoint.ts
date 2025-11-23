/**
 * Based on the Drone struct in GCOM-2023.
 */

export type { Waypoint } from "../schemas/waypoint";
import type { Waypoint } from "../schemas/waypoint";

// maybe not needed idk
export enum Designation {
    Launch = "launch",
    Land = "land",
    Obstacle = "obstacle",
    Payload = "payload",
}

export type WaypointEditState = {
    index: number;
    waypoint?: Waypoint;
};
