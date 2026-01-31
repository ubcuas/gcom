import { Box, Modal, Paper, Table, TableBody, TableCell, TableContainer, TableRow, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useAppSelector } from "../../store/store";
import { selectAircraftStatus } from "../../store/slices/dataSlice";
import { getDroneParameter, getCurrentMissionRaw } from "../../api/endpoints";

type DebugPanelProps = {
    open: boolean;
    onClose: () => void;
};

type DroneParam = {
    param: string;
    value: string;
};

const DRONE_PARAM_NAMES = ["RTL_ALT", "WPNAV_SPEED", "LAND_SPEED", "RTL_LOIT_TIME", "BATT_LOW_VOLT"];

const getFlightModeColor = (mode: string) => {
    switch (mode) {
        case "AUTO":
            return "success.main";
        case "GUIDED":
            return "info.main";
        case "RTL":
            return "warning.main";
        case "STABILIZE":
            return "secondary.main";
        default:
            return "grey.500";
    }
};

const getArmedColor = (armed: boolean) => {
    return armed ? "error.main" : "success.main";
};

export default function DebugPanel({ open, onClose }: DebugPanelProps) {
    const aircraftStatus = useAppSelector(selectAircraftStatus);

    const [waypointQueue, setWaypointQueue] = useState<object[] | string>("loading...");

    const [droneParams, setDroneParams] = useState<DroneParam[]>(
        DRONE_PARAM_NAMES.map((name) => ({ param: name, value: "loading..." })),
    );

    const flightMode = aircraftStatus.flightmode || "UNKNOWN";

    useEffect(() => {
        if (open) {
            getCurrentMissionRaw()
                .then((result) => setWaypointQueue(result))
                .catch((e) => {
                    console.error("Error fetching GCOM", e);
                    setWaypointQueue("error");
                });

            DRONE_PARAM_NAMES.forEach(async (paramName) => {
                try {
                    const result = await getDroneParameter(paramName);
                    setDroneParams((prev) =>
                        prev.map((p) => (p.param === paramName ? { ...p, value: result.param_value.toString() } : p)),
                    );
                } catch (error) {
                    console.log("Error fetching drone parameter", paramName, error);
                    setDroneParams((prev) => prev.map((p) => (p.param === paramName ? { ...p, value: "error" } : p)));
                }
            });
        }
    }, [open]);

    return (
        <Modal open={open} onClose={onClose}>
            <Paper
                elevation={2}
                sx={{
                    position: "absolute",
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%, -50%)",
                    width: "90%",
                    maxWidth: "600px",
                    overflow: "auto",
                    p: 3,
                }}
            >
                <Typography variant="h6" sx={{ mb: 3 }}>
                    Debug Panel
                </Typography>

                <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
                    <Box
                        sx={{
                            flex: 1,
                            border: 2,
                            borderColor: getFlightModeColor(flightMode),
                            borderRadius: 1,
                            p: 2,
                            textAlign: "center",
                        }}
                    >
                        <Typography variant="caption" color="text.secondary">
                            Flight Mode
                        </Typography>
                        <Typography
                            variant="h6"
                            sx={{
                                color: getFlightModeColor(flightMode),
                                fontWeight: "bold",
                            }}
                        >
                            {flightMode}
                        </Typography>
                    </Box>

                    <Box
                        sx={{
                            flex: 1,
                            border: 2,
                            borderColor: getArmedColor(aircraftStatus.armed),
                            borderRadius: 1,
                            p: 2,
                            textAlign: "center",
                        }}
                    >
                        <Typography variant="caption" color="text.secondary">
                            Armed Status
                        </Typography>
                        <Typography
                            variant="h6"
                            sx={{
                                color: getArmedColor(aircraftStatus.armed),
                                fontWeight: "bold",
                            }}
                        >
                            {aircraftStatus.armed ? "ARMED" : "DISARMED"}
                        </Typography>
                    </Box>
                </Box>

                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: "bold" }}>
                    Drone Parameters
                </Typography>
                <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
                    <Table size="small">
                        <TableBody>
                            {droneParams.map((param) => (
                                <TableRow key={param.param}>
                                    <TableCell sx={{ fontWeight: "medium" }}>{param.param}</TableCell>
                                    <TableCell align="right">{param.value}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>

                <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: "bold" }}>
                    Waypoint Queue
                </Typography>
                <Box
                    component="pre"
                    sx={{
                        backgroundColor: "grey.900",
                        color: "grey.100",
                        p: 2,
                        borderRadius: 1,
                        overflow: "auto",
                        fontSize: "0.7rem",
                        fontFamily: "monospace",
                        maxHeight: "300px",
                    }}
                >
                    {JSON.stringify(waypointQueue, null, 2)}
                </Box>
            </Paper>
        </Modal>
    );
}
