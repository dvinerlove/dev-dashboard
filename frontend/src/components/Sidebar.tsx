import {
  FolderGit2,
  LayoutDashboard,
  ListVideo,
  Network,
  OctagonAlert,
  PanelLeftClose,
  Settings,
  PanelLeftOpen,
  Radar,
  Server,
  Skull,
} from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useRef } from "react";
import { useApp, type Section } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { useDash } from "../lib/store";
import { cn } from "../lib/utils";
import { Separator } from "./ui/separator";
import { Tip } from "./ui/tooltip";

const ITEMS: { id: Section; label: string; icon: typeof Server }[] = [
  { id: "overview", label: "SECTION_OVERVIEW", icon: LayoutDashboard },
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

  // страховка: после смены режима залипшая инлайн-ширина драга
  // снимается — управление шириной всегда возвращается классу
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

  // кромка-ручка (resizable-sidebar): во время драга ширина живо следует
  // за курсором (transition выключен), на отпускании — снап к ближайшему
  // режиму с анимацией; клик без движения — toggle
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
    // отпускание/отмена: инлайн-ширину снимаем на следующем кадре — когда
    // класс-режим уже новый; transition-[width] сам анимирует снап.
    // lostpointercapture — страховка: если захват отняли без pointerup,
    // pointerup придёт элементу под курсором, а не нам — без этого
    // слушателя инлайн-ширина залипала навсегда (широкая панель + иконки
    // рельса). finished делает done() идемпотентным.
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
      // done() раньше release: lostpointercapture от снятия захвата
      // иначе съест реальный pointerup и toggle не сработает
      done(ev);
      try {
        el.releasePointerCapture(e.pointerId);
      } catch {
        /* захват уже снят */
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
          // px-2 + justify-start во всех режимах: центр иконки 23.5 ≈
          // центру рельса 24 — иконка не двигается при смене режима,
          // меняется только лейбл
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
        {/* лейбл схлопывается шириной+opacity — по ширине контейнера,
            не по rail: появляется посреди драга на пороге 122px;
            при разворачивании кнопкой стаггер читается каскадом */}
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
    // Tip всегда в обёртке — смена rail↔wide не пересоздаёт кнопку,
    // иначе лейбл маунтится новым узлом и transition не срабатывает
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
        // @container: лейблы/выравнивание следуют РЕАЛЬНОЙ ширине nav —
        // во время драга кромки они переключаются живьём на пороге 122px,
        // не дожидаясь отпускания и смены rail
        "@container relative flex shrink-0 flex-col border-r border-(--border-hairline) bg-(--bg-base) p-2 transition-[width] duration-200 ease-out",
        rail ? "w-12" : "w-[196px]",
      )}
    >
      {ITEMS.map(navItem)}

      <div className="mt-auto">
        <Separator className="mb-2" />
        <Tip label={rail ? t("SCAN_PROJECTS") : null} side="right">
          <button
            onClick={app.scan}
            className={cn(
              "flex h-8 w-full cursor-pointer items-center justify-start rounded-md px-2 text-[12.5px] text-(--text-secondary) transition-colors hover:bg-(--bg-hover) hover:text-(--text-primary)",
            )}
          >
            <Radar size={15} strokeWidth={1.75} className="shrink-0" />
            <span className="min-w-0 w-0 flex-none overflow-hidden whitespace-nowrap opacity-0 transition-[flex-grow,opacity,transform,margin] duration-200 @min-[122px]:ml-2 @min-[122px]:flex-1 @min-[122px]:opacity-100">
              <span className="block truncate text-left">
                {t("SCAN_PROJECTS")}
              </span>
            </span>
          </button>
        </Tip>
        <Tip label={t("KILL_PORT_HOLDER")} side="right">
          <button
            onClick={() => app.openDlg({ t: "killport" })}
            className={cn(
              "flex h-8 w-full cursor-pointer items-center justify-start rounded-md px-2 text-[12.5px] text-(--text-secondary) transition-colors hover:bg-(--status-red)/10 hover:text-(--status-red)",
            )}
          >
            <Skull size={15} strokeWidth={1.75} className="shrink-0" />
            <span className="min-w-0 w-0 flex-none overflow-hidden whitespace-nowrap opacity-0 transition-[flex-grow,opacity,transform,margin] duration-200 @min-[122px]:ml-2 @min-[122px]:flex-1 @min-[122px]:opacity-100">
              <span className="block truncate text-left">{t("KILL_PORT")}</span>
            </span>
          </button>
        </Tip>
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
