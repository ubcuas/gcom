import { Box, Button } from "@mui/material";
import { useState } from "react";
import DebugPanel from "./DebugPanel";

// Flight commands (takeoff, RTL, ...) live on the Flight Commands page, which talks to ACMS.
export default function MPSControlSection() {
    const [debugPanelOpen, setDebugPanelOpen] = useState(false);

    return (
        <Box>
            <Button fullWidth variant="outlined" color="info" onClick={() => setDebugPanelOpen(true)}>
                Open Debug Panel
            </Button>
            <DebugPanel open={debugPanelOpen} onClose={() => setDebugPanelOpen(false)} />
        </Box>
    );
}
