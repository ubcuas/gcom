import { useAppSelector } from "../store/store";
import { selectAircraftStatus } from "../store/slices/dataSlice";
import PositionSection from "./DroneStatus/PositionSection";
import SpeedSection from "./DroneStatus/SpeedSection";
import TimeStamp from "./DroneStatus/TimeStamp";
import MPSControlSection from "./DroneStatus/MPSControlSection";
import { Paper } from "@mui/material";

export default function DroneStatusCard() {
    const droneState = useAppSelector(selectAircraftStatus);

    return (
        <Paper
            sx={{
                p: 2,
                display: "flex",
                flexDirection: "column",
                gap: 4,
            }}
        >
            <PositionSection
                latitude={droneState.latitude}
                longitude={droneState.longitude}
                altitude={droneState.altitude}
                heading={droneState.heading}
            />
            <SpeedSection speed={droneState.speed} verticalSpeed={droneState.verticalSpeed} />
            <TimeStamp time={droneState.timestamp} />
            <MPSControlSection />
        </Paper>
    );
}
