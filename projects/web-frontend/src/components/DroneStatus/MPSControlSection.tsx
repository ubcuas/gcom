import { Box, Button, Modal, Paper, TextField, Tooltip, Typography } from "@mui/material";
import InfoIcon from "@mui/icons-material/Info";
import { useState } from "react";
import { armDrone, prepareTakeoffDrone, returnToLaunch } from "../../api/endpoints.ts";
import { openSnackbar } from "../../store/slices/appSlice";
import { selectAircraftStatus } from "../../store/slices/dataSlice";
import { useAppDispatch, useAppSelector } from "../../store/store";
import DebugPanel from "./DebugPanel";

export default function MPSControlSection() {
    const dispatch = useAppDispatch();
    const aircraftStatus = useAppSelector(selectAircraftStatus);
    const [takeoffAltitude, setTakeoffAltitude] = useState(0);
    const [armModalState, setArmModalState] = useState(false);
    const [rtlModalState, setRtlModalState] = useState(false);
    const [debugPanelOpen, setDebugPanelOpen] = useState(false);
    const [preparingTakeoff, setPreparingTakeoff] = useState(false);
    const [preparingRtl, setPreparingRtl] = useState(false);
    const [armingInProgress, setArmingInProgress] = useState(false);

    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 2,
            }}
        >
            <Box>
                {aircraftStatus.armed ? (
                    <Button
                        fullWidth
                        variant="outlined"
                        color={armingInProgress ? "inherit" : "success"}
                        disabled={armingInProgress}
                        onClick={() => {
                            setArmingInProgress(true);
                            armDrone(false)
                                .then((response) => {
                                    if (response.status === 200) {
                                        dispatch(
                                            openSnackbar({
                                                message: "Drone disarmed successfully",
                                                severity: "success",
                                            }),
                                        );
                                    } else {
                                        dispatch(
                                            openSnackbar({
                                                message: "Failed to disarm drone",
                                            }),
                                        );
                                    }
                                })
                                .finally(() => setArmingInProgress(false));
                        }}
                    >
                        Disarm Drone
                    </Button>
                ) : (
                    <Button
                        fullWidth
                        variant="outlined"
                        color="error"
                        onClick={() => {
                            setArmModalState(true);
                        }}
                    >
                        Arm Drone
                    </Button>
                )}
            </Box>
            <Box
                sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "stretch",
                    gap: 2,
                }}
            >
                <TextField
                    size="small"
                    required
                    id="takeoffAltitude"
                    type="number"
                    label="Take Off Altitude (ft)"
                    onChange={(e) => {
                        setTakeoffAltitude(parseFloat(e.target.value));
                    }}
                    value={takeoffAltitude === 0 ? "" : takeoffAltitude}
                />
                <Button
                    variant="contained"
                    color={preparingTakeoff ? "inherit" : "error"}
                    disabled={preparingTakeoff || takeoffAltitude <= 0}
                    onClick={() => {
                        setPreparingTakeoff(true);
                        prepareTakeoffDrone(takeoffAltitude)
                            .then((response) => {
                                if (response.status === 200) {
                                    dispatch(
                                        openSnackbar({
                                            message: "Drone prepared for takeoff. Switch to AUTO mode to begin.",
                                            severity: "success",
                                        }),
                                    );
                                } else {
                                    dispatch(
                                        openSnackbar({
                                            message: "Failed to prepare drone for takeoff",
                                        }),
                                    );
                                }
                            })
                            .finally(() => setPreparingTakeoff(false));
                    }}
                    endIcon={
                        <Tooltip title="Clears mission queue and loads a takeoff waypoint. Switch drone to AUTO mode to takeoff">
                            <InfoIcon fontSize="small" />
                        </Tooltip>
                    }
                >
                    Prepare for Takeoff
                </Button>
            </Box>
            <Box>
                <Button
                    fullWidth
                    variant="contained"
                    color={preparingRtl ? "inherit" : "warning"}
                    disabled={preparingRtl}
                    onClick={() => {
                        setRtlModalState(true);
                    }}
                    endIcon={
                        <Tooltip title="Switches the drone to RTL mode using the current RTL_ALT parameter">
                            <InfoIcon fontSize="small" />
                        </Tooltip>
                    }
                >
                    Return to Launch
                </Button>
            </Box>
            <Box>
                <Button
                    fullWidth
                    variant="outlined"
                    color="warning"
                    onClick={() => {
                        setDebugPanelOpen(true);
                    }}
                >
                    Open Debug Panel
                </Button>
            </Box>
            <Box
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 1,
                }}
            >
                <Button variant="outlined" onClick={() => {}}>
                    Show All Waypoints
                </Button>
                <Button variant="outlined" onClick={() => {}}>
                    Hide All Waypoints
                </Button>
                <Box
                    sx={{
                        display: "flex",
                        gap: 2,
                        alignItems: "center",
                    }}
                >
                    {/* Routes already get fetched on load, we don't have a situation where we need to refetch */}
                    {/* <Button
                        sx={{
                            flexGrow: 1,
                        }}
                        variant="outlined"
                        color="success"
                        onClick={() => {
                            console.log("Fetch MPS Data - needs route integration");
                        }}
                    >
                        Fetch MPS Data
                    </Button> */}
                    {/* <Box
                        sx={{
                            display: "flex",
                            alignItems: "center",
                        }}
                    >
                        Auto Fetch
                        <Switch
                            onClick={() => {
                                // Functionality to auto fetch the mps queue on an interval, not sure if needed so commented out for now.
                            }}
                        />
                    </Box> */}
                </Box>
            </Box>
            <Modal open={armModalState} onClose={() => setArmModalState(false)}>
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
                        Are you sure you are ready to arm?
                    </Typography>
                    <Button
                        fullWidth
                        variant="contained"
                        color="error"
                        onClick={() => {
                            setArmModalState(false);
                            setArmingInProgress(true);
                            armDrone(true)
                                .then((response) => {
                                    if (response.status === 200) {
                                        dispatch(
                                            openSnackbar({
                                                message: "Drone armed successfully",
                                                severity: "success",
                                            }),
                                        );
                                    } else {
                                        dispatch(
                                            openSnackbar({
                                                message: "Failed to arm drone",
                                            }),
                                        );
                                    }
                                })
                                .finally(() => setArmingInProgress(false));
                        }}
                    >
                        Yes
                    </Button>
                </Paper>
            </Modal>
            <Modal open={rtlModalState} onClose={() => setRtlModalState(false)}>
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
                        Are you sure you want to return to launch?
                    </Typography>
                    <Button
                        fullWidth
                        variant="contained"
                        color="warning"
                        onClick={() => {
                            setRtlModalState(false);
                            setPreparingRtl(true);
                            returnToLaunch()
                                .then((response) => {
                                    if (response.status === 200) {
                                        dispatch(
                                            openSnackbar({
                                                message: "Return to launch initiated successfully",
                                                severity: "success",
                                            }),
                                        );
                                    } else {
                                        dispatch(
                                            openSnackbar({
                                                message: "Failed to initiate return to launch",
                                            }),
                                        );
                                    }
                                })
                                .finally(() => setPreparingRtl(false));
                        }}
                    >
                        Yes
                    </Button>
                </Paper>
            </Modal>
            <DebugPanel open={debugPanelOpen} onClose={() => setDebugPanelOpen(false)} />
        </Box>
    );
}
