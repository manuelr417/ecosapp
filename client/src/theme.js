import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#22d3ee" },
    secondary: { main: "#f472b6" },
    background: { default: "#0b1220", paper: "#111a2e" },
  },
  typography: {
    h2: { fontWeight: 800 },
    h5: { fontWeight: 700 },
  },
  shape: { borderRadius: 12 },
});

export default theme;
