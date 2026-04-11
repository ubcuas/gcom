import { Box } from "@mui/material";
import { useCallback, useEffect, useRef, useState } from "react";
import type { OdlcImageAnnotation } from "../store/slices/dataSlice";

function useImageOverlayRect(imageRef: React.RefObject<HTMLImageElement | null>, imageSrc: string) {
    const [rect, setRect] = useState<{ left: number; top: number; width: number; height: number } | null>(null);
    const parentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const img = imageRef.current;
        const parent = parentRef.current;
        if (!img || !parent) return;
        const update = () => {
            const pr = parent.getBoundingClientRect();
            const ir = img.getBoundingClientRect();
            setRect({
                left: ir.left - pr.left,
                top: ir.top - pr.top,
                width: ir.width,
                height: ir.height,
            });
        };
        update();
        img.addEventListener("load", update);
        const ro = new ResizeObserver(update);
        ro.observe(parent);
        return () => {
            img.removeEventListener("load", update);
            ro.disconnect();
        };
    }, [imageSrc, imageRef]);

    return { rect, parentRef };
}

const HIT_THRESHOLD = 0.02; // normalized units

function hitTestSegment(nx: number, ny: number, p1: { x: number; y: number }, p2: { x: number; y: number }): number {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    const len = Math.hypot(dx, dy) || 1e-9;
    const t = Math.max(0, Math.min(1, ((nx - p1.x) * dx + (ny - p1.y) * dy) / (len * len)));
    const px = p1.x + t * dx;
    const py = p1.y + t * dy;
    return Math.hypot(nx - px, ny - py);
}

/** Bounding box as array of [x, y] in normalized 0-1 coords. Two points define the rectangle. */
export type BoundingBox = Array<[number, number]>;

type ImageAnnotationOverlayProps = {
    imageSrc: string;
    annotations: OdlcImageAnnotation[];
    recordId: string;
    /** Image bounding box (e.g. from ODLC image data); drawn as a rectangle from the first two points. */
    boundingBox?: BoundingBox;
    onAddAnnotation: (args: {
        id: string;
        annotationId: string;
        p1: { x: number; y: number };
        p2: { x: number; y: number };
    }) => void;
    onUndo: (id: string) => void;
    onDeleteAnnotation: (args: { id: string; annotationId: string }) => void;
    instructions?: string;
};

