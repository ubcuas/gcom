const VITE_MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY;

if (!VITE_MAPTILER_KEY && window.navigator.onLine) {
    throw new Error(
        "VITE_MAPTILER_KEY environment variable is not set. " +
            "Please copy .env.example to .env and configure it with your MapTiler API key.",
    );
}

export const MAPTILER_API_KEY = VITE_MAPTILER_KEY as string;

export const MAP_STYLE_ONLINE = `https://api.maptiler.com/maps/hybrid/style.json?key=${MAPTILER_API_KEY}`;
export const MAP_STYLE_OFFLINE = "http://localhost:8000/api/map-tiles/osmbright";
export const MAP_STYLE = window.navigator.onLine ? MAP_STYLE_ONLINE : MAP_STYLE_OFFLINE;

// MediaMTX serves the camera streams to the browser over WebRTC
export const MEDIAMTX_URL = (import.meta.env.VITE_MEDIAMTX_URL as string | undefined) ?? "http://localhost:8889";

// Which MediaMTX stream to show; stream names are listed in docker/mediamtx.yml
export const MEDIAMTX_STREAM = (import.meta.env.VITE_MEDIAMTX_STREAM as string | undefined) ?? "test";
