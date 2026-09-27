import AppBar from "@mui/material/AppBar";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import ScienceIcon from "@mui/icons-material/Science";
import { useEffect, useRef, useState } from "react";
import { analyzeImage, downscaleImage, streamNarration } from "./api.js";
import ResultsPanel from "./components/ResultsPanel.jsx";
import SubmissionPanel from "./components/SubmissionPanel.jsx";

export default function App() {
  const [mode, setMode] = useState("act1");
  const [samples, setSamples] = useState([]);
  const [imageUrl, setImageUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [narration, setNarration] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef(null);

  useEffect(() => {
    fetch("/samples/manifest.json")
      .then((r) => (r.ok ? r.json() : { act1: [], act2: [] }))
      .then((m) => setSamples(mode === "act2" ? m.act2 || [] : m.act1 || []))
      .catch(() => setSamples([]));
  }, [mode]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const analyze = async (file) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setError("");
    setNarration("");
    setResult(null);
    setImageUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(file);
    });
    setBusy(true);
    try {
      const uploadFile = await downscaleImage(file);
      const data = await analyzeImage(uploadFile, mode, controller.signal);
      setResult(data);
      let text = "";
      await streamNarration(
        data.detections,
        data.image_hash,
        (chunk) => {
          text += chunk;
          setNarration(text);
        },
        controller.signal
      );
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(
          err.message === "NOT_IMAGE"
            ? "That file is not an image. Please choose a JPEG or PNG photo."
            : err.message
        );
      }
    } finally {
      setBusy(false);
    }
  };

  const handleFile = async (fileOrPath) => {
    try {
      if (typeof fileOrPath === "string") {
        const response = await fetch(fileOrPath);
        analyze(await response.blob());
      } else {
        analyze(fileOrPath);
      }
    } catch {
      setError("Could not load that image.");
      setBusy(false);
    }
  };

  return (
    <Stack sx={{ minHeight: "100vh" }}>
      <AppBar position="static" color="transparent" elevation={0}>
        <Toolbar>
          <ScienceIcon sx={{ mr: 1.5, color: "primary.main" }} />
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            AI + Cell Manufacturing
          </Typography>
          <Typography variant="body2" color="text.secondary">
            live demo
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 5 } }}>
        <Stack spacing={1} alignItems="center" sx={{ textAlign: "center", mb: 3 }}>
          <Typography variant="h2" component="h1">
            Watch AI see.
          </Typography>
          <Typography variant="h6" color="text.secondary" fontWeight={400}>
            Upload a photo — or try one of ours — and watch the AI find what it was taught to look for.
          </Typography>
        </Stack>

        <SubmissionPanel
          mode={mode}
          onModeChange={setMode}
          samples={samples}
          onFile={handleFile}
          disabled={busy}
        />

        <ResultsPanel
          imageUrl={imageUrl}
          result={result}
          narration={narration}
          busy={busy}
          error={error}
          dashed={mode === "act2"}
        />
      </Container>
    </Stack>
  );
}
