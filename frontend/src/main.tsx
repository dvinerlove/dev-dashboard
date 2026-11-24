import { createRoot } from "react-dom/client";
import { MotionConfig } from "motion/react";
import App from "./App";
import { startPolling } from "./lib/store";
import "./index.css";

startPolling(2000);
createRoot(document.getElementById("root")!).render(
  // reducedMotion="user" — JS-анимации (layoutId/spring) чтят
  // prefers-reduced-motion так же, как CSS-блок в index.css
  <MotionConfig reducedMotion="user">
    <App />
  </MotionConfig>,
);
