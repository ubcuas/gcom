import { Typography, Box } from "@mui/material";
import Widget from "../Widget";

export default function BatterySection({ voltage }: { voltage: number }) {
    return (
        <Box>
            <Typography
                sx={{
                    mb: 1,
                }}
                variant="h5"
            >
                Battery
            </Typography>
            <Box
                sx={{
                    display: "flex",
                    gap: 1,
                }}
            >
                <Widget text="Voltage" data={`${voltage}V`} />
            </Box>
        </Box>
    );
}
