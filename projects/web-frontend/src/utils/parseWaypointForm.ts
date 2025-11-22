import { Waypoint } from "../types/Waypoint";
import { FormState } from "../types/WaypointForm";

const parseOptionalFloat = (field: string) => {
    const parsed = parseFloat(field);
    return Number.isNaN(parsed) ? undefined : parsed;
};

export default function parseWaypointForm(formState: FormState, existingWaypoint?: Waypoint): Waypoint {
    return {
        lat: parseFloat(formState.lat),
        long: parseFloat(formState.long),
        alt: parseOptionalFloat(formState.alt),
        radius: parseOptionalFloat(formState.radius),
        name: formState.name.trim(),
        remarks: formState.remarks.trim(),
        command: formState.command.trim(),
        ardupilot_param2: parseOptionalFloat(formState.ardupilot_param2),
        ardupilot_param3: parseOptionalFloat(formState.ardupilot_param3),
        id: existingWaypoint?.id ?? "-1",
        order: existingWaypoint?.order,
        route: existingWaypoint?.route,
    };
}
