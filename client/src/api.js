const MAX_SIDE = 640;

export async function downscaleImage(file) {
  if (!file.type.startsWith("image/")) {
    throw new Error("NOT_IMAGE");
  }
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  if (scale === 1 && file.type === "image/jpeg") {
    bitmap.close();
    return file;
  }
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext("2d");
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return await new Promise((resolve) =>
    canvas.toBlob(
      (blob) => resolve(new File([blob], "photo.jpg", { type: "image/jpeg" })),
      "image/jpeg",
      0.85
    )
  );
}

export async function analyzeImage(file, mode, signal) {
  const endpoint = mode === "act2" ? "/api/cells" : "/api/detect";
  const form = new FormData();
  form.append("upload", file);
  const response = await fetch(endpoint, { method: "POST", body: form, signal });
  if (!response.ok) {
    const detail = await errorMessage(response);
    throw new Error(detail);
  }
  return await response.json();
}

export async function streamNarration(detections, imageHash, onChunk, signal) {
  const response = await fetch("/api/narrate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ detections, image_hash: imageHash }),
    signal,
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value, { stream: true }));
  }
}

async function errorMessage(response) {
  try {
    const body = await response.json();
    return body.detail || `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}
