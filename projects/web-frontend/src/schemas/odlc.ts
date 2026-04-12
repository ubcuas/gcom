import { z } from "zod";

export const OdlcImageSchema = z.object({
    image_data: z.string(), // Base64-encoded JPEG color image
    depth_data: z.string().nullable(), // Base64-encoded 16UC1 PNG depthmap, or null if unavailable
    // So the PNG isn't an image but instead each pixel is a 16-bit unsigned integer representing depth in millimeters. We can decode this to get depth values.
    color_detection: z.tuple([z.number().int(), z.number().int(), z.number().int()]),
    bounding_box: z.array(z.tuple([z.number(), z.number()])),
    confidence_level: z.number(),
    yaw_deg: z.number().nullable().optional().default(null), // Aircraft yaw at capture time, degrees clockwise from north
});

export const OdlcImageAnnotationSchema = z.object({
    id: z.string(),
    p1: z.object({ x: z.number(), y: z.number() }),
    p2: z.object({ x: z.number(), y: z.number() }),
    distance: z.number().optional(),
});

export const OdlcImageRecordSchema = z.object({
    id: z.string(),
    receivedAt: z.number(),
    image: OdlcImageSchema,
    flagged: z.boolean(),
    textInput: z.string(),
    metadata: z.string(),
    annotations: z.array(OdlcImageAnnotationSchema),
});

export const OdlcSessionSchema = z.object({
    sessionId: z.string(),
    records: z.array(OdlcImageRecordSchema),
});

export type OdlcImage = z.infer<typeof OdlcImageSchema>;
