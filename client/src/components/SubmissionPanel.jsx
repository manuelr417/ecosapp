import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import ImageList from "@mui/material/ImageList";
import ImageListItem from "@mui/material/ImageListItem";
import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import UploadIcon from "@mui/icons-material/Upload";
import ScienceIcon from "@mui/icons-material/Science";
import PhotoCameraIcon from "@mui/icons-material/PhotoCamera";
import { useRef } from "react";

export default function SubmissionPanel({ mode, onModeChange, samples, onFile, disabled }) {
  const inputRef = useRef(null);

  const handlePick = (event) => {
    const file = event.target.files?.[0];
    if (file) onFile(file);
    event.target.value = "";
  };

  return (
    <Stack spacing={2} alignItems="center" sx={{ width: "100%", py: 2 }}>
      <ToggleButtonGroup
        value={mode}
        exclusive
        onChange={(_, value) => value && onModeChange(value)}
        size="large"
      >
        <ToggleButton value="act1" startIcon={<PhotoCameraIcon />}>
          Everyday objects
        </ToggleButton>
        <ToggleButton value="act2" startIcon={<ScienceIcon />}>
          Cell clusters
        </ToggleButton>
      </ToggleButtonGroup>

      <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" justifyContent="center">
        <Button
          variant="contained"
          size="large"
          startIcon={<UploadIcon />}
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
        >
          Upload a photo
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/*"
          hidden
          onChange={handlePick}
        />
        {samples.length > 0 && (
          <Chip label="or try a sample" variant="outlined" sx={{ color: "text.secondary" }} />
        )}
      </Stack>

      {samples.length > 0 && (
        <ImageList sx={{ maxWidth: 560, mb: 0 }} cols={samples.length} rowHeight={92} gap={12}>
          {samples.map((sample) => (
            <ImageListItem
              key={sample.id}
              sx={{
                cursor: disabled ? "default" : "pointer",
                opacity: disabled ? 0.5 : 1,
                borderRadius: 2,
                overflow: "hidden",
                border: "2px solid transparent",
                "&:hover": { borderColor: "primary.main" },
              }}
              onClick={() => !disabled && onFile(sample.file)}
            >
              <img src={sample.file} alt={sample.id} loading="lazy" style={{ height: 92, objectFit: "cover" }} />
            </ImageListItem>
          ))}
        </ImageList>
      )}
    </Stack>
  );
}
