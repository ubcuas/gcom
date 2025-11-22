import { Box, Stack } from "@mui/material";
import { RouteSelector } from "../components/RouteSelector";
import WaypointStatusCard from "../components/WaypointStatusCard";

export default function Queue() {
    return (
        <Box
            sx={{
                p: 8,
                width: "100%",
            }}
        >
            <Stack spacing={3}>
                <RouteSelector />
                <WaypointStatusCard />
            </Stack>
        </Box>
    );
}