export default function ImageAnnotationOverlay({
    imageSrc,
    annotations,
    recordId,
    boundingBox,
    onAddAnnotation,
    onUndo,
    onDeleteAnnotation,
    instructions,
}: ImageAnnotationOverlayProps) {
    const imageRef = useRef<HTMLImageElement>(null);
    const { rect: overlayRect, parentRef } = useImageOverlayRect(imageRef, imageSrc);
    const [dragging, setDragging] = useState<{ p1: { x: number; y: number }; p2: { x: number; y: number } } | null>(
        null,
    );

    const getNormalizedCoords = useCallback((clientX: number, clientY: number): { x: number; y: number } | null => {
        const el = imageRef.current;
        if (!el) return null;
        const rect = el.getBoundingClientRect();
        const x = (clientX - rect.left) / rect.width;
        const y = (clientY - rect.top) / rect.height;
        return { x, y };
    }, []);

    const handlePointerDown = useCallback(
        (e: React.PointerEvent) => {
            if (e.button !== 0) return;
            const p = getNormalizedCoords(e.clientX, e.clientY);
            if (p) setDragging({ p1: p, p2: p });
        },
        [getNormalizedCoords],
    );

    const handlePointerMove = useCallback(
        (e: React.PointerEvent) => {
            if (!dragging) return;
            const p = getNormalizedCoords(e.clientX, e.clientY);
            if (p) setDragging((d) => (d ? { ...d, p2: p } : null));
        },
        [dragging, getNormalizedCoords],
    );

    const clamp = useCallback((x: number) => Math.max(0, Math.min(1, x)), []);

    const handlePointerUp = useCallback(
        (e: React.PointerEvent) => {
            if (e.button !== 0 || !dragging) return;
            const p = getNormalizedCoords(e.clientX, e.clientY);
            if (p) {
                const p1 = { x: clamp(dragging.p1.x), y: clamp(dragging.p1.y) };
                const p2 = { x: clamp(p.x), y: clamp(p.y) };
                const dist = Math.hypot(p2.x - p1.x, p2.y - p1.y);
                if (dist >= 0.005) {
                    onAddAnnotation({
                        id: recordId,
                        annotationId: crypto.randomUUID(),
                        p1,
                        p2,
                    });
                }
            }
            setDragging(null);
        },
        [dragging, getNormalizedCoords, recordId, onAddAnnotation, clamp],
    );

    const handleDoubleClick = useCallback(
        (e: React.MouseEvent) => {
            const p = getNormalizedCoords(e.clientX, e.clientY);
            if (!p) return;
            let best: { id: string; d: number } | null = null;
            for (const a of annotations) {
                const d = hitTestSegment(p.x, p.y, a.p1, a.p2);
                if (d < HIT_THRESHOLD && (!best || d < best.d)) best = { id: a.id, d };
            }
            if (best) onDeleteAnnotation({ id: recordId, annotationId: best.id });
        },
        [annotations, getNormalizedCoords, recordId, onDeleteAnnotation],
    );

    useEffect(() => {
        const onKeyDown = (e: KeyboardEvent) => {
            if (e.key === "z" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                onUndo(recordId);
            }
        };
        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, [recordId, onUndo]);

    return (
        <Box
            ref={parentRef}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerLeave={() => setDragging(null)}
            onDoubleClick={handleDoubleClick}
            sx={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                maxWidth: "100%",
                maxHeight: "100%",
                cursor: "crosshair",
            }}
        >
            <Box
                component="img"
                ref={imageRef}
                src={imageSrc}
                alt="Annotated"
                draggable={false}
                sx={{
                    display: "block",
                    maxWidth: "100%",
                    maxHeight: "100%",
                    objectFit: "contain",
                    userSelect: "none",
                    pointerEvents: "none",
                }}
            />
            {overlayRect && (
                <Box
                    component="svg"
                    viewBox="0 0 1 1"
                    preserveAspectRatio="none"
                    sx={{
                        position: "absolute",
                        left: overlayRect.left,
                        top: overlayRect.top,
                        width: overlayRect.width,
                        height: overlayRect.height,
                        pointerEvents: "none",
                    }}
                >
                    {boundingBox &&
                        boundingBox.length >= 2 &&
                        (() => {
                            const [[x0, y0], [x1, y1]] = boundingBox;
                            const minX = Math.min(x0, x1);
                            const minY = Math.min(y0, y1);
                            const w = Math.abs(x1 - x0) || 0.01;
                            const h = Math.abs(y1 - y0) || 0.01;
                            return (
                                <rect
                                    x={minX}
                                    y={minY}
                                    width={w}
                                    height={h}
                                    fill="none"
                                    stroke="blue"
                                    strokeWidth={0.012}
                                    strokeDasharray="0.02 0.015"
                                />
                            );
                        })()}
                    {annotations.map((a, i) => (
  <g key={a.id}>
    <line
      x1={a.p1.x}
      y1={a.p1.y}
      x2={a.p2.x}
      y2={a.p2.y}
      stroke="red"
      strokeWidth={0.008}
      strokeLinecap="round"
    />
    {a.distance != null && (
      <text
        x={(a.p1.x + a.p2.x) / 2}
        y={(a.p1.y + a.p2.y) / 2 - 0.03}
        fontSize={0.03}
        fill="blue"
        textAnchor="middle"
        dominantBaseline="middle"
      >
        {a.distance.toFixed(2)}m
      </text>
    )}
  </g>
))}
                    {dragging && (
                        <line
                            x1={dragging.p1.x}
                            y1={dragging.p1.y}
                            x2={dragging.p2.x}
                            y2={dragging.p2.y}
                            stroke="red"
                            strokeWidth={0.008}
                            strokeDasharray="0.02 0.02"
                            strokeLinecap="round"
                        />
                    )}
                </Box>
            )}
            {instructions && (
                <Box
                    sx={{
                        position: "absolute",
                        top: 8,
                        left: 8,
                        right: 8,
                        fontSize: "0.75rem",
                        color: "text.secondary",
                        pointerEvents: "none",
                    }}
                >
                    {instructions}
                </Box>
            )}
        </Box>
    );
}
