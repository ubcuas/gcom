import { Box, Button, Paper, Stack, Typography, Chip, Grid } from "@mui/material";
import { useRef, useEffect } from "react";
import { useWebRTCConnection } from "../hooks/useWebRTCConnection";
import VideocamIcon from "@mui/icons-material/Videocam";

export default function WebRTCTest() {
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
                    <Typography
                        variant="h4"
                        sx={{
                            fontWeight: "bold",
                            mb: 3,
                        }}
                    >
                        WebRTC Video Stream
                    </Typography>

                    <Grid container spacing={3}>
                        <Grid item xs={12} md={8}>
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
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: "center" }}>
                                {remoteStream ? "Streaming video" : "Ready for video stream"}
                            </Typography>
                        </Grid>

                        <Grid item xs={12} md={4}>
                            <Stack spacing={3}>
                                <Box>
                                    <Typography
                                        variant="h6"
                                        sx={{
                                            fontWeight: "bold",
                                            mb: 2,
                                        }}
                                    >
                                        Connection Status
                                    </Typography>
                                    <Stack spacing={2}>
                                        <Box>
                                            <Typography variant="body2" sx={{ mb: 1 }}>
                                                Signaling Server:
                                            </Typography>
                                            <Chip
                                                label={getStatusLabel(signalingStatus)}
                                                color={getStatusColor(signalingStatus)}
                                                sx={{ fontWeight: "bold" }}
                                            />
                                        </Box>
                                        <Box>
                                            <Typography variant="body2" sx={{ mb: 1 }}>
                                                WebRTC Peer:
                                            </Typography>
                                            <Chip
                                                label={getStatusLabel(peerStatus)}
                                                color={getStatusColor(peerStatus)}
                                                sx={{ fontWeight: "bold" }}
                                            />
                                        </Box>
                                    </Stack>
                                </Box>

                                <Box>
                                    <Typography
                                        variant="h6"
                                        sx={{
                                            fontWeight: "bold",
                                            mb: 2,
                                        }}
                                    >
                                        Connection
                                    </Typography>
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
                                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                                        {isConnecting
                                            ? "Establishing connection to signaling server..."
                                            : signalingStatus === "connected"
                                              ? "Connected to signaling server"
                                              : "Click connect to start"}
                                    </Typography>
                                </Box>
                            </Stack>
                        </Grid>
                    </Grid>
                </Paper>
            </Stack>
        </Box>
    );
}
