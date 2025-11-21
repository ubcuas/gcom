import { Box, Button, Grid, Modal, Paper, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { postWaypointsToDrone } from "../api/endpoints";
import { openSnackbar, selectMapViewOpen, setMapViewOpen } from "../store/slices/appSlice";
import {
    deleteWaypointFromCurrentRoute,
    selectCurrentRouteWaypoints,
    updateCurrentRouteWaypoints,
    selectCurrentRoute,
} from "../store/slices/dataSlice";
import { saveCurrentRouteToBackend } from "../store/thunks/dataThunks";
import { useAppDispatch, useAppSelector } from "../store/store";
import { WaypointEditState } from "../types/Waypoint";
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

    const handlePost = async () => {
        if (waypointQueue.length === 0) {
            return;
        }
        try {
            await postWaypointsToDrone(waypointQueue);
        } catch (error) {
            const message = (error as Error).message;
            dispatch(openSnackbar(message));
        }
    };

    const handleSaveToBackend = async () => {
        try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            await (dispatch as any)(saveCurrentRouteToBackend()).unwrap();
            dispatch(openSnackbar("Route saved successfully"));
        } catch (error: unknown) {
            const message = (error as Error).message;
            dispatch(openSnackbar(message));
        }
    };

    const handleDeleteWaypoint = (index: number) => {
        dispatch(deleteWaypointFromCurrentRoute(index));
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
                                <Button
                                    color="primary"
                                    variant="contained"
                                    fullWidth
                                    onClick={handleSaveToBackend}
                                    disabled={!currentRoute}
                                    sx={{ mb: 1 }}
                                >
                                    Save to Backend
                                </Button>
                                <Button color="error" variant="outlined" fullWidth onClick={() => setModalOpen(true)}>
                                    Delete ALL Queued Waypoints
                                </Button>
                            </Box>
                        </Stack>
                    </Grid>
                </Grid>
            </InfoCard>
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
