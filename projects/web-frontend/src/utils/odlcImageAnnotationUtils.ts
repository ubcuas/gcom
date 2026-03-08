import { deprojectPixel } from "../api/endpoints";

export const calculateAnnotationDistance = async (
    p1: { x: number; y: number },
    p2: { x: number; y: number },
    depthMap: number[][],
    intrinsics: Object,
): Promise<{ distance: number }> => {
    deprojectPixel();
    return { distance: 0 };
};
