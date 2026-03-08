import {
    Box,
    Button,
    Collapse,
    FormControlLabel,
    IconButton,
    Paper,
    Stack,
    Switch,
    TextField,
    ToggleButton,
    ToggleButtonGroup,
    Typography,
} from "@mui/material";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import Flag from "@mui/icons-material/Flag";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAppDispatch, useAppSelector } from "../store/store";
import {
    selectOdlcImageRecords,
    selectSelectedOdlcImageId,
    selectSelectedOdlcImageRecord,
    setSelectedOdlcImage,
    updateOdlcImageFlag,
    updateOdlcImageTextInput,
    addOdlcImageAnnotation,
    undoLastOdlcImageAnnotation,
    deleteOdlcImageAnnotation,
    setOdlcImageAnnotationDistance,
    appendOdlcImage,
} from "../store/slices/dataSlice";
import ImageAnnotationOverlay from "../components/ImageAnnotationOverlay";
import { deprojectPixel } from "../api/endpoints";
import type { OdlcImageRecord } from "../store/slices/dataSlice";
import { getColorGroupKey, getColorGroupLabel } from "../utils/odlcColorGroup";
import type { RGB } from "../utils/odlcColorGroup";
import type { OdlcImage } from "../schemas/odlc";
import { calculateAnnotationDistance } from "../utils/odlcImageAnnotationUtils";

type SortBy = "time" | "confidence";

/** Build a colored square image as base64 JPEG for testing without a stream. */
function createDummyImageBase64(width: number, height: number, r: number, g: number, b: number): string {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return "";
    ctx.fillStyle = `rgb(${r},${g},${b})`;
    ctx.fillRect(0, 0, width, height);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
    return dataUrl.split(",")[1] ?? "";
}

/** Random int in [min, max] inclusive. */
function randomInt(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/** Random float in [min, max). */
function randomIn(min: number, max: number): number {
    return Math.random() * (max - min) + min;
}

function createDummyOdlcImage(color: [number, number, number], confidenceLevel: number): OdlcImage {
    const width = randomInt(40, 120);
    const height = randomInt(40, 120);
    const x1 = randomIn(0.05, 0.85);
    const y1 = randomIn(0.05, 0.85);
    const x2 = randomIn(0.15, 0.95);
    const y2 = randomIn(0.15, 0.95);
    return {
        image_data: createDummyImageBase64(width, height, ...color),
        color_detection: color,
        bounding_box: [
            [x1, y1],
            [x2, y2],
        ],
        confidence_level: confidenceLevel,
    };
}

function filterAndSortRecords(records: OdlcImageRecord[], flaggedOnly: boolean, sortBy: SortBy): OdlcImageRecord[] {
    const list = flaggedOnly ? records.filter((r) => r.flagged) : [...records];
    if (sortBy === "time") {
        list.sort((a, b) => a.receivedAt - b.receivedAt);
    } else {
        list.sort((a, b) => b.image.confidence_level - a.image.confidence_level);
    }
    return list;
}

/** Pretty-print image payload for read-only metadata display (not for export). */
function formatImageMetadata(record: OdlcImageRecord): string {
    const { image, receivedAt } = record;
    const [r, g, b] = image.color_detection;
    const lines = [
        `Received: ${new Date(receivedAt).toISOString()}`,
        `Confidence: ${image.confidence_level}%`,
        `Color (RGB): ${r}, ${g}, ${b}`,
        `Bounding box: ${image.bounding_box.map(([x, y]) => `(${x.toFixed(2)}, ${y.toFixed(2)})`).join(", ")}`,
    ];
    return lines.join("\n");
}

function groupByColor(records: OdlcImageRecord[]): Map<string, { label: string; records: OdlcImageRecord[] }> {
    const map = new Map<string, { label: string; records: OdlcImageRecord[] }>();
    for (const record of records) {
        const rgb = record.image.color_detection as RGB;
        const key = getColorGroupKey(rgb);
        const label = getColorGroupLabel(rgb);
        if (!map.has(key)) map.set(key, { label, records: [] });
        map.get(key)!.records.push(record);
    }
    return map;
}

function ColorGroupDropdown({
    _groupKey,
    label,
    records,
    selectedId,
    onSelect,
}: {
    _groupKey: string;
    label: string;
    records: OdlcImageRecord[];
    selectedId: string | null;
    onSelect: (id: string) => void;
}) {
    const [open, setOpen] = useState(true);
    return (
        <Box sx={{ mb: 0.5 }}>
            <Box
                onClick={() => setOpen((o) => !o)}
                sx={{
                    display: "flex",
                    alignItems: "center",
                    cursor: "pointer",
                    py: 0.5,
                    px: 1,
                    borderRadius: 1,
                    "&:hover": { bgcolor: "action.hover" },
                }}
            >
                <Typography variant="body2" fontWeight="medium" sx={{ flex: 1 }}>
                    {label}
                </Typography>
                <IconButton size="small" aria-label={open ? "Collapse" : "Expand"}>
                    {open ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
            </Box>
            <Collapse in={open}>
                <Stack spacing={0.25} sx={{ pl: 1, mt: 0.5 }}>
                    {records.map((record) => (
                        <Box
                            key={record.id}
                            onClick={() => onSelect(record.id)}
                            sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                                p: 0.75,
                                borderRadius: 1,
                                cursor: "pointer",
                                border: "1px solid",
                                borderColor: selectedId === record.id ? "primary.main" : "transparent",
                                bgcolor: selectedId === record.id ? "action.selected" : "transparent",
                                "&:hover": { bgcolor: "action.hover" },
                            }}
                        >
                            <Box
                                component="img"
                                src={`data:image/jpeg;base64,${record.image.image_data}`}
                                alt=""
                                sx={{
                                    width: 40,
                                    height: 40,
                                    borderRadius: 0.5,
                                    objectFit: "cover",
                                    flexShrink: 0,
                                }}
                            />
                            <Typography variant="caption" noWrap sx={{ flex: 1 }}>
                                {new Date(record.receivedAt).toLocaleTimeString()} · {record.image.confidence_level}%
                            </Typography>
                            {record.flagged && <Flag sx={{ fontSize: 14, color: "warning.main" }} />}
                        </Box>
                    ))}
                </Stack>
            </Collapse>
        </Box>
    );
}

