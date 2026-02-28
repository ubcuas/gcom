import { ExpandLess, ExpandMore } from "@mui/icons-material";
import { Box, Button, Collapse, List, ListItem, ListItemButton, ListItemText, Paper, Typography } from "@mui/material";
import React, { useState } from "react";
import { Detection } from "./AnnotationCanvas";

interface ImageData {
  id: string;
  src: string;
  colorLabel: string;
  detections: Detection[];
  textInput: string;
  isFlagged: boolean;
}

export default function LeftSidebar({
  imageTabs,
  currentTabIndex,
  onFlag,
  onExport,
  onSelectImage,
}: {
  imageTabs: ImageData[];
  currentTabIndex: number;
  onFlag: () => void;
  onExport: () => void;
  onSelectImage: (index: number) => void;
}) {
  const [openColorState, setOpenColorState] = useState<Record<string, boolean>>({});

  const toggleColor = (color: string) => {
    setOpenColorState((prev) => ({
      ...prev,
      [color]: !prev[color],
    }));
  };

  return (
    <Paper
      sx={{
        width: 280,
        padding: 2,
        borderRadius: 0,
        overflow: "auto",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
      elevation={0}
    >
      <Typography variant="h6" sx={{ fontWeight: 600 }}>
        Flags
      </Typography>

      <Box sx={{ display: "flex", gap: 1 }}>
        <Button
          variant="contained"
          onClick={onFlag}
          fullWidth
          size="small"
          sx={{ opacity: imageTabs[currentTabIndex]?.isFlagged ? 0.5 : 1 }}
        >
          Flag
        </Button>
        <Button variant="outlined" onClick={onExport} fullWidth size="small">
          Export
        </Button>
      </Box>

      {/* Colors with nested images */}
      <Box sx={{ borderTop: "1px solid", borderTopColor: "divider", paddingTop: 1 }}>
        {imageTabs.length === 0 && (
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            No images
          </Typography>
        )}

        {imageTabs.map((tab, idx) => (
          <Box key={tab.id}>
            <ListItemButton
              onClick={() => toggleColor(tab.colorLabel)}
              sx={{
                paddingLeft: "12px",
                paddingY: "8px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, flex: 1 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: "2px",
                    backgroundColor: tab.colorLabel.toLowerCase(),
                    border: "1px solid rgba(0,0,0,0.15)",
                  }}
                />
                <Typography variant="body2">{tab.colorLabel}</Typography>
              </Box>
              <Box sx={{ display: "flex", alignItems: "center" }}>
                {openColorState[tab.colorLabel] ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
              </Box>
            </ListItemButton>

            <Collapse in={openColorState[tab.colorLabel]} timeout="auto" unmountOnExit>
              <List sx={{ padding: 0 }}>
                <ListItemButton
                  selected={idx === currentTabIndex}
                  onClick={() => onSelectImage(idx)}
                  sx={{
                    paddingLeft: 4,
                    paddingY: 0.75,
                    fontSize: "0.875rem",
                  }}
                >
                  <ListItemText
                    primary={tab.colorLabel}
                    primaryTypographyProps={{ variant: "caption" }}
                  />
                </ListItemButton>
              </List>
            </Collapse>
          </Box>
        ))}
      </Box>


    </Paper>
  );
}
