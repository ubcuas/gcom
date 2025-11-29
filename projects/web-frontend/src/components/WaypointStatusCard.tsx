import { Box, Button, Grid, Modal, Paper, Stack, Typography } from "@mui/material";
import { useRef, useState } from "react";
import { postWaypointsToDrone } from "../api/endpoints";
import { openSnackbar, selectMapViewOpen, setMapViewOpen } from "../store/slices/appSlice";
import {
    addWaypointToCurrentRoute,
    deleteWaypointFromCurrentRoute,
    selectCurrentRouteWaypoints,
    selectCurrentRoute,
    updateCurrentRouteWaypoints,
} from "../store/slices/dataSlice";
import { saveCurrentRouteToBackend } from "../store/thunks/dataThunks";
import { useAppDispatch, useAppSelector } from "../store/store";
import { WaypointEditState } from "../types/Waypoint";
import { createErrorMessage } from "../utils/errorHandling";
import InfoCard from "./InfoCard";
import WaypointCreationMap from "./Map/WaypointCreationMap";
import WaypointItem from "./WaypointItem";
import WaypointForm from "./WaypointStatus/WaypointForm";

export default function WaypointStatusCard() {
    const dispatch = useAppDispatch();
    const waypointQueue = useAppSelector(selectCurrentRouteWaypoints);
    const currentRoute = useAppSelector(selectCurrentRoute);
    const mapViewOpen = useAppSelector(selectMapViewOpen);
    const [modalOpen, setModalOpen] = useState(false);
    const [editState, setEditState] = useState<WaypointEditState>({
        index: -1,
        waypoint: undefined,
    });
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    const handlePost = async () => {
        if (waypointQueue.length === 0) {
            return;
        }
        try {
            await postWaypointsToDrone(waypointQueue);
        } catch (error) {
            const message = createErrorMessage(error);
            dispatch(openSnackbar({ message }));
        }
    };

    const handleDeleteWaypoint = (index: number) => {
        dispatch(deleteWaypointFromCurrentRoute(index));
        dispatch(saveCurrentRouteToBackend());
        clearEditState();
    };

    const handleEditWaypoint = (index: number) => {
        setEditState({
            index,
            waypoint: waypointQueue[index],
        });
    };

    const clearEditState = () => {
        setEditState({
            index: -1,
            waypoint: undefined,
        });
    };

    const handleExportWaypoints = () => {
        if (waypointQueue.length === 0) {
            dispatch(openSnackbar({ message: "No waypoints to export" }));
            return;
        }
        try {
            const dataStr = JSON.stringify(waypointQueue, null, 2);
            const blob = new Blob([dataStr], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${currentRoute?.name || "waypoints"}-waypoints.json`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            dispatch(openSnackbar({ message: "Waypoints exported", severity: "success" }));
        } catch (error) {
            const message = createErrorMessage(error);
            dispatch(openSnackbar({ message, severity: "error" }));
        }
    };

    const handleImportClick = () => {
        fileInputRef.current?.click();
    };

    const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) {
            return;
        }
        try {
            const text = await file.text();
            const parsed = JSON.parse(text);
            if (!Array.isArray(parsed)) {
                throw new Error("Invalid waypoint file format: expected an array");
            }

            // Coerce inputs and add each waypoint using the same action the map uses.
            const importedWaypoints = parsed.map((wp: any) => ({
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
            }));
            dispatch(updateCurrentRouteWaypoints([]));
            dispatch(saveCurrentRouteToBackend());
            // Add each waypoint the same way WaypointCreationMap does so backend/save logic runs.
            for (const wp of importedWaypoints) {
                // keep id "-1" so reducer treats these as new entries when appropriate
                await dispatch(
                    addWaypointToCurrentRoute({
                        id: "-1",
                        latitude: wp.latitude,
                        longitude: wp.longitude,
                        name: wp.name,
                        altitude: wp.altitude,
                        command: wp.command,
                        param1: wp.param1,
                        param2: wp.param2,
                        param3: wp.param3,
                        param4: wp.param4,
                        remarks: wp.remarks,
                    }) as any,
                );
                // save after each add to match existing behavior that persists new map-created waypoints
                await dispatch(saveCurrentRouteToBackend() as any);
            }

            dispatch(openSnackbar({ message: "Waypoints imported", severity: "success" }));
        } catch (error) {
            const message = createErrorMessage(error);
            dispatch(openSnackbar({ message, severity: "error" }));
        } finally {
            // clear input so same file can be re-selected if needed
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    const rightButtons = (
        <Box
            sx={{
                display: "flex",
                p: 1,
                gap: 1,
            }}
        >
            <Button
                sx={{ fontSize: 16, fontWeight: "bold", px: 4 }}
                variant="outlined"
                onClick={() => dispatch(setMapViewOpen(!mapViewOpen))}
            >
                {mapViewOpen ? "List View" : "Map View"}
            </Button>
            <Button sx={{ fontSize: 16, fontWeight: "bold", px: 4 }} variant="outlined" onClick={handlePost}>
                Post Route to Drone
            </Button>
            <Button sx={{ fontSize: 16, fontWeight: "bold", px: 4 }} variant="outlined" onClick={handleExportWaypoints}>
                Export Waypoints
            </Button>
            <Button sx={{ fontSize: 16, fontWeight: "bold", px: 4 }} variant="outlined" onClick={handleImportClick}>
                Import Waypoints
            </Button>
        </Box>
    );

    return (
        <>
            <InfoCard title="Create Waypoints" rightNode={rightButtons}>
                <Grid
                    container
                    spacing={2}
                    sx={{
                        height: "100%",
                    }}
                >
                    <Grid item xs={12} md={6}>
                        {mapViewOpen ? (
                            <WaypointCreationMap
                                handleDelete={handleDeleteWaypoint}
                                handleEdit={handleEditWaypoint}
                                editState={editState}
                            />
                        ) : waypointQueue.length === 0 ? (
                            <Box
                                sx={{
                                    height: "100%",
                                    display: "flex",
                                    flexDirection: "column",
                                    justifyContent: "center",
                                }}
                            >
                                <Typography variant="h6" sx={{ textAlign: "center" }}>
                                    No waypoints queued
                                </Typography>
                            </Box>
                        ) : (
                            <Stack
                                spacing={2}
                                sx={{
                                    maxHeight: "73vh", // good enough of a value
                                    overflowY: "auto",
                                    p: 1,
                                }}
                            >
                                {waypointQueue.map((waypoint, index) => {
                                    return (
                                        <WaypointItem
                                            key={index}
                                            waypoint={waypoint}
                                            sx={{
                                                border: "4px solid",
                                                borderColor: index === editState.index ? "primary.main" : "transparent",
                                            }}
                                            handleDelete={() => handleDeleteWaypoint(index)}
                                            handleEdit={() => handleEditWaypoint(index)}
                                        />
                                    );
                                })}
                            </Stack>
                        )}
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Stack
                            sx={{
                                height: "100%",
                            }}
                            justifyContent={"space-between"}
                            spacing={2}
                        >
                            <WaypointForm editState={editState} clearEditState={clearEditState} />
                            <Box>
                                <Button color="error" variant="outlined" fullWidth onClick={() => setModalOpen(true)}>
                                    Delete ALL Queued Waypoints
                                </Button>
                            </Box>
                        </Stack>
                    </Grid>
                </Grid>
            </InfoCard>

            {/* Hidden file input for importing waypoints */}
            <input
                ref={fileInputRef}
                type="file"
                accept="application/json,.json"
                style={{ display: "none" }}
                onChange={handleImportFile}
            />

            <Modal open={modalOpen} onClose={() => setModalOpen(false)}>
                <Paper
                    elevation={2}
                    sx={{
                        position: "absolute",
                        top: "50%",
                        left: "50%",
                        transform: "translate(-50%, -50%)",
                        p: 4,
                    }}
                >
                    <Typography variant="body1" sx={{ mb: 2, textAlign: "center" }}>
                        Are you sure you want to delete all queued waypoints? <br />
                        This action cannot be undone.
                    </Typography>
                    <Button
                        fullWidth
                        variant="contained"
                        color="error"
                        onClick={() => {
                            dispatch(updateCurrentRouteWaypoints([]));
                            dispatch(saveCurrentRouteToBackend());
                            setModalOpen(false);
                        }}
                    >
                        Yes
                    </Button>
                </Paper>
            </Modal>
        </>
    );
}
