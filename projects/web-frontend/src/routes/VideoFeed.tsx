import { Box, Button, Paper, Stack, Typography, Chip, Grid } from "@mui/material";
import { useRef, useEffect } from "react";
import { useWebRTCConnection } from "../hooks/useWebRTCConnection";
import VideocamIcon from "@mui/icons-material/Videocam";
import DroneStatusCard from "../components/DroneStatusCard";

export default function VideoFeed() {
    const { signalingStatus, peerStatus, remoteStream, connect, disconnect, isConnecting } = useWebRTCConnection();

    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        if (videoRef.current && remoteStream) {
            console.log("Setting stream to video element");
            console.log("Stream active:", remoteStream.active);
            console.log(
                "Stream tracks:",
                remoteStream.getTracks().map((t) => ({
                    kind: t.kind,
                    enabled: t.enabled,
                    muted: t.muted,
                    readyState: t.readyState,
                })),
            );

            videoRef.current.srcObject = remoteStream;
        }
    }, [remoteStream]);

    const getStatusColor = (
        status: typeof signalingStatus | typeof peerStatus,
    ): "default" | "success" | "warning" | "error" => {
        switch (status) {
            case "connected":
                return "success";
            case "connecting":
                return "warning";
            case "failed":
                return "error";
            default:
                return "default";
        }
    };

    const getStatusLabel = (status: typeof signalingStatus | typeof peerStatus): string => {
        return status.charAt(0).toUpperCase() + status.slice(1);
    };

    return (
        <Box
            sx={{
                p: 8,
                width: "100%",
            }}
        >
            <Stack spacing={3}>
                <Paper
                    sx={{
                        p: 3,
                    }}
                >
                    <Grid container spacing={3}>
                        <Grid item xs={12} lg={8}>
                            <Typography
                                variant="h4"
                                sx={{
                                    fontWeight: "bold",
                                    mb: 3,
                                }}
                            >
                                WebRTC Video Stream
                            </Typography>
                            <Stack spacing={2}>
                                <Box
                                    sx={{
                                        position: "relative",
                                        width: "100%",
                                        paddingBottom: "56.25%",
                                        backgroundColor: "background.default",
                                        borderRadius: 1,
                                        overflow: "hidden",
                                    }}
                                >
                                    <video
                                        ref={videoRef}
                                        autoPlay
                                        playsInline
                                        muted
                                        style={{
                                            position: "absolute",
                                            top: 0,
                                            left: 0,
                                            width: "100%",
                                            height: "100%",
                                            objectFit: "contain",
                                        }}
                                    />
                                    {!remoteStream && (
                                        <Box
                                            sx={{
                                                position: "absolute",
                                                top: 0,
                                                left: 0,
                                                width: "100%",
                                                height: "100%",
                                                display: "flex",
                                                flexDirection: "column",
                                                alignItems: "center",
                                                justifyContent: "center",
                                                gap: 2,
                                                color: "text.secondary",
                                            }}
                                        >
                                            <VideocamIcon sx={{ fontSize: 64, opacity: 0.3 }} />
                                            <Typography variant="body1">
                                                {signalingStatus === "connected"
                                                    ? "Waiting for video stream..."
                                                    : "Connect to start streaming"}
                                            </Typography>
                                        </Box>
                                    )}
                                </Box>

                                <Paper sx={{ p: 2 }}>
                                    <Stack spacing={2}>
                                        <Box>
                                            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: "bold" }}>
                                                Connection Status
                                            </Typography>
                                            <Stack direction="row" spacing={2}>
                                                <Box sx={{ flex: 1 }}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        Signaling Server
                                                    </Typography>
                                                    <Box sx={{ mt: 0.5 }}>
                                                        <Chip
                                                            label={getStatusLabel(signalingStatus)}
                                                            color={getStatusColor(signalingStatus)}
                                                            size="small"
                                                        />
                                                    </Box>
                                                </Box>
                                                <Box sx={{ flex: 1 }}>
                                                    <Typography variant="caption" color="text.secondary">
                                                        WebRTC Peer
                                                    </Typography>
                                                    <Box sx={{ mt: 0.5 }}>
                                                        <Chip
                                                            label={getStatusLabel(peerStatus)}
                                                            color={getStatusColor(peerStatus)}
                                                            size="small"
                                                        />
                                                    </Box>
                                                </Box>
                                            </Stack>
                                        </Box>

                                        <Stack direction="row" spacing={2}>
                                            <Button
                                                variant="contained"
                                                onClick={connect}
                                                disabled={
                                                    signalingStatus === "connected" || signalingStatus === "connecting"
                                                }
                                                fullWidth
                                            >
                                                {isConnecting ? "Connecting..." : "Connect"}
                                            </Button>
                                            <Button
                                                variant="outlined"
                                                onClick={disconnect}
                                                disabled={signalingStatus === "disconnected"}
                                                fullWidth
                                            >
                                                Disconnect
                                            </Button>
                                        </Stack>
                                    </Stack>
                                </Paper>
                            </Stack>
                        </Grid>

                        <Grid item xs={12} lg={4}>
                            <DroneStatusCard />
                        </Grid>
                    </Grid>
                </Paper>
            </Stack>
        </Box>
    );
}
