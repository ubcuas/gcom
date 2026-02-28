import { Box, Paper, TextField, Typography } from "@mui/material";
import React, { useRef, useState } from "react";
import AnnotationCanvas, { Detection } from "../components/AnnotationCanvas";
import LeftSidebar from "../components/LeftSidebar";
import "../styles/task1.css";

interface ImageData {
  id: string;
  src: string;
  colorLabel: string;
  detections: Detection[];
  textInput: string;
  isFlagged: boolean;
}



// Helper to generate test images
function generateTestImage(color: string): string {
  const c = document.createElement("canvas");
  c.width = 640;
  c.height = 360;
  const ctx = c.getContext("2d")!;
  ctx.fillStyle = "#222";
  ctx.fillRect(0, 0, c.width, c.height);
  ctx.fillStyle = color;
  ctx.fillRect(80 + Math.random() * 200, 60 + Math.random() * 120, 100, 80);
  return c.toDataURL("image/png");
}

export default function Task1Page() {
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [imageTabs, setImageTabs] = useState<ImageData[]>([
    {
      id: "tab-0",
      src: generateTestImage("#0a84ff"),
      colorLabel: "Blue",
      detections: [
        {
          image_data: null,
          color_detection: "Blue",
          bounding_box: [[150, 120], [250, 200]],
          confidence_level: 85,
        },
      ],
      textInput: "",
      isFlagged: false,
    },
    {
      id: "tab-1",
      src: generateTestImage("#ff4444"),
      colorLabel: "Red",
      detections: [
        {
          image_data: null,
          color_detection: "Red",
          bounding_box: [[100, 100], [220, 220]],
          confidence_level: 92,
        },
      ],
      textInput: "",
      isFlagged: false,
    },
    {
      id: "tab-2",
      src: generateTestImage("#44ff44"),
      colorLabel: "Green",
      detections: [
        {
          image_data: null,
          color_detection: "Green",
          bounding_box: [[180, 140], [280, 240]],
          confidence_level: 78,
        },
      ],
      textInput: "",
      isFlagged: false,
    },
  ]);
  const [currentTabIndex, setCurrentTabIndex] = useState(0);

  const currentTab = imageTabs[currentTabIndex];

  function onTabChange(newValue: number) {
    setCurrentTabIndex(newValue);
  }

  function updateTextInput(text: string) {
    setImageTabs((tabs) =>
      tabs.map((tab, idx) => (idx === currentTabIndex ? { ...tab, textInput: text } : tab))
    );
  }

  function onFlag() {
    setImageTabs((tabs) =>
      tabs.map((tab, idx) =>
        idx === currentTabIndex ? { ...tab, isFlagged: !tab.isFlagged } : tab
      )
    );
  }

  function onExport() {
    const exportData = {
      images: imageTabs.map((tab) => ({
        id: tab.id,
        colorLabel: tab.colorLabel,
        textInput: tab.textInput,
        isFlagged: tab.isFlagged,
      })),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `task1_export_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Box sx={{ display: "flex", height: "100vh", width: "100%" }}>
      <LeftSidebar
        imageTabs={imageTabs}
        currentTabIndex={currentTabIndex}
        onFlag={onFlag}
        onExport={onExport}
        onSelectImage={onTabChange}
      />

      <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {/* Image display area */}
        <Box
          sx={{
            position: "relative",
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#222",
          }}
        >
          <img
            ref={imageRef}
            src={currentTab.src}
            alt="stream"
            style={{ maxWidth: "90%", maxHeight: "80%", border: "1px solid #333", backgroundColor: "black" }}
          />
          <AnnotationCanvas imageRef={imageRef} detections={currentTab.detections} />
        </Box>

        {/* Metadata and text input */}
        <Paper
          sx={{
            padding: 2,
            borderRadius: 0,
            display: "flex",
            flexDirection: "column",
            gap: 2,
            borderTop: "1px solid",
            borderTopColor: "divider",
          }}
          elevation={0}
        >
          <Box>
            <Typography variant="caption" sx={{ display: "block", marginBottom: 0.5, fontWeight: 600 }}>
              Text Input
            </Typography>
            <TextField
              placeholder="free text (auto-saved per tab)"
              value={currentTab.textInput}
              onChange={(e) => updateTextInput(e.target.value)}
              fullWidth
              size="small"
              variant="outlined"
            />
          </Box>
          <Box>
            <Typography variant="caption" sx={{ display: "block", marginBottom: 0.5, fontWeight: 600 }}>
              Metadata (detections JSON)
            </Typography>
            <TextField
              value={JSON.stringify(currentTab.detections, null, 2)}
              fullWidth
              multiline
              rows={4}
              InputProps={{ readOnly: true }}
              variant="outlined"
              size="small"
              sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}
            />
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}
