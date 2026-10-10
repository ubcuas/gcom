import {
    Box,
    Button,
    ButtonBase,
    Chip,
    Dialog,
    DialogContent,
    DialogTitle,
    Grid,
    IconButton,
    Paper,
    Stack,
    TextField,
    Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import VideocamIcon from "@mui/icons-material/Videocam";
import { useEffect, useRef, useState } from "react";

// UI mockup only: everything on this page is hardcoded and nothing is sent to a backend.

type BoundingBox = { x: number; y: number; width: number; height: number };

type TagDetection = {
    id: string;
    imageSrc: string;
    imageWidth: number;
    imageHeight: number;
    /** Tag region in source image pixels, origin top-left. */
    bbox: BoundingBox;
    prediction: string;
    confidence: number;
};

type Review = { status: "accepted" | "rejected" } | { status: "reannotated"; text: string };

const MOCK_DETECTIONS: TagDetection[] = [
    {
        id: "deer-1-left",
        imageSrc: "/stream-annotation/deer-1.jpg",
        imageWidth: 736,
        imageHeight: 736,
        bbox: { x: 100, y: 188, width: 122, height: 182 },
        prediction: "R7WH 409",
        confidence: 0.91,
    },
    {
        id: "deer-2-right",
        imageSrc: "/stream-annotation/deer-2.jpg",
        imageWidth: 1024,
        imageHeight: 684,
        bbox: { x: 625, y: 154, width: 132, height: 219 },
        prediction: "204",
        confidence: 0.97,
    },
    {
        id: "deer-2-left",
        imageSrc: "/stream-annotation/deer-2.jpg",
        imageWidth: 1024,
        imageHeight: 684,
        bbox: { x: 274, y: 230, width: 135, height: 124 },
        prediction: "JULIA BUTLER HANSEN NATIONAL WILDLIFE REFUGE 360-795-3915",
        confidence: 0.64,
    },
];

const BBOX_COLOR = "#ffeb3b";

// Animation timing: how long each image stays on screen, and the gap before each of its tags is "detected".
const FRAME_DURATION_MS = 4000;
const DETECTION_DELAY_MS = 1000;

/** Source images in the order they play, each listed once. */
const FRAME_SOURCES = [...new Set(MOCK_DETECTIONS.map((detection) => detection.imageSrc))];

/** Shows only the bounding box region of the source image, scaled to fit within maxHeight. */
function TagCrop({ detection, maxHeight }: { detection: TagDetection; maxHeight: number }) {
    const { bbox, imageWidth, imageSrc } = detection;
    return (
        <Box
            sx={{
                position: "relative",
                width: "100%",
                maxWidth: (maxHeight * bbox.width) / bbox.height,
                aspectRatio: `${bbox.width} / ${bbox.height}`,
                overflow: "hidden",
                borderRadius: 1,
                mx: "auto",
            }}
        >
            <img
                src={imageSrc}
                alt={`Tag crop: ${detection.prediction}`}
                style={{
                    position: "absolute",
                    width: `${(imageWidth / bbox.width) * 100}%`,
                    maxWidth: "none",
                    left: `${(-bbox.x / bbox.width) * 100}%`,
                    top: `${(-bbox.y / bbox.height) * 100}%`,
                }}
            />
        </Box>
    );
}

/** Outline of the tag region. Must sit inside a positioned box that exactly wraps the source image. */
function BoundingBoxOutline({ detection }: { detection: TagDetection }) {
    const { bbox, imageWidth, imageHeight } = detection;
    return (
        <Box
            sx={{
                position: "absolute",
                left: `${(bbox.x / imageWidth) * 100}%`,
                top: `${(bbox.y / imageHeight) * 100}%`,
                width: `${(bbox.width / imageWidth) * 100}%`,
                height: `${(bbox.height / imageHeight) * 100}%`,
                border: `3px solid ${BBOX_COLOR}`,
                boxShadow: "0 0 0 1px rgba(0,0,0,0.6)",
                pointerEvents: "none",
            }}
        />
    );
}

/** Shows the whole source image with the tag region outlined. */
function FullImageWithBox({ detection }: { detection: TagDetection }) {
    return (
        <Box sx={{ position: "relative", borderRadius: 1, overflow: "hidden", lineHeight: 0 }}>
            <img src={detection.imageSrc} alt="Full frame" style={{ width: "100%", display: "block" }} />
            <BoundingBoxOutline detection={detection} />
        </Box>
    );
}

/** One slideshow image filling the video area's height, with outlines for the tags detected so far. */
function StreamFrame({ src, detectedIds }: { src: string; detectedIds: string[] }) {
    const frameDetections = MOCK_DETECTIONS.filter((detection) => detection.imageSrc === src);
    const { imageWidth, imageHeight } = frameDetections[0];
    return (
        <Box
            sx={{
                position: "relative",
                height: "100%",
                aspectRatio: `${imageWidth} / ${imageHeight}`,
            }}
        >
            <img src={src} alt="Stream frame" style={{ width: "100%", height: "100%", display: "block" }} />
            {frameDetections
                .filter((detection) => detectedIds.includes(detection.id))
                .map((detection) => (
                    <BoundingBoxOutline key={detection.id} detection={detection} />
                ))}
        </Box>
    );
}

function ReviewChip({ review }: { review: Review | undefined }) {
    if (!review) return <Chip label="Pending" size="small" />;
    switch (review.status) {
        case "accepted":
            return <Chip label="Accepted" size="small" color="success" />;
        case "rejected":
            return <Chip label="Rejected" size="small" color="error" />;
        case "reannotated":
            return <Chip label="Re-Annotated" size="small" color="primary" />;
    }
}

function tagText(detection: TagDetection, review: Review | undefined): string {
    return review?.status === "reannotated" ? review.text : detection.prediction;
}

type AnnotationModalProps = {
    detection: TagDetection;
    review: Review | undefined;
    onReview: (review: Review) => void;
    onClose: () => void;
};

function AnnotationModal({ detection, review, onReview, onClose }: AnnotationModalProps) {
    const [reannotating, setReannotating] = useState(false);
    const [draft, setDraft] = useState("");

    const saveDraft = () => {
        onReview({ status: "reannotated", text: draft.trim() });
        setReannotating(false);
    };

    return (
        <Dialog open onClose={onClose} maxWidth="lg" fullWidth>
            <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                Tag Annotation
                <IconButton onClick={onClose} aria-label="Close" size="small">
                    <CloseIcon />
                </IconButton>
            </DialogTitle>
            <DialogContent dividers>
                <Grid container spacing={3}>
                    <Grid item xs={12} md={7}>
                        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                            Full Image
                        </Typography>
                        <FullImageWithBox detection={detection} />
                    </Grid>
                    <Grid item xs={12} md={5}>
                        <Stack spacing={2}>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                                    Detected Tag
                                </Typography>
                                <TagCrop detection={detection} maxHeight={320} />
                            </Box>
                            <Box>
                                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
                                    <Typography variant="subtitle2" color="text.secondary">
                                        {review?.status === "reannotated" ? "Annotated Tag Text" : "Predicted Tag Text"}
                                    </Typography>
                                    <ReviewChip review={review} />
                                </Stack>
                                <Typography variant="h5" sx={{ fontFamily: "monospace", fontWeight: "bold" }}>
                                    {tagText(detection, review)}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                    Prediction confidence: {Math.round(detection.confidence * 100)}%
                                </Typography>
                            </Box>
                            <Stack direction="row" spacing={1}>
                                <Button
                                    variant="contained"
                                    color="success"
                                    fullWidth
                                    onClick={() => onReview({ status: "accepted" })}
                                >
                                    Accept
                                </Button>
                                <Button
                                    variant="contained"
                                    color="error"
                                    fullWidth
                                    onClick={() => onReview({ status: "rejected" })}
                                >
                                    Reject
                                </Button>
                                <Button
                                    variant="outlined"
                                    fullWidth
                                    onClick={() => {
                                        setDraft(tagText(detection, review));
                                        setReannotating(true);
                                    }}
                                >
                                    Re-Annotate
                                </Button>
                            </Stack>
                            {reannotating && (
                                <Stack spacing={1}>
                                    <TextField
                                        label="What does the tag say?"
                                        value={draft}
                                        onChange={(event) => setDraft(event.target.value)}
                                        autoFocus
                                        fullWidth
                                        multiline
                                    />
                                    <Stack direction="row" spacing={1} justifyContent="flex-end">
                                        <Button onClick={() => setReannotating(false)}>Cancel</Button>
                                        <Button variant="contained" disabled={!draft.trim()} onClick={saveDraft}>
                                            Save
                                        </Button>
                                    </Stack>
                                </Stack>
                            )}
                        </Stack>
                    </Grid>
                </Grid>
            </DialogContent>
        </Dialog>
    );
}

export default function StreamAnnotation() {
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [reviews, setReviews] = useState<Record<string, Review>>({});
    // Ids of the tags shown in the sidebar, newest first.
    const [detectedIds, setDetectedIds] = useState<string[]>(() => MOCK_DETECTIONS.map((detection) => detection.id));
    const [frameSrc, setFrameSrc] = useState<string | null>(null);
    const [playing, setPlaying] = useState(false);
    const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

    useEffect(() => {
        return () => timersRef.current.forEach(clearTimeout);
    }, []);

    const playAnimation = () => {
        timersRef.current.forEach(clearTimeout);
        const schedule = (callback: () => void, delayMs: number) => {
            timersRef.current.push(setTimeout(callback, delayMs));
        };

        setDetectedIds([]);
        setReviews({});
        setPlaying(true);
        FRAME_SOURCES.forEach((src, frameIndex) => {
            const frameStartMs = frameIndex * FRAME_DURATION_MS;
            schedule(() => setFrameSrc(src), frameStartMs);
            MOCK_DETECTIONS.filter((detection) => detection.imageSrc === src).forEach((detection, tagIndex) => {
                schedule(
                    () => setDetectedIds((prev) => [detection.id, ...prev]),
                    frameStartMs + (tagIndex + 1) * DETECTION_DELAY_MS,
                );
            });
        });
        schedule(() => setPlaying(false), FRAME_SOURCES.length * FRAME_DURATION_MS);
    };

    const selected = MOCK_DETECTIONS.find((detection) => detection.id === selectedId);
    const sidebarDetections = detectedIds.flatMap(
        (id) => MOCK_DETECTIONS.find((detection) => detection.id === id) ?? [],
    );

    return (
        <Box
            sx={{
                p: 8,
                width: "100%",
            }}
        >
            <Paper
                sx={{
                    p: 3,
                }}
            >
                <Grid container spacing={3}>
                    <Grid item xs={12} lg={9}>
                        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={3}>
                            <Stack direction="row" alignItems="center" spacing={2}>
                                <Typography
                                    variant="h4"
                                    sx={{
                                        fontWeight: "bold",
                                    }}
                                >
                                    Stream Annotation
                                </Typography>
                                <Chip label="Mockup" size="small" variant="outlined" />
                            </Stack>
                            <Button
                                variant="contained"
                                size="small"
                                startIcon={<PlayArrowIcon fontSize="small" />}
                                onClick={playAnimation}
                                disabled={playing}
                            >
                                {playing ? "Playing..." : "Play Animation"}
                            </Button>
                        </Stack>
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
                                {frameSrc ? (
                                    <StreamFrame src={frameSrc} detectedIds={detectedIds} />
                                ) : (
                                    <>
                                        <VideocamIcon sx={{ fontSize: 64, opacity: 0.3 }} />
                                        <Typography variant="body1">Video stream placeholder</Typography>
                                    </>
                                )}
                            </Box>
                        </Box>
                    </Grid>

                    <Grid item xs={12} lg={3}>
                        <Typography variant="h6" sx={{ fontWeight: "bold", mb: 2 }}>
                            Detected Tags ({sidebarDetections.length})
                        </Typography>
                        <Stack spacing={2} sx={{ maxHeight: "75vh", overflowY: "auto", pr: 1 }}>
                            {sidebarDetections.length === 0 && (
                                <Typography variant="body2" color="text.secondary">
                                    Waiting for detections...
                                </Typography>
                            )}
                            {sidebarDetections.map((detection) => (
                                <ButtonBase
                                    key={detection.id}
                                    onClick={() => setSelectedId(detection.id)}
                                    sx={{ display: "block", textAlign: "left", borderRadius: 1, flexShrink: 0 }}
                                >
                                    <Paper
                                        variant="outlined"
                                        sx={{ p: 1.5, "&:hover": { borderColor: "primary.main" } }}
                                    >
                                        <TagCrop detection={detection} maxHeight={140} />
                                        <Stack
                                            direction="row"
                                            alignItems="center"
                                            justifyContent="space-between"
                                            spacing={1}
                                            sx={{ mt: 1 }}
                                        >
                                            <Typography variant="body2" noWrap sx={{ fontFamily: "monospace" }}>
                                                {tagText(detection, reviews[detection.id])}
                                            </Typography>
                                            <ReviewChip review={reviews[detection.id]} />
                                        </Stack>
                                    </Paper>
                                </ButtonBase>
                            ))}
                        </Stack>
                    </Grid>
                </Grid>
            </Paper>

            {selected && (
                <AnnotationModal
                    key={selected.id}
                    detection={selected}
                    review={reviews[selected.id]}
                    onReview={(review) => setReviews((prev) => ({ ...prev, [selected.id]: review }))}
                    onClose={() => setSelectedId(null)}
                />
            )}
        </Box>
    );
}
