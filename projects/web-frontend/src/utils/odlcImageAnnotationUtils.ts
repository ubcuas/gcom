import { deprojectPixel } from "../api/endpoints";
import { decode } from "fast-png";


/**
 * Hardcoded RealSense D435i color camera intrinsics at 1280x720.
 * These are nominal values — per-unit calibration will differ slightly.
 * Replace with per-device values once intrinsics are included in the WebRTC payload.
 */
// Values from: ros2 topic echo /camera/camera/color/camera_info (1280x720)
const REALSENSE_INTRINSICS = {
    fx: 643.2360229492188,
    fy: 642.1893920898438,
    ppx: 661.8545532226562,
    ppy: 365.9696044921875,
    model: "RS2_DISTORTION_BROWN_CONRADY",
    coeffs: [-0.05651168152689934, 0.06660270690917969, -0.00015544862253591418, 0.0008432056056335568, -0.02149238809943199],
};

/** 
 * Decodes a base64-encoded 16-bit grayscale PNG (ROS2 CompressedImage 16UC1 format)
 * into a flat Uint16Array of depth values in millimeters, plus image dimensions.
 **/

function decodeDepthPngToJson(base64: string): { data: Uint16Array; width: number; height: number } {
    const binaryStr = atob(base64);
    const bytes = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
    }
    
    // Assuming 'decode' is imported from your PNG library (like fast-png)
    const png = decode(bytes);
    const data = png.data as Uint16Array;

    // 1. Convert the Uint16Array into a JavaScript Object (Dictionary)
    // This perfectly matches the format your Python script was reading.
    const depthDict: Record<string, number> = {};
    for (let i = 0; i < data.length; i++) {
        depthDict[i.toString()] = data[i]; 
    }

    // 2. Convert the Dictionary to a JSON text string
    const jsonString = JSON.stringify(depthDict);

    // 3. Create a Blob (a file-like object of raw data) 
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    // 4. Create an invisible link, attach the Blob, and click it to download
    const link = document.createElement("a");
    link.href = url;
    link.download = `depth_data_${Date.now()}.json`;
    
    // Best practice: Append to body before clicking for Firefox compatibility
    document.body.appendChild(link); 
    link.click();
    
    // 5. Clean up the DOM and clear the URL from memory
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    return { data, width: png.width, height: png.height };
}

/**
 * Samples depth (in mm) at a normalized 0-1 coordinate from a decoded 16UC1 depth map.
 * Uses a 5x5 neighbourhood, then discards outlier readings that differ from the median
 * by more than 10% before averaging — this rejects edge-bleed and specular spikes while
 * still smoothing over sensor noise.
 */
function sampleDepth(data: Uint16Array, width: number, height: number, nx: number, ny: number): number {
    const px = Math.floor(nx * width);
    const py = Math.floor(ny * height);

    const radius = 2; // 5x5 window
    const readings: number[] = [];

    for (let dy = -radius; dy <= radius; dy++) {
        for (let dx = -radius; dx <= radius; dx++) {
            const x = Math.max(0, Math.min(width - 1, px + dx));
            const y = Math.max(0, Math.min(height - 1, py + dy));
            const val = data[y * width + x];
            if (val > 0) readings.push(val);
        }
    }

    if (readings.length === 0) return 0;

    // Find the median
    const sorted = [...readings].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];

    // Average only readings within 10% of the median (discard outliers)
    const threshold = median * 0.1;
    let sum = 0;
    let count = 0;
    for (const v of readings) {
        if (Math.abs(v - median) <= threshold) {
            sum += v;
            count++;
        }
    }

    return count > 0 ? sum / count : median;
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

    const { data, width, height } = decodeDepthPngToJson(depthData);
    console.log("Depth data:", data);
        

    const d1Mm = sampleDepth(data, width, height, p1.x, p1.y);
    const d2Mm = sampleDepth(data, width, height, p2.x, p2.y);
    console.log("Sampled depths (mm):", d1Mm, d2Mm);

    if (d1Mm === 0 || d2Mm === 0) {
        console.warn("Distance calculation failed: one or both sampled depths are zero.");
        return null;
    }

    try {
            const [res1, res2] = await Promise.all([
                deprojectPixel([p1.x * width, p1.y * height], REALSENSE_INTRINSICS, d1Mm / 1000),
                deprojectPixel([p2.x * width, p2.y * height], REALSENSE_INTRINSICS, d2Mm / 1000),
            ]);
            console.log("Deprojection results:", res1, res2);

        const [x1, y1, z1] = res1.point;
        const [x2, y2, z2] = res2.point;

        const dist = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2);
        console.log("Calculated distance (m):", dist);
        return { distance: dist };
    } catch (error) {
        console.error("Distance calculation failed during API call:", error);
        return null;
    }
};
