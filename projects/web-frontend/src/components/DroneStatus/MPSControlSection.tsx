import { Box, Button, Modal, Paper, TextField, Tooltip, Typography } from "@mui/material";
import InfoIcon from "@mui/icons-material/Info";
import { useState } from "react";
import { armDrone, prepareTakeoffDrone } from "../../api/endpoints.ts";

export default function MPSControlSection() {
    const [clientSideState, setClientSideState] = useState({
        armed: false,
        takeoffAltitude: 0,
    });
    const [modalState, setModalState] = useState(false);

    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 2,
            }}
        >
            <Box>
                {clientSideState.armed ? (
                    <Button
                        fullWidth
                        variant="outlined"
                        color="success"
                        onClick={() => {
                            armDrone(false).then((response) => {
                                if (response.status === 200) {
                                    setClientSideState((prevState) => ({
                                        ...prevState,
                                        armed: false,
                                    }));
                                }
                            });
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
                            setModalState(true);
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
                        setClientSideState((prevState) => ({
                            ...prevState,
                            takeoffAltitude: parseFloat(e.target.value),
                        }));
                    }}
                    value={clientSideState.takeoffAltitude === 0 ? "" : clientSideState.takeoffAltitude}
                />
                <Button
                    variant="contained"
                    color="error"
                    onClick={() => {
                        prepareTakeoffDrone(clientSideState.takeoffAltitude).then((response) => {
                            if (response.status === 200) {
                                console.log("Drone prepared for takeoff", response);
                                return;
                            }
                            console.error("Failed to prepare drone for takeoff", response);
                        });
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
            <Modal open={modalState} onClose={() => setModalState(false)}>
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
                            setModalState(false);
                            armDrone(true).then((response) => {
                                if (response.status === 200) {
                                    console.log("Drone armed successfully", response);
                                    setClientSideState((prevState) => ({
                                        ...prevState,
                                        armed: true,
                                    }));
                                } else {
                                    console.error("Failed to arm drone", response);
                                }
                            });
                        }}
                    >
                        Yes
                    </Button>
                </Paper>
            </Modal>
        </Box>
    );
}
