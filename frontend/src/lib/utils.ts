import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** pywebview window control (custom frame). In a browser — quiet no-op. */
export function winCtl(
  m: "window_minimize" | "window_toggle_maximize" | "window_close"
     | "window_drag_start",
) {
  return () =>
    (
      window as unknown as {
        pywebview?: { api?: Record<string, () => void> };
      }
    ).pywebview?.api?.[m]?.();
}
