import { Box, Typography } from "@mui/material";
import { selectPreferredTheme } from "../../store/slices/appSlice";
import { useAppSelector } from "../../store/store";
import Widget from "../Widget";

export default function PositionSection({
    latitude,
    longitude,
    altitude,
    relativeAltitude,
    heading,
}: {
    latitude: number;
    longitude: number;
    altitude: number;
    relativeAltitude?: number;
    heading: number;
}) {
    return (
        <Box>
            <Typography
                sx={{
                    mb: 1,
                }}
                variant="h5"
            >
                Position
            </Typography>
            <Box
                sx={{
                    display: "grid",
                    gap: 1,
                    gridTemplateColumns: "1fr 1fr",
                }}
            >
                <Widget text="Longitude" data={longitude} />
                <Widget text="Latitude" data={latitude} />
                <Widget text="Altitude from Sea Level" data={`${altitude.toFixed(2)} m`} />
                <Widget
                    text="Altitude from Ground"
                    data={relativeAltitude !== undefined ? `${relativeAltitude.toFixed(2)} m` : "N/A"}
                />
                <Widget
                    sx={{
                        gridColumn: "span 2",
                    }}
                    text="Heading"
                    data={<>{heading}&deg;</>}
                    aside={<Compass heading={heading} />}
                />
            </Box>
        </Box>
    );
}

function Compass({ heading }: { heading: number }) {
    const compassColor = useAppSelector(selectPreferredTheme) === "dark" ? "white" : "#aaa";

    return (
        <svg
            style={{
                height: "64px",
            }}
            viewBox="0 0 140 140"
            transform={`rotate(${-heading} 0 0)`}
        >
            <polygon points="60,70 70,20 80,70" fill="#2DA0DC" />
            <text x="70" y="15" textAnchor="middle" fill="#2DA0DC">
                N
            </text>
            <polygon points="60,70 70,120 80,70" fill={compassColor} />
        </svg>
    );
}
