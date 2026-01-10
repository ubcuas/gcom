import { Waypoint } from "../types/Waypoint";
import { FormState } from "../types/WaypointForm";

const parseOptionalFloat = (field: string) => {
    const parsed = parseFloat(field);
    return Number.isNaN(parsed) ? undefined : parsed;
};

export default function parseWaypointForm(formState: FormState, existingWaypoint?: Waypoint): Waypoint {
    return {
        latitude: parseFloat(formState.latitude),
        longitude: parseFloat(formState.longitude),
        altitude: parseOptionalFloat(formState.altitude),
        radius: parseOptionalFloat(formState.radius),
        name: formState.name.trim(),
        remarks: formState.remarks.trim(),
        command: formState.command.trim(),
        param1: parseOptionalFloat(formState.param1),
        param2: parseOptionalFloat(formState.param2),
        param3: parseOptionalFloat(formState.param3),
        param4: parseOptionalFloat(formState.param4),
        id: existingWaypoint?.id ?? "-1",
        order: existingWaypoint?.order,
        route: existingWaypoint?.route,
    };
}

export function createWaypointsBlob(waypoints: Waypoint[]): Blob {
    const dataStr = JSON.stringify(waypoints, null, 2);
    return new Blob([dataStr], { type: "application/json" });
}

export function triggerDownloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}

export function parseWaypointsFromJsonText(text: string): Waypoint[] {
    const parsed = JSON.parse(text);
    if (!Array.isArray(parsed)) {
        throw new Error("Invalid waypoint file format: expected an array");
    }

    return parsed.map((wp: any) => ({
        id: wp.id !== undefined ? String(wp.id) : "-1",
        name: wp.name ?? "",
        latitude: Number(wp.latitude ?? wp.lat ?? 0),
        longitude: Number(wp.longitude ?? wp.lon ?? wp.lng ?? 0),
        altitude: Number(wp.altitude ?? 0),
        command: wp.command ?? undefined,
        param1: wp.param1 ?? undefined,
        param2: wp.param2 ?? undefined,
        param3: wp.param3 ?? undefined,
        param4: wp.param4 ?? undefined,
        remarks: wp.remarks ?? undefined,
        // preserve other optional fields if desired (radius/order/route) — add as needed
    }));
}
