import { useAppSelector } from "../store/store";
import { selectAircraftStatus } from "../store/slices/dataSlice";
import PositionSection from "./DroneStatus/PositionSection";
import SpeedSection from "./DroneStatus/SpeedSection";
import TimeStamp from "./DroneStatus/TimeStamp";
import MPSControlSection from "./DroneStatus/MPSControlSection";
import StatusIndicators from "./DroneStatus/StatusIndicators";
import { AircraftStatus } from "../types/AircraftStatus";
import { Paper } from "@mui/material";

const roundValues = (
    data: Omit<AircraftStatus, "verticalSpeed" | "speed" | "voltage" | "armed"> & {
        vertical_velocity: number;
        velocity: number;
        battery_voltage: number;
        armed: boolean;
    },
) => {
    return {
        timestamp: Math.round(data.timestamp),
        latitude: Math.round(data.latitude * 1000000) / 1000000,
        longitude: Math.round(data.longitude * 1000000) / 1000000,
        altitude: Math.round(data.altitude),
        verticalSpeed: Math.round(data.vertical_velocity * 100) / 100,
        speed: Math.round(data.velocity * 100) / 100,
        heading: Math.round(data.heading),
        voltage: Math.round((data.battery_voltage / 1000) * 100) / 100,
        armed: data.armed,
        flightmode: data.flightmode,
    } satisfies AircraftStatus;
};

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
            <StatusIndicators
                flightMode={droneState.flightmode || "UNKNOWN"}
                armed={droneState.armed}
                voltage={droneState.voltage}
            />
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
