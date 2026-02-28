import React, { useEffect, useRef } from "react";

export type Detection = {
  image_data: any | null;
  color_detection: string;
  bounding_box: [number[], number[]];
  confidence_level: number;
};

export default function AnnotationCanvas({
  imageRef,
  detections,
}: {
  imageRef: React.RefObject<HTMLImageElement>;
  detections: Detection[];
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    function fitCanvas() {
      const img = imageRef.current;
      const c = canvasRef.current;
      if (!img || !c) return;
      c.width = img.clientWidth;
      c.height = img.clientHeight;
      render();
    }
    const obs = new ResizeObserver(fitCanvas);
    if (imageRef.current) obs.observe(imageRef.current);
    window.addEventListener("resize", fitCanvas);
    fitCanvas();
    return () => {
      obs.disconnect();
      window.removeEventListener("resize", fitCanvas);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [imageRef]);

  function render() {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext("2d")!;
    ctx.clearRect(0, 0, c.width, c.height);
  }

  useEffect(render, []);

  return (
    <canvas
      ref={canvasRef}
      className="annotation-canvas"
      style={{ position: "absolute", left: 0, top: 0, pointerEvents: "none" }}
    />
  );
}