export default function OdlcImages() {
    const records = useAppSelector(selectOdlcImageRecords);
    const selectedId = useAppSelector(selectSelectedOdlcImageId);
    const selectedRecord = useAppSelector(selectSelectedOdlcImageRecord);

    const [flaggedOnly, setFlaggedOnly] = useState(false);
    const [sortBy, setSortBy] = useState<SortBy>("time");

    const dispatch = useAppDispatch();
    const handleSelect = useCallback((id: string) => dispatch(setSelectedOdlcImage(id)), [dispatch]);

    const filteredSorted = useMemo(
        () => filterAndSortRecords(records, flaggedOnly, sortBy),
        [records, flaggedOnly, sortBy],
    );
    const grouped = useMemo(() => groupByColor(filteredSorted), [filteredSorted]);

    /** Flagged records in current filter/sort order (export includes only these). */
    const flaggedForExport = useMemo(() => filteredSorted.filter((r) => r.flagged), [filteredSorted]);

    const handleExport = useCallback(() => {
        if (flaggedForExport.length === 0) return;
        const lines = flaggedForExport.map(
            (r) => `[${r.id}] ${new Date(r.receivedAt).toISOString()}\n${r.textInput.trim() || "(no text)"}\n`,
        );
        const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `odlc-export-${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }, [flaggedForExport]);

    useEffect(() => {
        if (records.length > 0 && selectedId === null) {
            dispatch(setSelectedOdlcImage(records[0].id));
        }
    }, [records, selectedId, dispatch]);

    const loadSampleImages = useCallback(() => {
        const samples: OdlcImage[] = [
            createDummyOdlcImage([255, 0, 0], 92),
            createDummyOdlcImage([255, 0, 0], 88),
            createDummyOdlcImage([255, 200, 0], 85),
            createDummyOdlcImage([255, 200, 0], 78),
            createDummyOdlcImage([0, 180, 0], 95),
        ];
        samples.forEach((img) => dispatch(appendOdlcImage(img)));
    }, [dispatch]);

    const handleImageAnnotation = async (args: {
        id: string;
        annotationId: string;
        p1: {
            x: number;
            y: number;
        };
        p2: {
            x: number;
            y: number;
        };
    }) => {
        dispatch(addOdlcImageAnnotation(args));

        const res = await calculateAnnotationDistance(args.p1, args.p2);
        dispatch(
            setOdlcImageAnnotationDistance({
                id: args.id,
                annotationId: args.annotationId,
                distance: res.distance,
            }),
        );
    };

    if (records.length === 0) {
        return (
            <Box sx={{ p: 3, width: "100%" }}>
                <Typography variant="h5" fontWeight="bold" mb={3}>
                    ODLC Images
                </Typography>
                <Paper sx={{ p: 4, textAlign: "center" }}>
                    <Typography color="text.secondary">No ODLC images captured yet.</Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                        Connect to a WebRTC stream to receive images.
                    </Typography>
                    <Button variant="contained" size="small" onClick={loadSampleImages}>
                        Load sample images
                    </Button>
                </Paper>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3, width: "100%", display: "flex", flexDirection: "column", height: "100%" }}>
            <Typography variant="h5" fontWeight="bold" mb={2}>
                ODLC Images
            </Typography>

            <Box sx={{ display: "flex", gap: 2, flex: 1, minHeight: 0 }}>
                {/* Left sidebar */}
                <Paper sx={{ width: 280, flexShrink: 0, p: 1.5, overflow: "auto" }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Filters
                    </Typography>
                    <Stack spacing={1} sx={{ mb: 2 }}>
                        <FormControlLabel
                            control={
                                <Switch size="small" checked={flaggedOnly} onChange={(_, v) => setFlaggedOnly(v)} />
                            }
                            label={<Typography variant="body2">Flagged only</Typography>}
                        />
                        <Box>
                            <Typography variant="caption" color="text.secondary" display="block">
                                Sort
                            </Typography>
                            <ToggleButtonGroup
                                size="small"
                                value={sortBy}
                                exclusive
                                onChange={(_, v) => v != null && setSortBy(v)}
                                fullWidth
                            >
                                <ToggleButton value="time">Time</ToggleButton>
                                <ToggleButton value="confidence">Confidence</ToggleButton>
                            </ToggleButtonGroup>
                        </Box>
                    </Stack>

                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Images by color
                    </Typography>
                    <Stack spacing={0}>
                        {Array.from(grouped.entries()).map(([key, { label, records: groupRecords }]) => (
                            <ColorGroupDropdown
                                key={key}
                                _groupKey={key}
                                label={label}
                                records={groupRecords}
                                selectedId={selectedId}
                                onSelect={handleSelect}
                            />
                        ))}
                    </Stack>
                </Paper>

                {/* Main panel */}
                <Paper sx={{ flex: 1, p: 2, display: "flex", flexDirection: "column", minWidth: 0 }}>
                    <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
                        <Button
                            variant="outlined"
                            size="small"
                            disabled={flaggedForExport.length === 0}
                            onClick={handleExport}
                        >
                            Export
                        </Button>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1 }}>
                        Click &amp; hold to draw a line between 2 points · Ctrl+Z to undo · Double-click a line to
                        delete
                    </Typography>

                    <Box
                        sx={{
                            flex: 1,
                            minHeight: 200,
                            bgcolor: "background.default",
                            borderRadius: 1,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            overflow: "hidden",
                            position: "relative",
                        }}
                    >
                        {selectedRecord ? (
                            <ImageAnnotationOverlay
                                imageSrc={`data:image/jpeg;base64,${selectedRecord.image.image_data}`}
                                annotations={selectedRecord.annotations}
                                recordId={selectedRecord.id}
                                boundingBox={selectedRecord.image.bounding_box}
                                onAddAnnotation={handleImageAnnotation}
                                onUndo={(id) => dispatch(undoLastOdlcImageAnnotation(id))}
                                onDeleteAnnotation={(args) => dispatch(deleteOdlcImageAnnotation(args))}
                            />
                        ) : (
                            <Typography color="text.secondary">Select an image</Typography>
                        )}
                    </Box>

                    {selectedRecord && (
                        <Stack spacing={1.5} sx={{ mt: 2 }}>
                            <TextField
                                label="Text input"
                                size="small"
                                fullWidth
                                multiline
                                minRows={2}
                                value={selectedRecord.textInput}
                                onChange={(e) => {
                                    const next = e.target.value;
                                    const wasEmpty = selectedRecord.textInput.trim() === "";
                                    const nowEmpty = next.trim() === "";
                                    if (wasEmpty && !nowEmpty) {
                                        dispatch(
                                            updateOdlcImageFlag({
                                                id: selectedRecord.id,
                                                flagged: true,
                                            }),
                                        );
                                    }
                                    if (!wasEmpty && nowEmpty) {
                                        dispatch(
                                            updateOdlcImageFlag({
                                                id: selectedRecord.id,
                                                flagged: false,
                                            }),
                                        );
                                    }
                                    dispatch(
                                        updateOdlcImageTextInput({
                                            id: selectedRecord.id,
                                            textInput: next,
                                        }),
                                    );
                                }}
                            />
                            <Box>
                                <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                                    Metadata
                                </Typography>
                                <Box
                                    sx={{
                                        p: 1.5,
                                        borderRadius: 1,
                                        bgcolor: "action.hover",
                                        fontFamily: "monospace",
                                        fontSize: "0.75rem",
                                        whiteSpace: "pre-wrap",
                                        wordBreak: "break-all",
                                    }}
                                >
                                    {formatImageMetadata(selectedRecord)}
                                </Box>
                            </Box>
                            <Box>
                                <Button
                                    variant={selectedRecord.flagged ? "contained" : "outlined"}
                                    size="small"
                                    startIcon={<Flag />}
                                    onClick={() =>
                                        dispatch(
                                            updateOdlcImageFlag({
                                                id: selectedRecord.id,
                                                flagged: !selectedRecord.flagged,
                                            }),
                                        )
                                    }
                                >
                                    {selectedRecord.flagged ? "Flagged" : "Flag"}
                                </Button>
                            </Box>
                        </Stack>
                    )}
                </Paper>
            </Box>
        </Box>
    );
}
