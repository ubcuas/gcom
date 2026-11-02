import { Box, Button, Divider, MenuItem, Paper, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import {
    RosbridgeResult,
    rosbridgeArm,
    rosbridgePrepareTakeoff,
    rosbridgeRtl,
    rosbridgeSetMode,
    rosbridgeStartMission,
} from "../api/endpoints";
import { openSnackbar } from "../store/slices/appSlice";
import { useAppDispatch } from "../store/store";
import { extractAxiosError } from "../utils/errorHandling";

// ArduCopter mode names accepted by /flight_commander/set_mode
const FLIGHT_MODES = ["GUIDED", "AUTO", "LOITER", "STABILIZE", "ALT_HOLD", "RTL", "LAND"];

type LogEntry = { time: string; command: string; success: boolean; message: string };

/**
 * Prototype page: each button calls a flight_commander ROS service on the aircraft (ACMS)
 * through the backend's rosbridge client. Typical sequence:
 * Prepare takeoff -> GUIDED -> Arm -> AUTO -> Start mission -> (later) RTL
 */
export default function FlightCommands() {
    const dispatch = useAppDispatch();
    const [altitude, setAltitude] = useState("10");
    const [mode, setMode] = useState("GUIDED");
    const [busy, setBusy] = useState<string | null>(null);
    const [log, setLog] = useState<LogEntry[]>([]);

    const run = async (command: string, call: () => Promise<RosbridgeResult>) => {
        setBusy(command);
        let entry: LogEntry;
        try {
            const result = await call();
            entry = { time: new Date().toLocaleTimeString(), command, ...result };
        } catch (error) {
            entry = {
                time: new Date().toLocaleTimeString(),
                command,
                success: false,
                message: extractAxiosError(error).message,
            };
        } finally {
            setBusy(null);
        }
        setLog((prev) => [entry, ...prev].slice(0, 50));
        dispatch(
            openSnackbar({
                message: `${command}: ${entry.message || (entry.success ? "ok" : "failed")}`,
                severity: entry.success ? "success" : "error",
            }),
        );
    };

    const altitudeValue = parseFloat(altitude);
    const disabled = busy !== null;

    return (
        <Box sx={{ p: 8, width: "100%" }}>
            <Stack spacing={3} sx={{ maxWidth: 720 }}>
                <Box>
                    <Typography variant="h5">Flight Commands (rosbridge)</Typography>
                    <Typography variant="body2" color="text.secondary">
                        Sequence: Prepare takeoff → GUIDED → Arm → AUTO → Start mission → (later) RTL
                    </Typography>
                </Box>

                <Paper sx={{ p: 3 }} variant="outlined">
                    <Stack spacing={2}>
                        <Stack direction="row" spacing={2} alignItems="center">
                            <TextField
                                size="small"
                                type="number"
                                label="Takeoff altitude (m above home)"
                                value={altitude}
                                onChange={(e) => setAltitude(e.target.value)}
                                sx={{ width: 240 }}
                            />
                            <Button
                                variant="contained"
                                disabled={disabled || !(altitudeValue > 0)}
                                onClick={() => run("Prepare takeoff", () => rosbridgePrepareTakeoff(altitudeValue))}
                            >
                                Prepare takeoff
                            </Button>
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                            Replaces the mission with a straight climb from home. Does not arm or fly.
                        </Typography>

                        <Divider />

                        <Stack direction="row" spacing={2} alignItems="center">
                            <TextField
                                select
                                size="small"
                                label="Flight mode"
                                value={mode}
                                onChange={(e) => setMode(e.target.value)}
                                sx={{ width: 240 }}
                            >
                                {FLIGHT_MODES.map((m) => (
                                    <MenuItem key={m} value={m}>
                                        {m}
                                    </MenuItem>
                                ))}
                            </TextField>
                            <Button
                                variant="contained"
                                disabled={disabled}
                                onClick={() => run(`Set mode ${mode}`, () => rosbridgeSetMode(mode))}
                            >
                                Set mode
                            </Button>
                        </Stack>

                        <Divider />

                        <Stack direction="row" spacing={2}>
                            <Button
                                variant="contained"
                                color="error"
                                disabled={disabled}
                                onClick={() => run("Arm", () => rosbridgeArm(true))}
                            >
                                Arm
                            </Button>
                            <Button
                                variant="outlined"
                                disabled={disabled}
                                onClick={() => run("Disarm", () => rosbridgeArm(false))}
                            >
                                Disarm
                            </Button>
                            <Button
                                variant="contained"
                                color="success"
                                disabled={disabled}
                                onClick={() => run("Start mission", rosbridgeStartMission)}
                            >
                                Start mission
                            </Button>
                            <Button
                                variant="contained"
                                color="warning"
                                disabled={disabled}
                                onClick={() => run("RTL", rosbridgeRtl)}
                            >
                                Return to launch
                            </Button>
                        </Stack>
                    </Stack>
                </Paper>

                <Paper sx={{ p: 3 }} variant="outlined">
                    <Typography variant="subtitle1" gutterBottom>
                        Responses {busy && `(waiting on ${busy}…)`}
                    </Typography>
                    {log.length === 0 ? (
                        <Typography variant="body2" color="text.secondary">
                            No commands sent yet.
                        </Typography>
                    ) : (
                        <Stack spacing={0.5}>
                            {log.map((entry, i) => (
                                <Typography
                                    key={i}
                                    variant="body2"
                                    sx={{ fontFamily: "monospace" }}
                                    color={entry.success ? "success.main" : "error.main"}
                                >
                                    [{entry.time}] {entry.command}: {entry.message || (entry.success ? "ok" : "failed")}
                                </Typography>
                            ))}
                        </Stack>
                    )}
                </Paper>
            </Stack>
        </Box>
    );
}
