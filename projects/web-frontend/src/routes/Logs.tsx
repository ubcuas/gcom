import { Box, FormControl, InputLabel, MenuItem, Paper, Select, Stack, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { useAppSelector } from "../store/store";
import { selectNodeLogs } from "../store/slices/dataSlice";

const LEVEL_COLORS: Record<string, string> = {
    DEBUG: "#888888",
    INFO: "#4fc3f7",
    WARN: "#ffb74d",
    ERROR: "#ef5350",
    FATAL: "#b71c1c",
};

function levelColor(level: string): string {
    return LEVEL_COLORS[level] ?? "#ffffff";
}

function formatTimestamp(ms: number): string {
    return new Date(ms).toISOString().replace("T", " ").slice(0, 23);
}

export default function Logs() {
    const nodeLogs = useAppSelector(selectNodeLogs);
    const [selectedNode, setSelectedNode] = useState<string>("all");

    const nodes = useMemo(() => {
        const set = new Set(nodeLogs.map((l) => l.node));
        return Array.from(set).sort();
    }, [nodeLogs]);

    const filteredLogs = useMemo(() => {
        if (selectedNode === "all") return nodeLogs;
        return nodeLogs.filter((l) => l.node === selectedNode);
    }, [nodeLogs, selectedNode]);

    return (
        <Box sx={{ p: 4, width: "100%", display: "flex", flexDirection: "column", height: "100vh" }}>
            <Stack spacing={2} sx={{ height: "100%" }}>
                <Typography variant="h5" fontWeight="bold">
                    Node Logs
                </Typography>

                <FormControl size="small" sx={{ width: 240 }}>
                    <InputLabel>Node</InputLabel>
                    <Select value={selectedNode} label="Node" onChange={(e) => setSelectedNode(e.target.value)}>
                        <MenuItem value="all">All nodes</MenuItem>
                        {nodes.map((node) => (
                            <MenuItem key={node} value={node}>
                                {node}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <Paper
                    sx={{
                        flex: 1,
                        overflow: "auto",
                        p: 2,
                        backgroundColor: "#0d0d0d",
                        fontFamily: "monospace",
                        fontSize: "0.8rem",
                    }}
                >
                    {filteredLogs.length === 0 ? (
                        <Typography sx={{ color: "#555", fontFamily: "monospace" }}>No logs received.</Typography>
                    ) : (
                        filteredLogs.map((log, i) => (
                            <Box key={i} sx={{ display: "flex", gap: 1, lineHeight: 1.6 }}>
                                <Box component="span" sx={{ color: "#555", minWidth: 160, flexShrink: 0 }}>
                                    {formatTimestamp(log.timestamp)}
                                </Box>
                                <Box
                                    component="span"
                                    sx={{ color: levelColor(log.level), minWidth: 48, flexShrink: 0 }}
                                >
                                    {log.level}
                                </Box>
                                {selectedNode === "all" && (
                                    <Box component="span" sx={{ color: "#888", minWidth: 100, flexShrink: 0 }}>
                                        [{log.node}]
                                    </Box>
                                )}
                                <Box component="span" sx={{ color: "#e0e0e0", wordBreak: "break-word" }}>
                                    {log.message}
                                </Box>
                            </Box>
                        ))
                    )}
                </Paper>
            </Stack>
        </Box>
    );
}
