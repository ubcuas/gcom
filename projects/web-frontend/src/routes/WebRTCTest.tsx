import { Box, Button, Paper, Stack, Typography, Chip } from "@mui/material";
import { useState, useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";

type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

export default function WebRTCTest() {
    const [status, setStatus] = useState<ConnectionStatus>("disconnected");
    const [error, setError] = useState<string>("");
    const socketRef = useRef<Socket | null>(null);

    const signalingServerUrl = import.meta.env.VITE_SIGNALING_SERVER_URL;

    useEffect(() => {
        return () => {
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
        };
    }, []);

    const handleConnect = () => {
        if (!signalingServerUrl) {
            setError("VITE_SIGNALING_SERVER_URL not configured");
            setStatus("error");
            return;
        }

        if (socketRef.current && socketRef.current.connected) {
            return;
        }

        setStatus("connecting");
        setError("");

        const socket = io(signalingServerUrl, {
            autoConnect: false,
        });
        socketRef.current = socket;

        socket.on("connect", () => {
            setStatus("connected");
            setError("");
        });

        socket.on("disconnect", () => {
            setStatus("disconnected");
        });

        socket.on("connect_error", (err) => {
            setError(`Failed to connect: ${err.message}`);
            setStatus("error");
        });

        socket.connect();
    };

    const handleDisconnect = () => {
        if (socketRef.current) {
            socketRef.current.disconnect();
            socketRef.current = null;
            setStatus("disconnected");
            setError("");
        }
    };

    const getStatusColor = (): "default" | "success" | "warning" | "error" => {
        switch (status) {
            case "connected":
                return "success";
            case "connecting":
                return "warning";
            case "error":
                return "error";
            default:
                return "default";
        }
    };

    const getStatusLabel = (): string => {
        switch (status) {
            case "connected":
                return "Connected";
            case "connecting":
                return "Connecting...";
            case "error":
                return "Error";
            default:
                return "Disconnected";
        }
    };

    return (
        <Box
            sx={{
                p: 8,
                m: "auto",
                width: "100%",
                maxWidth: 600,
            }}
        >
            <Paper
                sx={{
                    p: 3,
                }}
            >
                <Typography
                    variant="h4"
                    sx={{
                        fontWeight: "bold",
                        mb: 3,
                    }}
                >
                    WebRTC Test
                </Typography>

                <Stack spacing={3}>
                    <Box>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                            Signaling Server Status:
                        </Typography>
                        <Chip label={getStatusLabel()} color={getStatusColor()} sx={{ fontWeight: "bold" }} />
                    </Box>

                    {error && (
                        <Typography variant="body2" color="error">
                            {error}
                        </Typography>
                    )}

                    {signalingServerUrl && (
                        <Typography variant="body2" color="text.secondary">
                            Server URL: {signalingServerUrl}
                        </Typography>
                    )}

                    <Stack direction="row" spacing={2}>
                        <Button
                            variant="contained"
                            onClick={handleConnect}
                            disabled={status === "connected" || status === "connecting"}
                        >
                            Connect
                        </Button>
                        <Button variant="outlined" onClick={handleDisconnect} disabled={status === "disconnected"}>
                            Disconnect
                        </Button>
                    </Stack>
                </Stack>
            </Paper>
        </Box>
    );
}
