import { useEffect, useRef } from "react";

const COLORS = ["#22d3ee", "#f472b6", "#a3e635", "#fbbf24", "#c084fc", "#fb7185"];

export default function DetectionOverlay({ imageUrl, detections, dashed = false }) {
  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    if (!canvas || !image || !imageUrl) return;

    const draw = () => {
      const width = image.clientWidth;
      const height = image.clientHeight;
      if (!width || !height) return;
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, width, height);
      ctx.lineWidth = 2.5;
      if (dashed) ctx.setLineDash([8, 5]);
      else ctx.setLineDash([]);
      ctx.font = "600 13px system-ui, sans-serif";
      (detections || []).forEach((d, i) => {
        const color = COLORS[i % COLORS.length];
        const [x1, y1, x2, y2] = d.bbox;
        const px = x1 * width;
        const py = y1 * height;
        const pw = (x2 - x1) * width;
        const ph = (y2 - y1) * height;
        ctx.strokeStyle = color;
        ctx.strokeRect(px, py, pw, ph);
        const label = `${d.label} ${Math.round(d.confidence * 100)}%`;
        const tw = ctx.measureText(label).width + 12;
        const th = 20;
        const ty = py - th < 0 ? py : py - th;
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.9;
        ctx.fillRect(px, ty, tw, th);
        ctx.globalAlpha = 1;
        ctx.fillStyle = "#0b1220";
        ctx.fillText(label, px + 6, ty + 14);
      });
    };

    if (image.complete) draw();
    else image.onload = draw;
    const observer = new ResizeObserver(draw);
    observer.observe(image);
    return () => observer.disconnect();
  }, [imageUrl, detections, dashed]);

  return (
    <div style={{ position: "relative", display: "inline-block", maxWidth: "100%" }}>
      <img
        ref={imageRef}
        src={imageUrl}
        alt="analyzed"
        style={{ display: "block", maxWidth: "100%", borderRadius: 8 }}
      />
      <canvas
        ref={canvasRef}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      />
    </div>
  );
}
