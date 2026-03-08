import { deprojectPixel } from "../api/endpoints";
import { decode } from "fast-png";

/**
 * Hardcoded RealSense D435i color camera intrinsics at 1280x720.
 * These are nominal values — per-unit calibration will differ slightly.
 * Replace with per-device values once intrinsics are included in the WebRTC payload.
 */
const REALSENSE_INTRINSICS = {
    fx: 921.0,
    fy: 921.0,
    ppx: 640.0,
    ppy: 360.0,
    model: "RS2_DISTORTION_BROWN_CONRADY",
    coeffs: [0, 0, 0, 0, 0],
};

/**
 * Decodes a base64-encoded 16-bit grayscale PNG (ROS2 CompressedImage 16UC1 format)
 * into a flat Uint16Array of depth values in millimeters, plus image dimensions.
 */
function decodeDepthPng(base64: string): { data: Uint16Array; width: number; height: number } {
    const binaryStr = atob(base64);
    const bytes = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
    }
    const png = decode(bytes);
    return { data: png.data as Uint16Array, width: png.width, height: png.height };
}

/**
 * Samples depth (in mm) at a normalized 0-1 coordinate from a decoded 16UC1 depth map.
 * Uses nearest-neighbor with boundary clamping.
 */
function sampleDepth(data: Uint16Array, width: number, height: number, nx: number, ny: number): number {
    const px = Math.max(0, Math.min(width - 1, Math.floor(nx * width)));
    const py = Math.max(0, Math.min(height - 1, Math.floor(ny * height)));
    return data[py * width + px];
}

/**
 * Computes the true 3D Euclidean distance (in meters) between two annotation points
 * drawn on a 2D ODLC image, using the associated depth map and camera intrinsics.
 *
 * Process:
 *  1. Decodes the base64-encoded 16UC1 PNG depth map into a Uint16Array of mm values
 *  2. Samples depth at each normalized (0-1) point coordinate via nearest-neighbor
 *  3. Calls the backend /vision/deproject_pixel/ for each point to get
 *     3D camera-space coordinates [x, y, z] in meters
 *  4. Returns the Euclidean distance sqrt((x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2)
 *
 * Returns null if depth_data is unavailable or either sampled depth is zero
 * (meaning the depth sensor returned no reading at that pixel).
 */
export const calculateAnnotationDistance = async (
    p1: { x: number; y: number },
    p2: { x: number; y: number },
    depthData: string | null,
): Promise<{ distance: number } | null> => {
    if (!depthData) return null;

    const { data, width, height } = decodeDepthPng(depthData);

    const d1Mm = sampleDepth(data, width, height, p1.x, p1.y);
    const d2Mm = sampleDepth(data, width, height, p2.x, p2.y);

    if (d1Mm === 0 || d2Mm === 0) return null;

    const [res1, res2] = await Promise.all([
        deprojectPixel([p1.x * width, p1.y * height], REALSENSE_INTRINSICS, d1Mm / 1000),
        deprojectPixel([p2.x * width, p2.y * height], REALSENSE_INTRINSICS, d2Mm / 1000),
    ]);

    const [x1, y1, z1] = res1.point;
    const [x2, y2, z2] = res2.point;

    return { distance: Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) };
};
