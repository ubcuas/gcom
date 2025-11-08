import { Waypoint } from "./Waypoint";

export type FormState = Record<keyof Omit<Waypoint, "id">, string>;

export type FormErrors = {
    latitude: boolean;
    longitude: boolean;
    alt: boolean;
};

export type FormKeys = keyof FormState & keyof FormErrors;
