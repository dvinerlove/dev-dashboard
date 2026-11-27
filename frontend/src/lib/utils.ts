import type React from "react";
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

/** Keyboard activation for clickable row divs: Enter/Space fire the
    click handler, focusable via Tab. Spread next to onClick. */
export function rowKeys(fn: ((e: React.MouseEvent) => void) | undefined) {
  if (!fn) return {};
  return {
    role: "button" as const,
    tabIndex: 0,
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        fn(e as unknown as React.MouseEvent);
      }
    },
  };
}
