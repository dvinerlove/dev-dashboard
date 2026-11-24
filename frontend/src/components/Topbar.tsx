import { useEffect, useRef, useState } from "react";
import {
  Activity,
  Minus,
  PanelRight,
  Play,
  Plus,
  Search,
  Square,
  X,
} from "lucide-react";
import { SECTION_TITLES, useApp } from "../lib/ctx";
import { useT } from "../lib/i18n";
import { useDash } from "../lib/store";
import { cn, winCtl } from "../lib/utils";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown";
import { Tip } from "./ui/tooltip";

/** mousedown дальше не идёт — иначе кнопки внутри шапки
 *  тоже начинали бы перетаскивание окна */
const noDrag = (e: React.MouseEvent) => e.stopPropagation();

/** ЛКМ на шапке → нативный move-loop Windows (один вызов, без лагов
 *  .pywebview-drag-region). detail>1 — это даблклик → maximize, не drag. */
const startDrag = (e: React.MouseEvent) => {
  if (e.button === 0 && e.detail < 2) winCtl("window_drag_start")();
};

/** Даблклик по шапке → maximize, но не сквозь кнопки: dblclick
 *  всплывает, без гейта даблклик по любой кнопке разворачивал окно */
const dblMax = (e: React.MouseEvent) => {
  if (!(e.target as HTMLElement).closest("button, a, input, [role=button]")) {
    winCtl("window_toggle_maximize")();
  }
};

