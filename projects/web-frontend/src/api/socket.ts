import { io } from "socket.io-client";

export const socket = io("http://localhost:8000", {
    autoConnect: true,
});

socket.on("connect_error", (error) => {
    console.log("Socket connection error", error);
});
