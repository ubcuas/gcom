import { z } from "zod";

export const OldcImageSchema = z.object({
    image: z.string(),
    metadata: z.record(z.string(), z.unknown()),
});

export const OldcSessionPayloadSchema = z.object({
    sessionId: z.string().uuid(),
    images: z.array(OldcImageSchema),
});

export type OldcImage = z.infer<typeof OldcImageSchema>;
