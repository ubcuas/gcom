import { Box, Modal, Paper, Table, TableBody, TableCell, TableContainer, TableRow, Typography } from "@mui/material";
import { useAppSelector } from "../../store/store";
import { selectAircraftStatus, selectCurrentRouteWaypoints } from "../../store/slices/dataSlice";

type DebugPanelProps = {
    open: boolean;
    onClose: () => void;
};

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
    const waypoints = useAppSelector(selectCurrentRouteWaypoints);

    const flightMode = "GUIDED";

    const droneParams = [
        { param: "RTL_ALT", value: "100" },
        { param: "WP_RADIUS", value: "15" },
        { param: "WPNAV_SPEED", value: "500" },
        { param: "LAND_SPEED", value: "50" },
        { param: "RTL_LOIT_TIME", value: "5000" },
        { param: "BATT_LOW_VOLT", value: "10.5" },
    ];

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
                    maxHeight: "80vh",
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
                        fontSize: "0.875rem",
                        fontFamily: "monospace",
                        maxHeight: "300px",
                    }}
                >
                    {JSON.stringify(waypoints, null, 2)}
                </Box>
            </Paper>
        </Modal>
    );
}
