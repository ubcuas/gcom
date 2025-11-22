/**
 * Based on the Drone struct in GCOM-2023.
 */

import { FrontendWaypoint } from "../schemas/waypoint";

// maybe not needed idk
export enum Designation {
    Launch = "launch",
    Land = "land",
    Obstacle = "obstacle",
    Payload = "payload",
}

export type Waypoint = FrontendWaypoint;

export type WaypointEditState = {
    index: number;
    waypoint?: Waypoint;
};
