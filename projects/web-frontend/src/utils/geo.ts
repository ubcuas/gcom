import type { NoFlyZone } from "../api/endpoints";

export const createCircleCoordinates = (zone: NoFlyZone): [number, number][] => {
    const coordinates: [number, number][] = [];
    const earthRadiusMeters = 6_378_137;
    const latitudeRadians = (zone.latitude * Math.PI) / 180;

    for (let index = 0; index <= 64; index += 1) {
        const angle = (index / 64) * 2 * Math.PI;
        const latitudeOffset = (zone.radius_m / earthRadiusMeters) * (180 / Math.PI) * Math.sin(angle);
        const longitudeOffset =
            (zone.radius_m / (earthRadiusMeters * Math.cos(latitudeRadians))) * (180 / Math.PI) * Math.cos(angle);
        coordinates.push([zone.longitude + longitudeOffset, zone.latitude + latitudeOffset]);
    }

    return coordinates;
};
