import { SerializedError } from "@reduxjs/toolkit";
import { AxiosError } from "axios";

export type ApiErrorResponse = {
    message: string;
    status?: number;
    statusText?: string;
    data?: unknown;
};

export const extractAxiosError = (error: unknown): ApiErrorResponse => {
    if (error instanceof AxiosError) {
        const axiosError = error as AxiosError;

        // Log the full error for debugging
        console.error("Axios error:", {
            message: axiosError.message,
            status: axiosError.response?.status,
            statusText: axiosError.response?.statusText,
            data: axiosError.response?.data,
            config: {
                url: axiosError.config?.url,
                method: axiosError.config?.method,
            },
        });

        // Extract serializable error information
        const errorData = axiosError.response?.data as { detail?: string; message?: string } | undefined;
        const message = errorData?.detail || errorData?.message || axiosError.message || "An unknown error occurred";

        return {
            message,
            status: axiosError.response?.status,
            statusText: axiosError.response?.statusText,
            data: axiosError.response?.data,
        };
    }

    // Handle non-axios errors
    if (error instanceof Error) {
        console.error("Error:", error);
        return {
            message: error.message,
        };
    }

    // Fallback for unknown error types
    console.error("Unknown error:", error);
    return {
        message: "An unknown error occurred",
    };
};

export const createErrorMessage = (error: unknown): string => {
    // Handle ApiErrorResponse or SerializedError
    if (error && typeof error === "object" && "message" in error && typeof error.message === "string") {
        return error.message;
    }

    // Handle standard Error objects
    if (error instanceof Error) {
        return error.message;
    }

    return "An unknown error occurred";
};
