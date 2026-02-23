import { createContext, useContext, ReactNode } from "react";
import { useWebRTCConnection } from "../hooks/useWebRTCConnection";

type WebRTCContextValue = ReturnType<typeof useWebRTCConnection>;

const WebRTCContext = createContext<WebRTCContextValue | null>(null);

export function WebRTCProvider({ children }: { children: ReactNode }) {
    const webrtc = useWebRTCConnection();
    return <WebRTCContext.Provider value={webrtc}>{children}</WebRTCContext.Provider>;
}

export function useWebRTCContext(): WebRTCContextValue {
    const ctx = useContext(WebRTCContext);
    if (!ctx) {
        throw new Error("useWebRTCContext must be used within a WebRTCProvider");
    }
    return ctx;
}
