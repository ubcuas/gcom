import { z } from "zod";

export const OdlcImageSchema = z.object({
    image_data: z.string(), // Base64-encoded JPEG color image
    depth_data: z.string().nullable(), // Base64-encoded 16UC1 PNG depthmap, or null if unavailable
    // So the PNG isn't an image but instead each pixel is a 16-bit unsigned integer representing depth in millimeters. We can decode this to get depth values.
    color_detection: z.tuple([z.number().int(), z.number().int(), z.number().int()]),
    bounding_box: z.array(z.tuple([z.number(), z.number()])),
    confidence_level: z.number(),
});

export const OdlcSessionPayloadSchema = z.object({
    sessionId: z.string().uuid(),
    images: z.array(OdlcImageSchema),
});

export type OdlcImage = z.infer<typeof OdlcImageSchema>;
