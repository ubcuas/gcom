import { Coords } from "../types/Coords";

export const defaultCoords: Coords = {
    // UBC
    longitude: -123.246,
    latitude: 49.2606,
};

export function validCoords(coords: Coords) {
    return (
        coords.latitude !== null &&
        coords.longitude !== null &&
        checkLat(coords.latitude) &&
        checkLong(coords.longitude)
    );
}

export function checkLat(lat: number) {
    return lat <= 90 && lat >= -90;
}

export function checkLong(long: number) {
    return long <= 180 && long >= -180;
}
