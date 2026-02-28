import { Button, Grid, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { WaypointEditState } from "../../types/Waypoint";
import { useAppDispatch, useAppSelector } from "../../store/store";
import {
    addWaypointToCurrentRoute,
    editWaypointInCurrentRoute,
    selectCurrentRouteWaypoints,
} from "../../store/slices/dataSlice";
import { FormErrors, FormKeys, FormState } from "../../types/WaypointForm";
import parseWaypointForm from "../../utils/parseWaypointForm";
import { saveCurrentRouteToBackend } from "../../store/thunks/dataThunks";
import { openSnackbar, selectAppSlice } from "../../store/slices/appSlice.ts";

// TODO: Needs a bit of cleaning up, im sure there are better logical flows for this form.

type WaypointFormProps = {
    editState: WaypointEditState;
    clearEditState: () => void;
};

const defaultFormState: FormState = {
    latitude: "",
    longitude: "",
    altitude: "",
    name: "",
    radius: "",
    remarks: "",
    command: "",
    param1: "",
    param2: "",
    param3: "",
    param4: "",
};

export default function WaypointForm({ editState, clearEditState }: WaypointFormProps) {
    const dispatch = useAppDispatch();
    const waypoints = useAppSelector(selectCurrentRouteWaypoints);
    const settings = useAppSelector(selectAppSlice);
    const [formState, setFormState] = useState<FormState>(defaultFormState);

    const [formErrors, setFormErrors] = useState<FormErrors>({
        latitude: false,
        longitude: false,
        altitude: false,
    });

    useEffect(() => {
        if (editState.waypoint) {
            // TODO: bit ugly, could be improved in the future.
            setFormState({
                latitude: editState.waypoint.latitude ? String(editState.waypoint.latitude) : "",
                longitude: editState.waypoint.longitude ? String(editState.waypoint.longitude) : "",
                altitude: editState.waypoint.altitude ? String(editState.waypoint.altitude) : "",
                name: editState.waypoint.name ?? "No Name",
                radius: editState.waypoint.radius ? String(editState.waypoint.radius) : "",
                remarks: editState.waypoint.remarks ?? "",
                command: editState.waypoint.command ?? "",
                param1: editState.waypoint.param1 ? String(editState.waypoint.param1) : "",
                param2: editState.waypoint.param2 ? String(editState.waypoint.param2) : "",
                param3: editState.waypoint.param3 ? String(editState.waypoint.param3) : "",
                param4: editState.waypoint.param4 ? String(editState.waypoint.param4) : "",
            });
        } else {
            setFormState(defaultFormState);
        }
    }, [editState.index]);

    const checkReqFields = (keys: FormKeys[]): boolean => {
        const newFormErrors = keys.reduce((acc, key) => {
            const value = formState[key].trim();
            let hasError = value === "";

            if (!hasError) {
                if (key === "latitude") {
                    const num = Number(value);
                    hasError = Number.isNaN(num) || num < -90 || num > 90;
                } else if (key === "longitude") {
                    const num = Number(value);
                    hasError = Number.isNaN(num) || num < -180 || num > 180;
                } else if (key === "altitude") {
                    const num = Number(value);
                    hasError = Number.isNaN(num) || num <= 0;
                }
            }

            return { ...acc, [key]: hasError };
        }, formErrors);

        setFormErrors(newFormErrors);

        return keys.every((key) => !newFormErrors[key]);
    };

    const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (
            ["latitude", "longitude", "altitude", "radius", "param1", "param2", "param3", "param4"].includes(
                event.target.id,
            ) &&
            /[^0-9.-]/.test(event.target.value)
        ) {
            return;
        }
        setFormState({
            ...formState,
            [event.target.id]: event.target.value,
        });
        setFormErrors({
            ...formErrors,
            [event.target.id]: !event.target.validity.valid,
        });
    };

    const handleFormSubmit = () => {
        if (checkReqFields(["latitude", "longitude", "altitude"])) {
            const waypoint = parseWaypointForm(formState);
            if (!waypoint.name) {
                const unnamedCount = waypoints.filter((wp) => wp.name?.startsWith("Unnamed Waypoint")).length;
                waypoint.name = `Unnamed Waypoint ${unnamedCount + 1}`;
            }
            dispatch(addWaypointToCurrentRoute(waypoint));
            dispatch(saveCurrentRouteToBackend());
            const message = `Waypoint "${waypoint.name}" created at (${waypoint.latitude}, ${waypoint.longitude})`;
            dispatch(openSnackbar({ message, severity: "success" }));
        }
    };

    const cancelEditing = () => {
        clearEditState();
        setFormState(defaultFormState);
    };

    const handleFinishEditing = () => {
        const waypoint = parseWaypointForm(formState, editState.waypoint);
        dispatch(
            editWaypointInCurrentRoute({
                index: editState.index,
                waypoint,
            }),
        );
        dispatch(saveCurrentRouteToBackend());
        const message = `Edited waypoint "${waypoint.name}" at (${waypoint.latitude}, ${waypoint.longitude})`;
        dispatch(openSnackbar({ message, severity: "success" }));
        cancelEditing();
    };

    return (
        <Grid container spacing={2}>
            <Grid item xs={12}>
                <Typography variant="h6">{editState.waypoint ? "Edit" : "Create"} Waypoint</Typography>
            </Grid>
            <Grid item xs={12} lg={6}>
                <TextField
                    fullWidth
                    required
                    id="latitude"
                    type="string"
                    label="Latitude"
                    onChange={handleFormChange}
                    onWheel={preventScroll}
                    value={formState.latitude}
                    error={formErrors.latitude}
                    helperText={formErrors.latitude && "Latitude is required to be between -90 and 90."}
                />
            </Grid>
            <Grid item xs={12} lg={6}>
                <TextField
                    fullWidth
                    required
                    id="longitude"
                    type="string"
                    label="Longitude"
                    onChange={handleFormChange}
                    onWheel={preventScroll}
                    value={formState.longitude}
                    error={formErrors.longitude}
                    helperText={formErrors.longitude && "Longitude is required to be between -180 and 180."}
                />
            </Grid>
            <Grid item xs={12} lg={6}>
                <TextField
                    fullWidth
                    required
                    id="altitude"
                    type="string"
                    label="Altitude Relative to Home (m)"
                    onChange={handleFormChange}
                    onWheel={preventScroll}
                    value={formState.altitude}
                    error={formErrors.altitude}
                    helperText={formErrors.altitude && "Altitude is required to be above 0."}
                />
            </Grid>
            <Grid item xs={12} lg={6}>
                <TextField
                    fullWidth
                    id="radius"
                    type="string"
                    label="Radius"
                    value={formState.radius}
                    onChange={handleFormChange}
                    onWheel={preventScroll}
                />
            </Grid>
            <Grid item xs={12} lg={6}>
                <TextField
                    fullWidth
                    id="name"
                    label="Name"
                    autoComplete="off"
                    value={formState.name}
                    onChange={handleFormChange}
                />
            </Grid>
            <Grid item xs={12} lg={6}>
                <TextField
                    fullWidth
                    id="remarks"
                    label="Remarks"
                    autoComplete="off"
                    value={formState.remarks}
                    onChange={handleFormChange}
                />
            </Grid>
            <Grid item xs={12}>
                <TextField
                    fullWidth
                    id="command"
                    label="Command"
                    autoComplete="off"
                    value={formState.command}
                    onChange={handleFormChange}
                />
            </Grid>

            {settings.showParamValues && (
                <>
                    <Grid item xs={12} md={6} lg={3}>
                        <TextField
                            fullWidth
                            id="param1"
                            type="string"
                            label="Param 1"
                            value={formState.param1}
                            onChange={handleFormChange}
                            onWheel={preventScroll}
                        />
                    </Grid>
                    <Grid item xs={12} md={6} lg={3}>
                        <TextField
                            fullWidth
                            id="param2"
                            type="string"
                            label="Param 2"
                            value={formState.param2}
                            onChange={handleFormChange}
                            onWheel={preventScroll}
                        />
                    </Grid>
                    <Grid item xs={12} md={6} lg={3}>
                        <TextField
                            fullWidth
                            id="param3"
                            type="string"
                            label="Param 3"
                            value={formState.param3}
                            onChange={handleFormChange}
                            onWheel={preventScroll}
                        />
                    </Grid>
                    <Grid item xs={12} md={6} lg={3}>
                        <TextField
                            fullWidth
                            id="param4"
                            type="string"
                            label="Param 4"
                            value={formState.param4}
                            onChange={handleFormChange}
                            onWheel={preventScroll}
                        />
                    </Grid>
                </>
            )}
            {editState.waypoint ? (
                <>
                    <Grid item xs={12} lg={6}>
                        <Button color="secondary" fullWidth variant="outlined" onClick={cancelEditing}>
                            Cancel
                        </Button>
                    </Grid>
                    <Grid item xs={12} lg={6}>
                        <Button fullWidth variant="outlined" onClick={handleFinishEditing}>
                            Edit Waypoint
                        </Button>
                    </Grid>
                </>
            ) : (
                <Grid item xs={12}>
                    <Button fullWidth variant="outlined" onClick={handleFormSubmit}>
                        Create Waypoint
                    </Button>
                </Grid>
            )}
        </Grid>
    );
}

const preventScroll = (e: React.WheelEvent<HTMLInputElement>) => {
    if (e.target instanceof HTMLElement) {
        e.target.blur();
    }
};
