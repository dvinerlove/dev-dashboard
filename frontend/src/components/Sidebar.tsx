import {
  FolderGit2,
  ListVideo,
  Network,
  OctagonAlert,
  PanelLeftClose,
  Settings,
  PanelLeftOpen,
  Server,
} from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useRef } from "react";
import { useApp, type Section } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { useDash } from "../lib/store";
import { cn } from "../lib/utils";
import { Separator } from "./ui/separator";
import { Tip } from "./ui/tooltip";

/** app hexagon logo as a lucide-style icon: same 24 grid, strokeWidth
 *  passthrough — the line weight always matches the neighboring icons */
function HexIcon({
  size = 24,
  strokeWidth = 2,
  className,
}: {
  size?: number;
  strokeWidth?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M22 16.2V7.8a2 2 0 0 0-1-1.73l-8-4.55a2 2 0 0 0-2 0l-8 4.55A2 2 0 0 0 2 7.8v8.4a2 2 0 0 0 1 1.73l8 4.55a2 2 0 0 0 2 0l8-4.55a2 2 0 0 0 1-1.73z" />
      <circle cx="12" cy="8.6" r="1.6" fill="currentColor" stroke="none" />
      <circle cx="7.8" cy="14.3" r="1.6" fill="currentColor" stroke="none" />
      <circle cx="16.2" cy="14.3" r="1.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

const ITEMS: { id: Section; label: string; icon: typeof Server }[] = [
  // accepts the same props it is ever called with — size/strokeWidth/className
  { id: "overview", label: "SECTION_OVERVIEW", icon: HexIcon as typeof Server },
  { id: "infra", label: "SECTION_INFRA", icon: Server },
  { id: "projects", label: "SECTION_PROJECTS", icon: FolderGit2 },
  { id: "ports", label: "SECTION_PORTS", icon: Network },
  { id: "autorun", label: "SECTION_AUTORUN", icon: ListVideo },
  { id: "events", label: "SECTION_EVENTS", icon: OctagonAlert },
];

export function Sidebar({
  rail = false,
  canToggle = false,
  onToggle,
}: {
  rail?: boolean;
  canToggle?: boolean;
  onToggle?: () => void;
}) {
  const app = useApp();
  const t = useT();
  const st = useDash();
  const navRef = useRef<HTMLElement | null>(null);

  // insurance: after a mode switch the stuck inline drag width
  // is cleared — width control always returns to the class
  useEffect(() => {
    const t = setTimeout(() => {
      const n = navRef.current;
      if (n?.style.width) {
        n.style.width = "";
        n.style.transition = "";
      }
    }, 300);
    return () => clearTimeout(t);
  }, [rail]);

  // edge handle (resizable sidebar): during drag the width follows the cursor
  // live (transition off), on release — snap to the nearest mode with
  // animation; a click without movement — toggle
  const railDrag = (e: React.PointerEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const nav = el.parentElement as HTMLElement;
    const x0 = e.clientX;
    const w0 = nav.getBoundingClientRect().width;
    let w = w0;
    el.setPointerCapture(e.pointerId);
    nav.style.transition = "none";
    document.body.style.cursor = "ew-resize";
    document.body.style.userSelect = "none";
    const move = (ev: PointerEvent) => {
      w = Math.min(Math.max(w0 + ev.clientX - x0, 48), 320);
      nav.style.width = `${w}px`;
    };
    // release/cancel: inline width is cleared on the next frame — once the
    // mode class is already new; transition-[width] animates the snap itself.
    // lostpointercapture — insurance: if the capture is taken without pointerup,
    // pointerup lands on the element under the cursor, not us — without this
    // listener the inline width would stick forever (wide panel + rail icons).
    // finished makes done() idempotent.
    let finished = false;
    const done = (ev: PointerEvent | null) => {
      if (finished) return;
      finished = true;
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", cancel);
      el.removeEventListener("lostpointercapture", cancel);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      nav.style.transition = "";
      if (ev) {
        const dx = ev.clientX - x0;
        const wantRail = Math.abs(dx) < 4 ? !rail : w < 122;
        if (wantRail !== rail) onToggle?.();
      }
      requestAnimationFrame(() => {
        nav.style.width = "";
      });
    };
    const up = (ev: PointerEvent) => {
      // done() before release: lostpointercapture from releasing the capture
      // would otherwise eat the real pointerup and toggle would not fire
      done(ev);
      try {
        el.releasePointerCapture(e.pointerId);
      } catch {
        /* capture already released */
      }
    };
    const cancel = () => done(null);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", cancel);
    el.addEventListener("lostpointercapture", cancel);
  };

  const count = (id: Section): React.ReactNode => {
    if (!st) return null;
    switch (id) {
      case "infra":
        return `${st.infraUp}/${st.infraTotal}`;
      case "projects":
        return st.projects.length || "";
      case "autorun":
        return st.autorunMine.length + st.autorunOther.length || "";
      case "events": {
        const n = Math.max(st.issues, st.problems.length);
        if (!n) return "";
        const bad = st.problems.length > 0;
        return (
          <span
            className={cn(
              "tnum rounded px-1 text-[10px]",
              bad ? "bg-(--status-amber)/15 text-(--status-amber)" : "text-(--text-muted)",
            )}
          >
            {n}
          </span>
        );
      }
      default:
        return null;
    }
  };

  const navItem = (
    { id, label, icon: Icon }: { id: Section; label: string; icon: typeof Server },
    i: number,
  ) => {
    const active = app.section === id;
    const btn = (
      <button
        key={id}
        aria-current={active ? "page" : undefined}
        onClick={() => app.setSection(id)}
        className={cn(
          // px-2 + justify-start in all modes: icon center 23.5 ≈ rail center 24 —
          // the icon does not move on mode switch, only the label changes
          // only the label changes
          "relative flex h-8 w-full cursor-pointer items-center justify-start rounded-md px-2 text-[12.5px] transition-colors",
          active
            ? "text-(--text-primary)"
            : "text-(--text-secondary) hover:bg-(--bg-hover) hover:text-(--text-primary)",
        )}
      >
        {active && (
          <motion.span
            layoutId="nav-active"
            transition={{ type: "spring", stiffness: 500, damping: 38 }}
            className="absolute inset-0 rounded-md bg-(--bg-selected) transition-none"
          />
        )}
        <Icon
          size={15}
          strokeWidth={1.75}
          className={cn(
            "relative z-10 shrink-0",
            active && "text-(--accent)",
          )}
        />
        {/* the label collapses via width+opacity — driven by the container width,
            not the rail: appears mid-drag at the 122px threshold;
            on button-expand the stagger reads as a cascade */}
        <span
          style={{ transitionDelay: rail ? "0ms" : `${40 + i * 18}ms` }}
          className={cn(
            "relative z-10 ml-0 flex min-w-0 w-0 flex-none -translate-x-1 items-center overflow-hidden whitespace-nowrap opacity-0 transition-[flex-grow,opacity,transform,margin] duration-200 @min-[122px]:ml-2 @min-[122px]:flex-1 @min-[122px]:translate-x-0 @min-[122px]:opacity-100",
          )}
        >
          <span className="flex-1 truncate text-left">{t(label)}</span>
          <span
            className={cn(
              "font-mono text-[11px]",
              active ? "text-(--text-secondary)" : "text-(--text-muted)",
            )}
          >
            {count(id)}
          </span>
        </span>
      </button>
    );
    // Tip is always wrapped — the rail↔wide switch does not recreate the button,
    // otherwise the label mounts as a new node and the transition does not fire
    return (
      <Tip key={id} label={rail ? t(label) : null} side="right">
        {btn}
      </Tip>
    );
  };

  return (
    <nav
      ref={navRef}
      className={cn(
        // @container: labels/alignment follow the REAL nav width —
        // while dragging the edge they switch live at the 122px threshold,
        // without waiting for release and the rail switch
        "@container relative flex shrink-0 flex-col border-r border-(--border-hairline) bg-(--bg-base) p-2 transition-[width] duration-200 ease-out",
        rail ? "w-12" : "w-[196px]",
      )}
    >
      {ITEMS.map(navItem)}

      <div className="mt-auto">
        <Separator className="mb-2" />
        {navItem(
          { id: "settings", label: "SECTION_SETTINGS", icon: Settings },
          ITEMS.length,
        )}
        {canToggle && (
          <Tip
            label={rail ? t("EXPAND_PANEL") : t("COLLAPSE_PANEL")}
            side="right"
          >
            <button
              onClick={onToggle}
              aria-label={rail ? t("EXPAND_PANEL") : t("COLLAPSE_PANEL")}
              className={cn(
                "flex h-8 w-full cursor-pointer items-center justify-start rounded-md px-2 text-[12.5px] text-(--text-muted) transition-colors hover:bg-(--bg-hover) hover:text-(--text-primary)",
              )}
            >
              <PanelLeftOpen
                size={15}
                strokeWidth={1.75}
                className="shrink-0 @min-[122px]:hidden"
              />
              <PanelLeftClose
                size={15}
                strokeWidth={1.75}
                className="hidden shrink-0 @min-[122px]:block"
              />
              <span className="ml-0 min-w-0 w-0 flex-none overflow-hidden whitespace-nowrap opacity-0 transition-[flex-grow,opacity,transform,margin] duration-200 @min-[122px]:ml-2 @min-[122px]:flex-1 @min-[122px]:opacity-100">
                <span className="block truncate text-left">{t("COLLAPSE")}</span>
              </span>
            </button>
          </Tip>
        )}
      </div>
      {canToggle && (
        <div
          role="separator"
          aria-orientation="vertical"
          tabIndex={0}
          aria-label={rail ? t("EXPAND_PANEL") : t("COLLAPSE_PANEL")}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") onToggle?.();
          }}
          onPointerDown={railDrag}
          className="absolute inset-y-0 -right-[3px] z-20 w-1.5 cursor-ew-resize after:absolute after:inset-y-0 after:left-1/2 after:w-px after:-translate-x-1/2 after:bg-(--accent) after:opacity-0 after:transition-opacity hover:after:opacity-100"
        />
      )}
    </nav>
  );
}
