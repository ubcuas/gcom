import { useEffect, useRef, useState } from "react";
import { Box, Button, Chip, Divider, IconButton, Paper, Stack, Toolbar, Tooltip, Typography } from "@mui/material";
import ArrowBack from "@mui/icons-material/ArrowBack";
import ArrowForward from "@mui/icons-material/ArrowForward";
import CheckCircle from "@mui/icons-material/CheckCircle";
import CropFree from "@mui/icons-material/CropFree";
import PanTool from "@mui/icons-material/PanTool";
import PhotoCamera from "@mui/icons-material/PhotoCamera";
import RadioButtonUnchecked from "@mui/icons-material/RadioButtonUnchecked";
import Undo from "@mui/icons-material/Undo";
import { Delete } from "@mui/icons-material";
import { getAnnotationImages, type AnnotationBox, type AnnotationImage } from "../api/endpoints";
import { socket } from "../api/socket";

export default function StreamAnnotations() {
    type ImageBounds = { left: number; top: number; width: number; height: number };

    const [streamImages, setStreamImages] = useState<AnnotationImage[]>([]);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [activeIndex, setActiveIndex] = useState(0);
    const [tool, setTool] = useState<"select" | "box">("select");
    const [annotated, setAnnotated] = useState(false);
    const [annotationsByImage, setAnnotationsByImage] = useState<Record<string, AnnotationBox[]>>({});
    const [imageBounds, setImageBounds] = useState<ImageBounds>({ left: 0, top: 0, width: 100, height: 100 });
    const [draftAnnotation, setDraftAnnotation] = useState<AnnotationBox | null>(null);
    const canvasRef = useRef<HTMLDivElement>(null);
    const imageRef = useRef<HTMLImageElement>(null);
    const dragStart = useRef<{ x: number; y: number } | null>(null);
    const activeImage = streamImages[activeIndex];
    const annotations = activeImage ? annotationsByImage[activeImage.id] ?? activeImage.annotations : [];

    useEffect(() => {
        getAnnotationImages()
            .then((images) => {
                setStreamImages(images);
                setAnnotationsByImage(Object.fromEntries(images.map((image) => [image.id, image.annotations])));
            })
            .catch((error: unknown) => {
                console.error("Unable to load annotation images", error);
                setLoadError("Unable to load annotation images.");
            });

        const handleAnnotationUpdate = (update: { imageId: string; annotations: AnnotationBox[] }) => {
            setAnnotationsByImage((current) => ({ ...current, [update.imageId]: update.annotations }));
        };
        const handleAnnotationError = (error: { error?: string }) => {
            console.error("Annotation synchronization failed", error);
            setLoadError(error.error ?? "Annotation synchronization failed.");
        };
        socket.on("annotation_update", handleAnnotationUpdate);
        socket.on("annotation_error", handleAnnotationError);
        return () => {
            socket.off("annotation_update", handleAnnotationUpdate);
            socket.off("annotation_error", handleAnnotationError);
        };
    }, []);

    const updateImageBounds = () => {
        const canvas = canvasRef.current;
        const image = imageRef.current;
        if (!canvas || !image) return;

        const canvasRect = canvas.getBoundingClientRect();
        const aspectRatio = image.naturalWidth / image.naturalHeight;
        if (!aspectRatio) return;

        const canvasRatio = canvasRect.width / canvasRect.height;
        const width = canvasRatio > aspectRatio ? canvasRect.height * aspectRatio : canvasRect.width;
        const height = canvasRatio > aspectRatio ? canvasRect.height : canvasRect.width / aspectRatio;
        setImageBounds({
            left: ((canvasRect.width - width) / 2 / canvasRect.width) * 100,
            top: ((canvasRect.height - height) / 2 / canvasRect.height) * 100,
            width: (width / canvasRect.width) * 100,
            height: (height / canvasRect.height) * 100,
        });
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const observer = new ResizeObserver(updateImageBounds);
        observer.observe(canvas);
        updateImageBounds();
        return () => observer.disconnect();
    }, [activeIndex]);

    if (!activeImage) {
        return <Box sx={{ display: "grid", placeItems: "center", height: "100vh", bgcolor: "#0b1118" }}>{loadError ?? "Loading annotation images…"}</Box>;
    }

    const publishAnnotations = (nextAnnotations: AnnotationBox[]) => {
        setAnnotationsByImage((current) => ({ ...current, [activeImage.id]: nextAnnotations }));
        socket.emit("annotation_update", { imageId: activeImage.id, annotations: nextAnnotations });
    };

    const goToImage = (index: number) => {
        setActiveIndex((index + streamImages.length) % streamImages.length);
        setAnnotated(false);
        setDraftAnnotation(null);
        dragStart.current = null;
    };

    const getImagePoint = (event: React.PointerEvent<HTMLDivElement>) => {
        const rect = canvasRef.current?.getBoundingClientRect();
        if (!rect) return null;
        const canvasX = ((event.clientX - rect.left) / rect.width) * 100;
        const canvasY = ((event.clientY - rect.top) / rect.height) * 100;
        return {
            x: Math.min(Math.max((canvasX - imageBounds.left) / imageBounds.width, 0), 1),
            y: Math.min(Math.max((canvasY - imageBounds.top) / imageBounds.height, 0), 1),
        };
    };

    const updateDraft = (event: React.PointerEvent<HTMLDivElement>) => {
        if (!dragStart.current) return;
        const point = getImagePoint(event);
        if (!point) return;
        const start = dragStart.current;
        setDraftAnnotation({
            x: Math.min(start.x, point.x),
            y: Math.min(start.y, point.y),
            width: Math.abs(point.x - start.x),
            height: Math.abs(point.y - start.y),
        });
    };

    const finishDrawing = (event: React.PointerEvent<HTMLDivElement>) => {
        if (!dragStart.current) return;
        updateDraft(event);
        const point = getImagePoint(event);
        const start = dragStart.current;
        if (point) {
            const annotation: AnnotationBox = {
                x: Math.min(start.x, point.x),
                y: Math.min(start.y, point.y),
                width: Math.abs(point.x - start.x),
                height: Math.abs(point.y - start.y),
            };
            if (annotation.width > 0.005 && annotation.height > 0.005) {
                publishAnnotations([...annotations, annotation]);
            }
        }
        dragStart.current = null;
        setDraftAnnotation(null);
    };

    return (
        <Box
            sx={{
                display: "flex",
                width: "100%",
                minWidth: 0,
                height: "100vh",
                overflow: "hidden",
                bgcolor: "#0b1118",
            }}
        >
            <Box sx={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", p: { xs: 2, md: 3 }, gap: 2 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between" gap={2}>
                    <Box>
                        <Typography variant="overline" sx={{ color: "#69b8df", letterSpacing: 1.8 }}>
                            LIVE WORKSPACE
                        </Typography>
                        <Typography variant="h5" sx={{ fontWeight: 700 }}>
                            Stream annotations
                        </Typography>
                    </Box>
                    <Stack direction="row" alignItems="center" gap={1}>
                        <Chip
                            size="small"
                            icon={
                                <RadioButtonUnchecked
                                    sx={{ fontSize: "12px !important", color: "#5ee0a0 !important" }}
                                />
                            }
                            label="STREAM ACTIVE"
                            sx={{
                                bgcolor: "rgba(94,224,160,.1)",
                                color: "#8ce8b8",
                                fontWeight: 700,
                                letterSpacing: 0.5,
                            }}
                        />
                        <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ display: { xs: "none", sm: "block" } }}
                        >
                            Mission 04 · North field
                        </Typography>
                    </Stack>
                </Stack>

                <Paper
                    elevation={0}
                    sx={{
                        flex: 1,
                        minHeight: 0,
                        display: "flex",
                        flexDirection: "column",
                        overflow: "hidden",
                        bgcolor: "#111b25",
                        border: "1px solid #263543",
                        borderRadius: 2,
                    }}
                >
                    <Stack
                        direction="row"
                        alignItems="center"
                        justifyContent="space-between"
                        sx={{ px: 2, py: 1.25, borderBottom: "1px solid #263543" }}
                    >
                        <Stack direction="row" alignItems="center" gap={1.25}>
                            <PhotoCamera sx={{ color: "#71bee4", fontSize: 19 }} />
                            <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                                {activeImage.id}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                {activeImage.time}
                            </Typography>
                        </Stack>
                        <Stack direction="row" alignItems="center" gap={1}>
                            <Tooltip title="Undo annotation">
                                <span>
                                    <IconButton
                                        size="small"
                                        disabled={!annotations.length}
                                        onClick={() =>
                                            publishAnnotations(annotations.slice(0, -1))
                                        }
                                    >
                                        <Undo fontSize="small" />
                                    </IconButton>
                                </span>
                            </Tooltip>
                            <Divider orientation="vertical" flexItem sx={{ borderColor: "#344451" }} />
                            <Tooltip title="Select / pan">
                                <IconButton
                                    size="small"
                                    onClick={() => setTool("select")}
                                    sx={{
                                        color: tool === "select" ? "#79c7ee" : "text.secondary",
                                        bgcolor: tool === "select" ? "rgba(45,160,220,.12)" : "transparent",
                                    }}
                                >
                                    <PanTool fontSize="small" />
                                </IconButton>
                            </Tooltip>
                            <Tooltip title="Draw bounding box">
                                <IconButton
                                    size="small"
                                    onClick={() => setTool("box")}
                                    sx={{
                                        color: tool === "box" ? "#79c7ee" : "text.secondary",
                                        bgcolor: tool === "box" ? "rgba(45,160,220,.12)" : "transparent",
                                    }}
                                >
                                    <CropFree fontSize="small" />
                                </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete bounding box">
                                <IconButton
                                    size="small"
                                    onClick={() =>
                                        publishAnnotations(annotations.slice(0, -1))
                                    }
                                >
                                    <Delete fontSize="small" />
                                </IconButton>
                            </Tooltip>
                        </Stack>
                    </Stack>

                    <Box
                        ref={canvasRef}
                        onPointerDown={(event) => {
                            if (tool !== "box") return;
                            const point = getImagePoint(event);
                            if (!point) return;
                            dragStart.current = point;
                            event.currentTarget.setPointerCapture(event.pointerId);
                            setDraftAnnotation({ x: point.x, y: point.y, width: 0, height: 0 });
                        }}
                        onPointerMove={updateDraft}
                        onPointerUp={finishDrawing}
                        onPointerCancel={finishDrawing}
                        sx={{
                            position: "relative",
                            flex: 1,
                            minHeight: 0,
                            overflow: "hidden",
                            bgcolor: "#070b10",
                            cursor: tool === "box" ? "crosshair" : "grab",
                            touchAction: "none",
                        }}
                    >
                        <Box
                            ref={imageRef}
                            component="img"
                            src={activeImage.image}
                            onLoad={updateImageBounds}
                            alt={`Stream frame ${activeImage.id}`}
                            sx={{
                                width: "100%",
                                height: "100%",
                                objectFit: "contain",
                                userSelect: "none",
                                pointerEvents: "none",
                            }}
                        />
                        {[...annotations, ...(draftAnnotation ? [draftAnnotation] : [])].map((annotation, index) => (
                            <Box
                                key={`${annotation.x}-${annotation.y}-${index}`}
                                sx={{
                                    position: "absolute",
                                    left: `${imageBounds.left + annotation.x * imageBounds.width}%`,
                                    top: `${imageBounds.top + annotation.y * imageBounds.height}%`,
                                    width: `${annotation.width * imageBounds.width}%`,
                                    height: `${annotation.height * imageBounds.height}%`,
                                    border: "2px solid #58c6ff",
                                    bgcolor: "rgba(45,160,220,.12)",
                                    boxShadow: "0 0 0 1px rgba(0,0,0,.5)",
                                    pointerEvents: "none",
                                }}
                            >
                                <Typography
                                    sx={{
                                        position: "absolute",
                                        top: -22,
                                        left: -2,
                                        px: 0.6,
                                        bgcolor: "#1687c1",
                                        color: "white",
                                        fontSize: 10,
                                        fontWeight: 700,
                                    }}
                                >
                                    TARGET {index + 1}
                                </Typography>
                            </Box>
                        ))}
                        <Chip
                            size="small"
                            label={activeImage.location}
                            sx={{
                                position: "absolute",
                                left: 16,
                                bottom: 16,
                                bgcolor: "rgba(6,12,18,.8)",
                                color: "#d6e1e8",
                                border: "1px solid rgba(255,255,255,.16)",
                            }}
                        />
                        <Chip
                            size="small"
                            label={`${annotations.length} annotation${annotations.length === 1 ? "" : "s"}`}
                            sx={{
                                position: "absolute",
                                right: 16,
                                bottom: 16,
                                bgcolor: "rgba(6,12,18,.8)",
                                color: "#d6e1e8",
                                border: "1px solid rgba(255,255,255,.16)",
                            }}
                        />
                    </Box>

                    <Stack
                        direction="row"
                        alignItems="center"
                        justifyContent="space-between"
                        sx={{ px: 2, py: 1.5, borderTop: "1px solid #263543" }}
                    >
                        <Button size="small" startIcon={<ArrowBack />} onClick={() => goToImage(activeIndex - 1)}>
                            Previous
                        </Button>
                        <Typography variant="caption" color="text.secondary">
                            FRAME {String(activeIndex + 1).padStart(2, "0")} /{" "}
                            {String(streamImages.length).padStart(2, "0")}
                        </Typography>
                        <Stack direction="row" gap={1}>
                            <Button size="small" onClick={() => goToImage(activeIndex + 1)} endIcon={<ArrowForward />}>
                                Next frame
                            </Button>
                            <Button
                                size="small"
                                variant="contained"
                                startIcon={<CheckCircle />}
                                onClick={() => setAnnotated(true)}
                                sx={{ minWidth: 128 }}
                            >
                                {annotated ? "Saved" : "Mark reviewed"}
                            </Button>
                        </Stack>
                    </Stack>
                </Paper>
            </Box>

            <Paper
                square
                elevation={0}
                sx={{
                    width: { xs: 220, sm: 270 },
                    flexShrink: 0,
                    display: "flex",
                    flexDirection: "column",
                    bgcolor: "#0e1720",
                    borderLeft: "1px solid #263543",
                }}
            >
                <Box sx={{ px: 2, pt: 3, pb: 2 }}>
                    <Typography variant="overline" sx={{ color: "#8495a3", letterSpacing: 1.5 }}>
                        ANNOTATION QUEUE
                    </Typography>
                    <Stack direction="row" justifyContent="space-between" alignItems="baseline">
                        <Typography variant="h6" sx={{ fontWeight: 700 }}>
                            Recently annotated
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            {streamImages.length}
                        </Typography>
                    </Stack>
                </Box>
                <Divider sx={{ borderColor: "#263543" }} />
                <Stack spacing={1} sx={{ p: 1.25, overflowY: "auto" }}>
                    {streamImages.map((image, index) => {
                        const isActive = index === activeIndex;
                        const isDone = image.status === "Annotated" || (isActive && annotated);
                        return (
                            <Paper
                                key={image.id}
                                onClick={() => goToImage(index)}
                                elevation={0}
                                sx={{
                                    p: 1,
                                    cursor: "pointer",
                                    bgcolor: isActive ? "rgba(45,160,220,.12)" : "transparent",
                                    border: `1px solid ${isActive ? "#2da0dc" : "transparent"}`,
                                    borderRadius: 1.5,
                                    transition: "all .15s",
                                    "&:hover": { bgcolor: "rgba(255,255,255,.04)" },
                                }}
                            >
                                <Box
                                    sx={{
                                        position: "relative",
                                        height: 104,
                                        overflow: "hidden",
                                        borderRadius: 1,
                                        bgcolor: "#18232e",
                                    }}
                                >
                                    <Box
                                        component="img"
                                        src={image.image}
                                        alt={image.id}
                                        sx={{ width: "100%", height: "100%", objectFit: "cover" }}
                                    />
                                    <Chip
                                        size="small"
                                        label={isDone ? "REVIEWED" : "NEW"}
                                        sx={{
                                            position: "absolute",
                                            top: 7,
                                            left: 7,
                                            height: 20,
                                            fontSize: 9,
                                            fontWeight: 700,
                                            bgcolor: isDone ? "rgba(30,130,85,.9)" : "rgba(190,126,37,.92)",
                                            color: "white",
                                        }}
                                    />
                                </Box>
                                <Stack
                                    direction="row"
                                    justifyContent="space-between"
                                    alignItems="center"
                                    sx={{ pt: 1 }}
                                >
                                    <Box>
                                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                                            {image.id}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            {image.time}
                                        </Typography>
                                    </Box>
                                    <Typography variant="caption" sx={{ color: isDone ? "#78d8a4" : "#eab760" }}>
                                        {isDone ? "Reviewed" : "Pending"}
                                    </Typography>
                                </Stack>
                            </Paper>
                        );
                    })}
                </Stack>
            </Paper>
        </Box>
    );
}
