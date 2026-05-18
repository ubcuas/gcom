import axios from "axios";

export const api = axios.create({
    baseURL: "https://vittals-macbook-air.tail8164f3.ts.net/api",
    headers: {
        "Content-Type": "application/json",
    },
});

export default api;
