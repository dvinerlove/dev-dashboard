import { useT } from "../lib/i18n";
import { useDash } from "../lib/store";
import { AttentionList, SectionTitle } from "./bits";
import { ProjectsGrid } from "./ProjectCards";
import { ServiceList } from "./ServiceRows";

export function OverviewView() {
  const t = useT();
  const st = useDash();
  if (!st) return null;

  const up = [...st.services, ...st.remotes].filter((r) => r.state === "up");

  const stats = [
    { k: t("SECTION_INFRA"), v: `${st.infraUp}/${st.infraTotal}` },
    {
      k: t("SECTION_PROJECTS"),
      v: `${st.projects.filter((p) => p.state === "up").length}/${st.projects.length}`,
    },
    { k: "RAM", v: `${st.memMb} MB` },
    { k: t("SECTION_EVENTS"), v: String(st.issues) },
  ];

  return (
    <div className="space-y-6">
      {/* stat strip */}
      <div className="flex divide-x divide-(--border-hairline) overflow-hidden rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40">
        {stats.map((s) => (
          <div key={s.k} className="min-w-0 flex-1 px-4 py-3">
            <div className="text-[10px] uppercase tracking-[0.08em] text-(--text-muted)">
              {s.k}
            </div>
            <div className="tnum mt-1 font-mono text-[16px] font-medium text-(--text-primary)">
              {s.v}
            </div>
          </div>
        ))}
      </div>

      {/* needs attention */}
      <div>
        <SectionTitle>{t("NEEDS_ATTENTION")}</SectionTitle>
        <AttentionList st={st} />
      </div>

      {/* projects — live cards with quick actions */}
      {!!st.projects.length && (
        <div>
          <SectionTitle>{t("SECTION_PROJECTS")}</SectionTitle>
          <ProjectsGrid rows={st.projects} />
        </div>
      )}

      {/* running now */}
      <div>
        <SectionTitle>{t("RUNNING_SECTION")}</SectionTitle>
        {up.length ? (
          <ServiceList rows={up} />
        ) : (
          <div className="rounded-lg border border-(--border-hairline) bg-(--bg-surface)/40 px-3.5 py-4 text-[12.5px] text-(--text-muted)">
            {t("NOTHING_RUNNING")}
          </div>
        )}
      </div>
    </div>
  );
}