export function Topbar() {
  const app = useApp();
  const t = useT();
  const st = useDash();
  const issues = st?.issues ?? 0;
  const problems = st?.problems.length ?? 0;
  const bad = problems > 0;

  // поиск строго по центру окна: absolute + измеренная ширина свободного
  // места между крайними блоками (ResizeObserver ловит и ресайз, и
  // схлопывания заголовка/статуса) → центр точный, налезть не может,
  // а transition-[width] превращает смену ширины в плавный дрейф
  const leftRef = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLButtonElement>(null);
  const [free, setFree] = useState(600);
  useEffect(() => {
    const lastF = { cur: 9999 };
    const measure = () => {
      const l = leftRef.current?.getBoundingClientRect();
      const r = rightRef.current?.getBoundingClientRect();
      const btn = searchRef.current;
      if (!l || !r || !btn) return;
      const hdrLeft = l.left - 12;             // px-3
      const cx = (l.left + r.right) / 2;
      const half = Math.min(r.left - cx, cx - l.right);
      const f = Math.max(0, half * 2 - 16);
      const w = Math.min(340, f);
      const wEff = f < 92 ? Math.min(32, f) : w;
      // кнопка хочет центр, но уходит в свободный зазор, если соседи
      // пересекают его во время своих схлопываний — наезжать нельзя
      const lo = l.right + 8;
      const hi = r.left - 8 - wEff;
      const x = Math.min(Math.max(cx - wEff / 2, lo), Math.max(hi, lo));
      const hide = wEff < 40;
      // сжатие/эвакуация — мгновенно (transition дал бы наезд на кадры);
      // расширение и возврат к центру — плавно
      btn.style.transitionProperty = f < lastF.cur ? "none" : "";
      lastF.cur = f;
      btn.style.width = `${wEff}px`;
      btn.style.left = `${x - hdrLeft}px`;
      btn.style.opacity = hide ? "0" : "1";
      btn.style.pointerEvents = hide ? "none" : "";
      setFree(f);
    };
    // RO на блоках ловит контентные изменения (схлопывания, бейджи);
    // при ресайзе окна размеры те же — позиции сдвигаются, нужен resize
    const ro = new ResizeObserver(measure);
    for (const e of [leftRef.current, rightRef.current]) {
      if (e) ro.observe(e);
    }
    window.addEventListener("resize", measure);
    measure();
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);
  const searchW = Math.min(340, free);
  // три режима: пилл с текстом / пилл с kbd / голая иконка (крайний случай)
  const mode = searchW >= 190 ? "full" : searchW >= 92 ? "kbd" : "icon";
  const effW = mode === "icon" ? 32 : searchW;

  return (
    <header
      onMouseDown={startDrag}
      onDoubleClick={dblMax}
      className={cn(
        "relative flex h-10 shrink-0 items-center gap-3 border-b border-(--border-hairline) bg-(--bg-base) px-3 select-none",
      )}
    >
      <div
        ref={leftRef}
        className="flex items-center gap-2 whitespace-nowrap"
      >
        <Activity size={15} strokeWidth={1.75} className="text-(--accent)" />
        {/* заголовок схлопывается плавно (max-w→0 + компенсация gap) —
            иначе display:none дёргало бы поиск мгновенно */}
        <div className="flex max-w-[260px] items-center gap-2 overflow-hidden whitespace-nowrap opacity-100 transition-[max-width,opacity,margin] max-[1150px]:-mr-2 max-[1150px]:max-w-0 max-[1150px]:opacity-0">
          <h1 className="text-[13px] text-(--text-muted)">Dev Dashboard</h1>
          <span className="text-[13px] text-(--text-muted)">/</span>
        </div>
        <span className="text-[13px] font-medium text-(--text-primary)">
          {t(SECTION_TITLES[app.section])}
        </span>
      </div>

      {/* поиск → Command Palette: строго по центру, ширина = свободное
          место (измерено), при тесноте сворачивается в иконку */}
      <button
        ref={searchRef}
        onClick={() => app.setPalette(true)}
        onMouseDown={noDrag}
        aria-label={t("SEARCH_CTRL_K")}
        style={{ width: effW }}
        className={cn(
          "absolute top-1/2 left-0 flex h-7 min-w-0 -translate-y-1/2 cursor-pointer items-center gap-2 overflow-hidden rounded-md border border-(--border-hairline) bg-(--bg-surface) px-2.5 text-[12px] text-(--text-muted) transition-[width,left,opacity,color,background-color,border-color] hover:border-(--border-strong)",
          mode !== "full" && "justify-center",
        )}
      >
        <Search size={14} strokeWidth={1.75} className="shrink-0" />
        {mode === "full" && (
          <span className="flex-1 truncate text-left">
            {t("SEARCH_PLACEHOLDER_SHORT")}
          </span>
        )}
        {mode !== "icon" && <kbd className="kbd">Ctrl+K</kbd>}
      </button>

      <div
        ref={rightRef}
        onMouseDown={noDrag}
        className="ml-auto flex items-center gap-1.5"
      >
        {/* живой статус */}
        <button
          onClick={() => app.setSection("events")}
          className="flex h-7 shrink-0 cursor-pointer items-center gap-1.5 whitespace-nowrap rounded-md border border-(--border-hairline) bg-(--bg-surface) px-2.5 text-[12px] text-(--text-secondary) transition-colors hover:border-(--border-strong)"
        >
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              bad ? "bg-(--status-amber)" : "bg-(--status-green)",
            )}
          />
          <span className="max-w-[170px] overflow-hidden font-mono text-[11.5px] whitespace-nowrap opacity-100 transition-[max-width,opacity,margin] max-[1400px]:-mr-1.5 max-[1400px]:max-w-0 max-[1400px]:opacity-0">
            {st ? t("STATUS_SUMMARY", { u: st.infraUp, n: st.infraTotal, mb: st.memMb }) : "…"}
          </span>
          {(issues > 0 || bad) && (
            <span
              className={cn(
                "tnum rounded px-1 font-mono text-[10px]",
                bad ? "bg-(--status-amber)/15 text-(--status-amber)" : "bg-(--bg-hover) text-(--text-secondary)",
              )}
            >
              {Math.max(issues, problems)}
            </span>
          )}
        </button>

        <Tip label={t("START_ALL")}>
          <Button variant="ghost" size="icon" onClick={app.startAll}>
            <Play size={15} strokeWidth={1.75} />
          </Button>
        </Tip>
        <Tip label={t("STOP_ALL")}>
          <Button variant="ghost" size="icon" onClick={app.stopAll}>
            <Square size={15} strokeWidth={1.75} />
          </Button>
        </Tip>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="secondary"
              size="sm"
              className="h-7"
              aria-label={t("ADD")}
            >
              <Plus size={14} strokeWidth={1.75} />
              <span className="max-w-[80px] overflow-hidden whitespace-nowrap transition-[max-width,opacity,margin] max-[1150px]:-mr-1.5 max-[1150px]:max-w-0 max-[1150px]:opacity-0">
                {t("ADD")}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={() => app.openDlg({ t: "service", spec: null })}>
              {t("NEW_SERVICE")}
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => app.openDlg({ t: "project", spec: null })}>
              {t("NEW_PROJECT")}
            </DropdownMenuItem>
            <DropdownMenuItem
              onSelect={() => app.openDlg({ t: "autorun", name: "", cmd: "" })}
            >
              {t("NEW_AUTORUN_ENTRY")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Tip label={t("INSPECTOR_CTRL_I")}>
          <Button
            variant="ghost"
            size="icon"
            className={cn(app.inspector && "text-(--accent)")}
            onClick={() => app.setInspector(!app.inspector)}
          >
            <PanelRight size={15} strokeWidth={1.75} />
          </Button>
        </Tip>

        {/* кнопки окна: — □ × (× = в трей). Только Windows-кастомная
            рамка: на macOS нативный chrome, в веб-режиме — браузер */}
        {st?.platform === "windows" && (
          <>
            <div className="mx-1 h-4 w-px bg-(--border-strong)" />
            <button
              aria-label={t("COLLAPSE")}
              onClick={winCtl("window_minimize")}
              className="flex h-7 w-8 cursor-pointer items-center justify-center rounded-md text-(--text-muted) transition-colors hover:bg-(--bg-hover) hover:text-(--text-primary)"
            >
              <Minus size={14} strokeWidth={1.75} />
            </button>
            <button
              aria-label={t("MAXIMIZE_RESTORE")}
              onClick={winCtl("window_toggle_maximize")}
              className="flex h-7 w-8 cursor-pointer items-center justify-center rounded-md text-(--text-muted) transition-colors hover:bg-(--bg-hover) hover:text-(--text-primary)"
            >
              <Square size={11} strokeWidth={1.75} />
            </button>
            <button
              aria-label={t("MINIMIZE_TO_TRAY")}
              onClick={winCtl("window_close")}
              className="flex h-7 w-8 cursor-pointer items-center justify-center rounded-md text-(--text-muted) transition-colors hover:bg-(--status-red) hover:text-white"
            >
              <X size={14} strokeWidth={1.75} />
            </button>
          </>
        )}
      </div>
    </header>
  );
}
