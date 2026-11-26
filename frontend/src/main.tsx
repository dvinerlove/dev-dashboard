import { createRoot } from "react-dom/client";
import { MotionConfig } from "motion/react";
import App from "./App";
import { startPolling } from "./lib/store";
import "./index.css";

startPolling(2000);
createRoot(document.getElementById("root")!).render(
  // reducedMotion="user" — JS animations (layoutId/spring) honor
  // prefers-reduced-motion the same way as the CSS block in index.css
  <MotionConfig reducedMotion="user">
    <App />
  </MotionConfig>,
);
