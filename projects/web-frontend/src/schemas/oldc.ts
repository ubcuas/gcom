import { z } from "zod";

export const OldcImageSchema = z.object({
    image_data: z.string(),
    color_detection: z.tuple([z.number().int(), z.number().int(), z.number().int()]),
    bounding_box: z.array(z.tuple([z.number(), z.number()])),
    confidence_level: z.number().int(),
});

export const OldcSessionPayloadSchema = z.object({
    sessionId: z.string().uuid(),
    images: z.array(OldcImageSchema),
});

export type OldcImage = z.infer<typeof OldcImageSchema>;
