import { Box, Typography } from "@mui/material";
import Widget from "../Widget";

const getFlightModeColor = (mode: string) => {
    switch (mode) {
        case "AUTO":
            return "success.main";
        case "GUIDED":
            return "info.main";
        case "RTL":
            return "warning.main";
        case "STABILIZE":
            return "secondary.main";
        default:
            return "grey.500";
    }
};

const getArmedColor = (armed: boolean) => {
    return armed ? "error.main" : "success.main";
};

type StatusIndicatorsProps = {
    flightMode: string;
    armed: boolean;
    voltage: number;
};

export default function StatusIndicators({ flightMode, armed, voltage }: StatusIndicatorsProps) {
    return (
        <Box>
            <Typography
                sx={{
                    mb: 1,
                }}
                variant="h5"
            >
                Status
            </Typography>
            <Box
                sx={{
                    display: "flex",
                    gap: 1,
                }}
            >
                <Widget
                    text="Flight Mode"
                    data={
                        <Typography
                            variant="h6"
                            sx={{
                                color: getFlightModeColor(flightMode),
                                fontWeight: "bold",
                            }}
                        >
                            {flightMode}
                        </Typography>
                    }
                />
                <Widget
                    text="Armed Status"
                    data={
                        <Typography
                            variant="h6"
                            sx={{
                                color: getArmedColor(armed),
                                fontWeight: "bold",
                            }}
                        >
                            {armed ? "ARMED" : "DISARMED"}
                        </Typography>
                    }
                />
            </Box>
            <Typography
                variant="body2"
                color="text.secondary"
                sx={{
                    mt: 1,
                }}
            >
                Battery: {voltage}V
            </Typography>
        </Box>
    );
}
