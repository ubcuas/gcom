const VITE_MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY;

if (!VITE_MAPTILER_KEY && window.navigator.onLine) {
    throw new Error(
        "VITE_MAPTILER_KEY environment variable is not set. " +
        "Please copy .env.example to .env and configure it with your MapTiler API key."
    );
}

export const MAPTILER_API_KEY = VITE_MAPTILER_KEY as string;
