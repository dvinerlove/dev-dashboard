import { createContext, useContext } from "react";
import type { ThemeId } from "./theme";
import type {
  PortConflict,
  ProjectSpec,
  ScannedProject,
  ServiceSpec,
} from "./api";

export type Section = "overview" | "infra" | "projects" | "ports" | "autorun" | "events" | "settings";

export const SECTION_TITLES: Record<Section, string> = {
  overview: "SECTION_OVERVIEW",
  infra: "SECTION_INFRA",
  projects: "SECTION_PROJECTS",
  ports: "SECTION_PORTS",
  autorun: "SECTION_AUTORUN",
  events: "SECTION_EVENTS",
  settings: "SECTION_SETTINGS",
};
export type SelKind = "svc" | "prj";
export interface Sel {
  kind: SelKind;
  name: string;
  remote?: boolean;
}

export type Dlg =
  | { t: "confirm"; title: string; body: string; action: string; danger?: boolean; run: () => void }
  | { t: "service"; spec: ServiceSpec | null }
  | { t: "project"; spec: ProjectSpec | null }
  | { t: "killport" }
  | { t: "autorun"; name: string; cmd: string }
  | { t: "token"; name: string }
  | { t: "scan"; items: ScannedProject[] }
  | { t: "portconflict"; name: string; c: PortConflict & { port: number; pid: number; pname: string } }
  | { t: "onboarding" }
  | null;

export interface AppApi {
  theme: ThemeId;
  setTheme: (t: ThemeId) => void;
  section: Section;
  setSection: (s: Section) => void;
  sel: Sel | null;
  select: (s: Sel | null) => void;
  inspector: boolean;
  setInspector: (v: boolean) => void;
  inspectorTab: string;
  setInspectorTab: (t: string) => void;
  palette: boolean;
  setPalette: (v: boolean) => void;
  railAuto: boolean;
  setRailAuto: (v: boolean) => void;
  openDlg: (d: Dlg) => void;
  closeDlg: () => void;
  // действия из старого Main.qml
  svcToggle: (name: string, remote?: boolean) => void;
  svcRestart: (name: string) => void;
  prjToggle: (name: string) => void;
  chip: (kind: "svc" | "remote" | "prj", name: string) => void;
  startAll: () => void;
  stopAll: () => void;
  scan: () => void;
  killPortFlow: (port: number) => void;
  deleteService: (name: string) => void;
  deleteProject: (name: string, running: boolean) => void;
  editService: (name: string) => void;
  editProject: (name: string) => void;
  editAutorun: (name: string, cmd: string, mine: boolean) => void;
  deleteAutorun: (name: string) => void;
  showRuns: (name: string, kind: SelKind) => void;
  confirm: (
    title: string,
    body: string,
    action: string,
    run: () => void,
    danger?: boolean,
  ) => void;
  toast: (msg: string) => void;
}

export const AppCtx = createContext<AppApi>(null as unknown as AppApi);
export const useApp = () => useContext(AppCtx);
