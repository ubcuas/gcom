import { Waypoint } from "./Waypoint";

export type Route = {
    id: number;
    name: string;
    waypoints: Waypoint[];
};
