import { useRef, useState } from "react";
import { MEDIAMTX_STREAM, MEDIAMTX_URL } from "../constants";

type PeerStatus = "disconnected" | "connecting" | "connected" | "failed";

type UseWebRTCConnectionResult = {
    peerStatus: PeerStatus;
    remoteStream: MediaStream | null;
    connect: () => void;
    disconnect: () => void;
    isConnecting: boolean;
};

// How long to wait for the browser to find its network addresses before sending the offer anyway
const ICE_GATHERING_TIMEOUT_MS = 2000;

// MediaMTX doesn't accept ICE candidates sent one at a time without extra requests,
// so wait until they are all included in the offer
const waitForIceGathering = (pc: RTCPeerConnection): Promise<void> =>
    new Promise((resolve) => {
        if (pc.iceGatheringState === "complete") {
            resolve();
            return;
        }
        const onChange = () => {
            if (pc.iceGatheringState === "complete") {
                pc.removeEventListener("icegatheringstatechange", onChange);
                resolve();
            }
        };
        pc.addEventListener("icegatheringstatechange", onChange);
        setTimeout(resolve, ICE_GATHERING_TIMEOUT_MS);
    });

/**
 * Receives a video stream from MediaMTX over WebRTC.
 *
 * The connection is set up with WHEP: the browser POSTs its offer to
 * `<MEDIAMTX_URL>/<stream>/whep` and MediaMTX replies with the answer.
 * Ending the session is a DELETE to the URL MediaMTX returns in the Location header.
 */
export function useWebRTCConnection(): UseWebRTCConnectionResult {
    const [peerStatus, setPeerStatus] = useState<PeerStatus>("disconnected");
    const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);

    const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
    const sessionUrlRef = useRef<string | null>(null);

    const deleteSession = (sessionUrl: string) => {
        fetch(sessionUrl, { method: "DELETE" }).catch((error) => {
            console.warn("Failed to end MediaMTX session:", error);
        });
    };

    const closeConnection = () => {
        if (sessionUrlRef.current) {
            deleteSession(sessionUrlRef.current);
            sessionUrlRef.current = null;
        }

        if (peerConnectionRef.current) {
            peerConnectionRef.current.close();
            peerConnectionRef.current = null;
        }

        setRemoteStream(null);
    };

    const startConnection = async () => {
        // Start fresh, e.g. after a failed or dropped connection
        closeConnection();
        setPeerStatus("connecting");

        const pc = new RTCPeerConnection();
        peerConnectionRef.current = pc;
        pc.addTransceiver("video", { direction: "recvonly" });

        pc.addEventListener("track", (event) => {
            console.log("Remote track received:", event.track.kind);
            setRemoteStream(event.streams[0] ?? new MediaStream([event.track]));
        });

        pc.addEventListener("connectionstatechange", () => {
            console.log("Connection state:", pc.connectionState);
            if (peerConnectionRef.current !== pc) return;

            if (pc.connectionState === "connected") {
                setPeerStatus("connected");
            } else if (pc.connectionState === "failed") {
                closeConnection();
                setPeerStatus("failed");
            } else if (pc.connectionState === "disconnected") {
                setPeerStatus("disconnected");
            }
        });

        try {
            await pc.setLocalDescription(await pc.createOffer());
            await waitForIceGathering(pc);

            const whepUrl = `${MEDIAMTX_URL}/${MEDIAMTX_STREAM}/whep`;
            console.log("Sending offer to", whepUrl);
            const response = await fetch(whepUrl, {
                method: "POST",
                headers: { "Content-Type": "application/sdp" },
                body: pc.localDescription?.sdp,
            });
            const responseText = await response.text();

            if (response.status !== 201) {
                throw new Error(`MediaMTX returned ${response.status}: ${responseText}`);
            }

            const location = response.headers.get("Location");
            const sessionUrl = location ? new URL(location, whepUrl).toString() : null;

            // Disconnected while waiting for MediaMTX
            if (peerConnectionRef.current !== pc) {
                if (sessionUrl) deleteSession(sessionUrl);
                return;
            }

            sessionUrlRef.current = sessionUrl;
            await pc.setRemoteDescription({ type: "answer", sdp: responseText });
        } catch (error) {
            console.error("Failed to start video stream:", error);
            if (peerConnectionRef.current === pc) {
                closeConnection();
                setPeerStatus("failed");
            }
        }
    };

    const connect = () => {
        void startConnection();
    };

    const disconnect = () => {
        closeConnection();
        setPeerStatus("disconnected");
    };

    return {
        peerStatus,
        remoteStream,
        connect,
        disconnect,
        isConnecting: peerStatus === "connecting",
    };
}
