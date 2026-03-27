import { Box, IconButton, Paper, Stack, Typography } from "@mui/material";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import { useEffect, useState } from "react";
import { useAppSelector } from "../store/store";
import { selectOldcImages } from "../store/slices/dataSlice";
import type { OldcImage } from "../schemas/oldc";

function ImageMetadata({ image }: { image: OldcImage }) {
    const [r, g, b] = image.color_detection;

    return (
        <Stack spacing={1.5}>
            <Box>
                <Typography variant="caption" color="text.secondary" display="block">
                    Confidence Level
                </Typography>
                <Typography variant="body2">{image.confidence_level}%</Typography>
            </Box>

            <Box>
                <Typography variant="caption" color="text.secondary" display="block">
                    Color Detection (RGB)
                </Typography>
                <Stack direction="row" alignItems="center" spacing={1}>
                    <Box
                        sx={{
                            width: 16,
                            height: 16,
                            borderRadius: "2px",
                            backgroundColor: `rgb(${r}, ${g}, ${b})`,
                            flexShrink: 0,
                            border: "1px solid",
                            borderColor: "divider",
                        }}
                    />
                    <Typography variant="body2">
                        {r}, {g}, {b}
                    </Typography>
                </Stack>
            </Box>

            <Box>
                <Typography variant="caption" color="text.secondary" display="block">
                    Bounding Box
                </Typography>
                <Stack spacing={0.25}>
                    {image.bounding_box.map(([x, y], i) => (
                        <Typography key={i} variant="body2">
                            ({x.toFixed(2)}, {y.toFixed(2)})
                        </Typography>
                    ))}
                </Stack>
            </Box>

            <Box>
                <Typography variant="caption" color="text.secondary" display="block">
                    Image Data
                </Typography>
                <Typography
                    variant="body2"
                    sx={{
                        fontFamily: "monospace",
                        wordBreak: "break-all",
                        fontSize: "0.65rem",
                        color: "text.secondary",
                        maxHeight: 60,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        display: "-webkit-box",
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: "vertical",
                    }}
                >
                    {image.image_data}
                </Typography>
            </Box>
        </Stack>
    );
}

const THUMBNAILS_PER_PAGE = 20;

function ThumbnailGallery({
    images,
    selectedIndex,
    onSelect,
}: {
    images: OldcImage[];
    selectedIndex: number;
    onSelect: (index: number) => void;
}) {
    const totalPages = Math.max(1, Math.ceil(images.length / THUMBNAILS_PER_PAGE));
    const [page, setPage] = useState(0);

    // Auto-advance page when selected index falls outside the current page
    useEffect(() => {
        const selectedPage = Math.floor(selectedIndex / THUMBNAILS_PER_PAGE);
        if (selectedPage !== page) {
            setPage(selectedPage);
        }
    }, [selectedIndex]);

    const pageStart = page * THUMBNAILS_PER_PAGE;
    const pageImages = images.slice(pageStart, pageStart + THUMBNAILS_PER_PAGE);

    return (
        <Stack spacing={1}>
            <Stack direction="row" spacing={1} sx={{ overflowX: "auto", pb: 1 }}>
                {pageImages.map((image, i) => {
                    const globalIndex = pageStart + i;
                    return (
                        <Box
                            key={globalIndex}
                            onClick={() => onSelect(globalIndex)}
                            sx={{
                                flexShrink: 0,
                                width: 72,
                                height: 72,
                                borderRadius: 1,
                                overflow: "hidden",
                                cursor: "pointer",
                                border: "2px solid",
                                borderColor: globalIndex === selectedIndex ? "primary.main" : "transparent",
                                transition: "border-color 0.15s ease",
                                "&:hover": {
                                    borderColor: globalIndex === selectedIndex ? "primary.main" : "divider",
                                },
                            }}
                        >
                            <Box
                                component="img"
                                src={`data:image/jpeg;base64,${image.image_data}`}
                                alt={`OLDC capture ${globalIndex + 1}`}
                                sx={{
                                    width: "100%",
                                    height: "100%",
                                    objectFit: "cover",
                                    display: "block",
                                }}
                            />
                        </Box>
                    );
                })}
            </Stack>

            {totalPages > 1 && (
                <Stack direction="row" alignItems="center" justifyContent="center" spacing={1}>
                    <IconButton size="small" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                        <ChevronLeft fontSize="small" />
                    </IconButton>
                    <Typography variant="caption" color="text.secondary">
                        {page + 1} / {totalPages}
                    </Typography>
                    <IconButton size="small" disabled={page === totalPages - 1} onClick={() => setPage((p) => p + 1)}>
                        <ChevronRight fontSize="small" />
                    </IconButton>
                </Stack>
            )}
        </Stack>
    );
}

export default function OldcImages() {
    const images = useAppSelector(selectOldcImages);
    const [selectedIndex, setSelectedIndex] = useState(0);

    const selected = images[selectedIndex] ?? null;

    if (images.length === 0) {
        return (
            <Box sx={{ p: 8, width: "100%" }}>
                <Typography variant="h5" fontWeight="bold" mb={3}>
                    OLDC Images
                </Typography>
                <Paper sx={{ p: 4, textAlign: "center" }}>
                    <Typography color="text.secondary">No OLDC images captured yet.</Typography>
                    <Typography variant="caption" color="text.secondary">
                        Connect to a WebRTC stream to receive images.
                    </Typography>
                </Paper>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 8, width: "100%" }}>
            <Typography variant="h5" fontWeight="bold" mb={3}>
                OLDC Images
            </Typography>
            <Paper sx={{ p: 3 }}>
                <Stack spacing={3}>
                    <Stack direction="row" spacing={3}>
                        <Box
                            sx={{
                                flex: 1,
                                minWidth: 0,
                                backgroundColor: "background.default",
                                borderRadius: 1,
                                overflow: "hidden",
                                aspectRatio: "4 / 3",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                            }}
                        >
                            {selected && (
                                <Box
                                    component="img"
                                    src={`data:image/jpeg;base64,${selected.image_data}`}
                                    alt={`OLDC capture ${selectedIndex + 1}`}
                                    sx={{
                                        maxWidth: "100%",
                                        maxHeight: "100%",
                                        objectFit: "contain",
                                        display: "block",
                                    }}
                                />
                            )}
                        </Box>

                        <Box sx={{ width: 220, flexShrink: 0 }}>
                            <Typography variant="subtitle2" fontWeight="bold" mb={2}>
                                Image {selectedIndex + 1} of {images.length}
                            </Typography>
                            {selected && <ImageMetadata image={selected} />}
                        </Box>
                    </Stack>

                    <ThumbnailGallery images={images} selectedIndex={selectedIndex} onSelect={setSelectedIndex} />
                </Stack>
            </Paper>
        </Box>
    );
}
