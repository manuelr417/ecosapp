import Alert from "@mui/material/Alert";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid";
import LinearProgress from "@mui/material/LinearProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import DetectionOverlay from "./DetectionOverlay.jsx";

const SOURCE_LABELS = {
  cached: "pre-computed result",
  local: "on-laptop AI",
  live: "hosted AI",
};

export default function ResultsPanel({ imageUrl, result, narration, busy, error, dashed }) {
  const imageCard = (
    <Card sx={{ minHeight: 320, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <CardContent sx={{ width: "100%", display: "flex", justifyContent: "center", py: 4 }}>
        {imageUrl ? (
          <DetectionOverlay imageUrl={imageUrl} detections={result?.detections || []} dashed={dashed} />
        ) : (
          <Typography variant="body1" color="text.secondary">
            Pick a sample or upload a photo to begin
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const infoCards = (
    <Stack spacing={2}>
      {result && (
        <Card>
          <CardContent>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <Typography variant="h6">Detections</Typography>
              <Chip size="small" label={SOURCE_LABELS[result.source] || result.source} variant="outlined" />
            </Stack>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {result.detections.length === 0 && (
                <Typography color="text.secondary">Nothing recognized</Typography>
              )}
              {result.detections.map((d, i) => (
                <Chip
                  key={i}
                  color="primary"
                  variant="outlined"
                  label={`${d.label} · ${Math.round(d.confidence * 100)}%`}
                />
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      {(narration || busy) && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>
              AI says…
            </Typography>
            <Typography variant="body1" sx={{ minHeight: 48, whiteSpace: "pre-wrap" }}>
              {narration || "…"}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Stack>
  );

  return (
    <Stack spacing={2} sx={{ width: "100%" }}>
      {error && <Alert severity="warning">{error}</Alert>}
      {busy && <LinearProgress />}
      <Grid container spacing={2} alignItems="flex-start">
        <Grid size={{ xs: 12, md: 7 }}>{imageCard}</Grid>
        <Grid size={{ xs: 12, md: 5 }}>{infoCards}</Grid>
      </Grid>
    </Stack>
  );
}
