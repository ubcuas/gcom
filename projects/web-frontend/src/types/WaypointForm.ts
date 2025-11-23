import { Waypoint } from "./Waypoint";

export type FormState = Record<keyof Omit<Waypoint, "id" | "order" | "route">, string>;

export type FormErrors = {
    latitude: boolean;
    longitude: boolean;
    altitude: boolean;
};

export type FormKeys = keyof FormState & keyof FormErrors;
