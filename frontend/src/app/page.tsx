"use client";

import { useState, useEffect, useCallback } from "react";
import {
  generateLeads,
  getGenerationStatus,
  getProjects,
  getProjectLeads,
  getStats,
  exportLeads,
  type Lead,
  type Project,
  type Stats,
} from "@/lib/api";

/* ═══════════════════════════════════════════
   SCORE BADGE
═══════════════════════════════════════════ */
function ScoreBadge({ grade, score }: { grade: string; score: number }) {
  const cls =
    grade === "Hot" ? "badge-hot" : grade === "Warm" ? "badge-warm" : "badge-cold";
  const icon = grade === "Hot" ? "🔥" : grade === "Warm" ? "⚡" : "❄️";
  return (
    <span className={`badge ${cls}`}>
      {icon} {grade} · {score}
    </span>
  );
}

/* ═══════════════════════════════════════════
   STAT CARD
═══════════════════════════════════════════ */
function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string | number;
  icon: string;
  accent: string;
}) {
  return (
    <div className="glass-card fade-in" style={{ padding: "20px 22px" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 14,
        }}
      >
        <span style={{ fontSize: 22 }}>{icon}</span>
        <span
          style={{
            fontSize: 10,
            fontWeight: 600,
            padding: "3px 8px",
            borderRadius: 6,
            background: `${accent}12`,
            color: accent,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          {label}
        </span>
      </div>
      <div style={{ fontSize: 28, fontWeight: 800, color: accent, lineHeight: 1 }}>
        {value}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   LEAD CARD
═══════════════════════════════════════════ */
function LeadCard({ lead, onClick }: { lead: Lead; onClick: () => void }) {
  return (
    <div
      className="glass-card glass-card-interactive fade-in"
      onClick={onClick}
      style={{ padding: "20px 22px" }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 10,
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3
            className="truncate"
            style={{
              fontSize: 15,
              fontWeight: 650,
              color: "var(--text-primary)",
              marginBottom: 2,
            }}
          >
            {lead.company_name || "Unknown Company"}
          </h3>
          <a
            href={lead.website}
            target="_blank"
            rel="noopener noreferrer"
            className="truncate"
            style={{
              display: "block",
              fontSize: 12,
              color: "var(--accent-light)",
              opacity: 0.8,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {lead.website?.replace(/https?:\/\/(www\.)?/, "").slice(0, 45)}
          </a>
        </div>
        <ScoreBadge grade={lead.grade} score={lead.score} />
      </div>

      <p
        className="line-clamp-2"
        style={{
          fontSize: 13,
          color: "var(--text-secondary)",
          marginBottom: 12,
          lineHeight: 1.55,
        }}
      >
        {lead.insights || "No insights available for this lead."}
      </p>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {lead.email && (
          <span
            className="signal-chip"
            style={{ background: "var(--bg-secondary)", color: "var(--text-secondary)" }}
          >
            📧 {lead.email.length > 28 ? lead.email.slice(0, 28) + "…" : lead.email}
          </span>
        )}
        {lead.has_hiring_page && (
          <span
            className="signal-chip"
            style={{ background: "var(--success-bg)", color: "var(--success)" }}
          >
            👥 Hiring
          </span>
        )}
        {lead.has_pricing_page && (
          <span
            className="signal-chip"
            style={{ background: "var(--warm-bg)", color: "var(--warm)" }}
          >
            💰 Pricing
          </span>
        )}
        {Array.isArray(lead.tech_stack) && lead.tech_stack.length > 0 && (
          <span
            className="signal-chip"
            style={{ background: "var(--accent-glow)", color: "var(--accent-light)" }}
          >
            ⚙️ {lead.tech_stack.slice(0, 2).join(", ")}
          </span>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   LEAD DETAIL MODAL
═══════════════════════════════════════════ */
function LeadDetailModal({ lead, onClose }: { lead: Lead; onClose: () => void }) {
  const scoreColor =
    lead.grade === "Hot"
      ? "var(--hot)"
      : lead.grade === "Warm"
        ? "var(--warm)"
        : "var(--cold)";
  const scoreBg =
    lead.grade === "Hot"
      ? "var(--hot-bg)"
      : lead.grade === "Warm"
        ? "var(--warm-bg)"
        : "var(--cold-bg)";

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
        background: "rgba(0,0,0,0.75)",
        backdropFilter: "blur(10px)",
      }}
      onClick={onClose}
    >
      <div
        className="glass-card fade-in"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "100%",
          maxWidth: 640,
          maxHeight: "85vh",
          overflowY: "auto",
          padding: 32,
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            marginBottom: 24,
          }}
        >
          <div>
            <h2
              className="gradient-text"
              style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}
            >
              {lead.company_name}
            </h2>
            <a
              href={lead.website}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 13, color: "var(--accent-light)" }}
            >
              {lead.website}
            </a>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted)",
              fontSize: 20,
              cursor: "pointer",
              padding: 4,
            }}
          >
            ✕
          </button>
        </div>

        {/* Score */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginBottom: 24,
            padding: 16,
            borderRadius: 12,
            background: "var(--bg-secondary)",
          }}
        >
          <div
            className="score-ring"
            style={{ background: scoreBg, color: scoreColor }}
          >
            {lead.score}
          </div>
          <div>
            <ScoreBadge grade={lead.grade} score={lead.score} />
            <p
              style={{
                fontSize: 11,
                color: "var(--text-muted)",
                marginTop: 4,
              }}
            >
              Lead Quality Score
            </p>
          </div>
        </div>

        {/* Insights */}
        <Section title="AI Insights">
          <p
            style={{
              fontSize: 13,
              color: "var(--text-primary)",
              lineHeight: 1.65,
              padding: "14px 16px",
              borderRadius: 10,
              background: "var(--bg-secondary)",
              borderLeft: "3px solid var(--accent)",
            }}
          >
            {lead.insights || "No insights generated."}
          </p>
        </Section>

        {/* Contact */}
        <Section title="Contact">
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 10,
            }}
          >
            {lead.email && (
              <ContactItem icon="📧">
                <a href={`mailto:${lead.email}`} style={{ color: "var(--accent-light)" }}>
                  {lead.email}
                </a>
              </ContactItem>
            )}
            {lead.phone && (
              <ContactItem icon="📞">
                <span>{lead.phone}</span>
              </ContactItem>
            )}
            {lead.linkedin && (
              <ContactItem icon="🔗">
                <a
                  href={lead.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: "var(--accent-light)" }}
                >
                  LinkedIn Profile
                </a>
              </ContactItem>
            )}
          </div>
        </Section>

        {/* Signals */}
        <Section title="Signals">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {lead.has_hiring_page && <SignalTag color="var(--success)" bg="var(--success-bg)" icon="👥" text="Hiring Page" />}
            {lead.has_pricing_page && <SignalTag color="var(--warm)" bg="var(--warm-bg)" icon="💰" text="Pricing Page" />}
            {lead.has_blog && <SignalTag color="var(--cold)" bg="var(--cold-bg)" icon="📝" text="Blog" />}
            {lead.blog_updated_recently && <SignalTag color="var(--success)" bg="var(--success-bg)" icon="✅" text="Blog Fresh" />}
            {lead.email && <SignalTag color="var(--accent-light)" bg="var(--accent-glow)" icon="📧" text="Email Found" />}
          </div>
        </Section>

        {/* Tech Stack */}
        {Array.isArray(lead.tech_stack) && lead.tech_stack.length > 0 && (
          <Section title="Tech Stack">
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {lead.tech_stack.map((tech) => (
                <span
                  key={tech}
                  style={{
                    fontSize: 12,
                    fontWeight: 500,
                    padding: "5px 12px",
                    borderRadius: 8,
                    background: "var(--accent-glow)",
                    color: "var(--accent-light)",
                  }}
                >
                  {tech}
                </span>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 22 }}>
      <h3
        style={{
          fontSize: 11,
          fontWeight: 700,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          marginBottom: 10,
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}

function ContactItem({ icon, children }: { icon: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "10px 14px",
        borderRadius: 9,
        background: "var(--bg-secondary)",
        fontSize: 13,
      }}
    >
      <span>{icon}</span>
      {children}
    </div>
  );
}

function SignalTag({
  color,
  bg,
  icon,
  text,
}: {
  color: string;
  bg: string;
  icon: string;
  text: string;
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        fontSize: 12,
        fontWeight: 500,
        padding: "5px 12px",
        borderRadius: 8,
        background: bg,
        color: color,
      }}
    >
      {icon} {text}
    </span>
  );
}

/* ═══════════════════════════════════════════
   GENERATE FORM
═══════════════════════════════════════════ */
function GenerateForm({
  onStart,
  isGenerating,
}: {
  onStart: (keyword: string, country: string, maxResults: number) => void;
  isGenerating: boolean;
}) {
  const [keyword, setKeyword] = useState("");
  const [country, setCountry] = useState("India");
  const [maxResults, setMaxResults] = useState(10);

  return (
    <div className="glass-card fade-in" style={{ padding: 24, marginBottom: 28 }}>
      <h2
        className="gradient-text"
        style={{ fontSize: 17, fontWeight: 700, marginBottom: 18 }}
      >
        🚀 Generate Leads
      </h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr 100px",
          gap: 14,
          alignItems: "end",
        }}
      >
        <div>
          <label
            style={{
              display: "block",
              fontSize: 11,
              color: "var(--text-muted)",
              marginBottom: 6,
              fontWeight: 500,
            }}
          >
            Industry Keyword
          </label>
          <input
            type="text"
            className="input-field"
            placeholder='e.g. "SaaS companies", "IT services"'
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && keyword.trim() && !isGenerating)
                onStart(keyword, country, maxResults);
            }}
          />
        </div>
        <div>
          <label
            style={{
              display: "block",
              fontSize: 11,
              color: "var(--text-muted)",
              marginBottom: 6,
              fontWeight: 500,
            }}
          >
            Country
          </label>
          <select
            className="input-field"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          >
            <option value="India">🇮🇳 India</option>
            <option value="US">🇺🇸 United States</option>
            <option value="UK">🇬🇧 United Kingdom</option>
            <option value="Canada">🇨🇦 Canada</option>
            <option value="Australia">🇦🇺 Australia</option>
            <option value="Germany">🇩🇪 Germany</option>
            <option value="Singapore">🇸🇬 Singapore</option>
            <option value="UAE">🇦🇪 UAE</option>
          </select>
        </div>
        <div>
          <label
            style={{
              display: "block",
              fontSize: 11,
              color: "var(--text-muted)",
              marginBottom: 6,
              fontWeight: 500,
            }}
          >
            Max Results
          </label>
          <input
            type="number"
            className="input-field"
            min={1}
            max={50}
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
          />
        </div>
      </div>

      <button
        className="btn-primary"
        disabled={!keyword.trim() || isGenerating}
        onClick={() => onStart(keyword, country, maxResults)}
        style={{ marginTop: 18 }}
      >
        {isGenerating ? (
          <>
            <span className="spinner" />
            Generating...
          </>
        ) : (
          "⚡ Find & Score Leads"
        )}
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════
   PROCESSING STATUS
═══════════════════════════════════════════ */
function ProcessingStatus({ status }: { status: any }) {
  if (!status) return null;

  return (
    <div
      className="glass-card pulse-glow fade-in"
      style={{ padding: 22, marginBottom: 24 }}
    >
      <div
        style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}
      >
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: "var(--accent)",
            boxShadow: "0 0 8px var(--accent)",
          }}
        />
        <span
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: "var(--accent-light)",
          }}
        >
          Pipeline Running
        </span>
      </div>
      <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
        {status.progress || "Processing..."}
      </p>
      {(status.total_found > 0 || status.total_enriched > 0) && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 10,
            marginTop: 14,
          }}
        >
          <MiniStat label="Found" value={status.total_found || 0} />
          <MiniStat label="Enriched" value={status.total_enriched || 0} />
          <MiniStat label="Scored" value={status.total_scored || 0} />
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: 10,
        borderRadius: 10,
        background: "var(--bg-secondary)",
      }}
    >
      <div
        style={{
          fontSize: 20,
          fontWeight: 800,
          color: "var(--text-primary)",
          lineHeight: 1,
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: 10,
          color: "var(--text-muted)",
          marginTop: 4,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        {label}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════
   MAIN DASHBOARD
═══════════════════════════════════════════ */
export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"generate" | "projects">("generate");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<any>(null);
  const [gradeFilter, setGradeFilter] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    loadProjects();
  }, []);

  const loadStats = async () => {
    try {
      const s = await getStats();
      setStats(s);
    } catch {
      /* no data yet */
    }
  };

  const loadProjects = async () => {
    try {
      const { projects: p } = await getProjects();
      setProjects(p);
    } catch {
      /* first load */
    }
  };

  const loadLeads = useCallback(
    async (projectId: string) => {
      try {
        const { leads: l } = await getProjectLeads(projectId, gradeFilter || undefined);
        setLeads(l);
        setSelectedProject(projectId);
      } catch (e: any) {
        setError(e.message);
      }
    },
    [gradeFilter]
  );

  const pollStatus = useCallback(
    (projectId: string) => {
      const interval = setInterval(async () => {
        try {
          const status = await getGenerationStatus(projectId);
          setPipelineStatus(status);
          if (status.status === "completed" || status.status === "failed") {
            clearInterval(interval);
            setIsGenerating(false);
            if (status.status === "completed") {
              loadLeads(projectId);
              loadProjects();
              loadStats();
            } else {
              setError(status.error || "Pipeline failed");
            }
          }
        } catch {
          clearInterval(interval);
          setIsGenerating(false);
        }
      }, 3000);
    },
    [loadLeads]
  );

  const handleGenerate = async (
    keyword: string,
    country: string,
    maxResults: number
  ) => {
    setError(null);
    setIsGenerating(true);
    setLeads([]);
    setSelectedProject(null);
    setPipelineStatus({ status: "processing", progress: "Starting pipeline..." });

    try {
      const result = await generateLeads({ keyword, country, max_results: maxResults });
      pollStatus(result.project_id);
    } catch (e: any) {
      setError(e.message);
      setIsGenerating(false);
      setPipelineStatus(null);
    }
  };

  const handleExport = async (projectId: string) => {
    try {
      await exportLeads(projectId);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (selectedProject) loadLeads(selectedProject);
  }, [gradeFilter, selectedProject, loadLeads]);

  const hotCount = leads.filter((l) => l.grade === "Hot").length;
  const warmCount = leads.filter((l) => l.grade === "Warm").length;
  const coldCount = leads.filter((l) => l.grade === "Cold").length;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)" }}>
      {/* ═══ HEADER ═══ */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 40,
          background: "rgba(6, 6, 11, 0.85)",
          backdropFilter: "blur(16px)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div
          style={{
            maxWidth: 1200,
            margin: "0 auto",
            padding: "14px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 24 }}>🧬</span>
            <h1
              className="gradient-text"
              style={{ fontSize: 19, fontWeight: 800, letterSpacing: "-0.01em" }}
            >
              LeadTwin AI
            </h1>
          </div>

          <nav style={{ display: "flex", gap: 4 }}>
            {(["generate", "projects"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  if (tab === "projects") loadProjects();
                }}
                style={{
                  padding: "8px 16px",
                  borderRadius: 9,
                  fontSize: 13,
                  fontWeight: 500,
                  border: "none",
                  cursor: "pointer",
                  transition: "all 0.2s",
                  background:
                    activeTab === tab ? "var(--accent)" : "transparent",
                  color:
                    activeTab === tab ? "#fff" : "var(--text-secondary)",
                }}
              >
                {tab === "generate" ? "⚡ Generate" : "📁 Projects"}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* ═══ MAIN ═══ */}
      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "28px 24px" }}>
        {/* Error */}
        {error && (
          <div
            className="fade-in"
            style={{
              marginBottom: 20,
              padding: "12px 16px",
              borderRadius: 10,
              background: "rgba(244,63,94,0.08)",
              border: "1px solid rgba(244,63,94,0.2)",
              color: "var(--hot)",
              fontSize: 13,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span>⚠️ {error}</span>
            <button
              onClick={() => setError(null)}
              style={{
                background: "none",
                border: "none",
                color: "inherit",
                cursor: "pointer",
                fontSize: 16,
              }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Stats */}
        {stats && stats.total_leads > 0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(5, 1fr)",
              gap: 14,
              marginBottom: 28,
            }}
          >
            <StatCard label="Projects" value={stats.total_projects} icon="📁" accent="#818cf8" />
            <StatCard label="Total Leads" value={stats.total_leads} icon="👥" accent="#a78bfa" />
            <StatCard label="Hot" value={stats.hot_leads} icon="🔥" accent="#f43f5e" />
            <StatCard label="Warm" value={stats.warm_leads} icon="⚡" accent="#f59e0b" />
            <StatCard label="Avg Score" value={stats.avg_score} icon="📊" accent="#10b981" />
          </div>
        )}

        {/* Tab: Generate */}
        {activeTab === "generate" && (
          <>
            <GenerateForm onStart={handleGenerate} isGenerating={isGenerating} />
            {isGenerating && <ProcessingStatus status={pipelineStatus} />}
          </>
        )}

        {/* Tab: Projects */}
        {activeTab === "projects" && (
          <div style={{ marginBottom: 28 }}>
            <h2
              style={{
                fontSize: 17,
                fontWeight: 700,
                color: "var(--text-primary)",
                marginBottom: 16,
              }}
            >
              Your Projects
            </h2>
            {projects.length === 0 ? (
              <div
                className="glass-card fade-in"
                style={{ padding: "56px 24px", textAlign: "center" }}
              >
                <span style={{ fontSize: 40, display: "block", marginBottom: 12 }}>
                  📭
                </span>
                <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
                  No projects yet. Generate your first leads!
                </p>
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3, 1fr)",
                  gap: 14,
                }}
              >
                {projects.map((project) => (
                  <div
                    key={project.id}
                    className="glass-card glass-card-interactive fade-in"
                    onClick={() => {
                      setSelectedProject(project.id);
                      loadLeads(project.id);
                    }}
                    style={{ padding: "18px 20px" }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        marginBottom: 8,
                      }}
                    >
                      <h3
                        className="truncate"
                        style={{
                          fontSize: 14,
                          fontWeight: 600,
                          color: "var(--text-primary)",
                        }}
                      >
                        {project.name}
                      </h3>
                      <StatusDot status={project.status} />
                    </div>
                    <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      🔍 {project.keyword} · 🌍 {project.country}
                    </p>
                    <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                      {project.total_leads} leads ·{" "}
                      {new Date(project.created_at || "").toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Leads Section */}
        {(selectedProject || leads.length > 0) && (
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 18,
                flexWrap: "wrap",
                gap: 12,
              }}
            >
              <h2 style={{ fontSize: 17, fontWeight: 700 }}>
                🎯 Leads ({leads.length})
              </h2>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                {/* Filters */}
                <div
                  style={{
                    display: "flex",
                    gap: 2,
                    padding: 3,
                    borderRadius: 10,
                    background: "var(--bg-secondary)",
                  }}
                >
                  {[
                    { label: "All", value: "" },
                    { label: "🔥 Hot", value: "Hot" },
                    { label: "⚡ Warm", value: "Warm" },
                    { label: "❄️ Cold", value: "Cold" },
                  ].map((f) => (
                    <button
                      key={f.value}
                      onClick={() => setGradeFilter(f.value)}
                      style={{
                        padding: "6px 12px",
                        borderRadius: 8,
                        fontSize: 12,
                        fontWeight: 500,
                        border: "none",
                        cursor: "pointer",
                        transition: "all 0.2s",
                        background:
                          gradeFilter === f.value ? "var(--accent)" : "transparent",
                        color:
                          gradeFilter === f.value ? "#fff" : "var(--text-muted)",
                      }}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>

                {selectedProject && leads.length > 0 && (
                  <button
                    className="btn-ghost"
                    onClick={() => handleExport(selectedProject)}
                  >
                    📥 Export CSV
                  </button>
                )}
              </div>
            </div>

            {leads.length === 0 ? (
              <div
                className="glass-card fade-in"
                style={{ padding: "48px 24px", textAlign: "center" }}
              >
                <span style={{ fontSize: 36, display: "block", marginBottom: 10 }}>
                  🔍
                </span>
                <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
                  No leads found with current filters.
                </p>
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, 1fr)",
                  gap: 14,
                }}
              >
                {leads.map((lead, i) => (
                  <LeadCard
                    key={lead.id || i}
                    lead={lead}
                    onClick={() => setSelectedLead(lead)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!selectedProject &&
          leads.length === 0 &&
          !isGenerating &&
          activeTab === "generate" && (
            <div className="fade-in" style={{ textAlign: "center", padding: "60px 0" }}>
              <span style={{ fontSize: 56, display: "block", marginBottom: 20 }}>
                🧬
              </span>
              <h2
                className="gradient-text"
                style={{ fontSize: 26, fontWeight: 800, marginBottom: 10 }}
              >
                AI-Powered Lead Intelligence
              </h2>
              <p
                style={{
                  color: "var(--text-secondary)",
                  maxWidth: 420,
                  margin: "0 auto",
                  fontSize: 14,
                  lineHeight: 1.7,
                }}
              >
                Enter an industry keyword above to discover, enrich, and score potential
                B2B leads automatically.
              </p>
            </div>
          )}
      </main>

      {/* Lead Detail Modal */}
      {selectedLead && (
        <LeadDetailModal lead={selectedLead} onClose={() => setSelectedLead(null)} />
      )}
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, { bg: string; color: string }> = {
    completed: { bg: "var(--success-bg)", color: "var(--success)" },
    processing: { bg: "var(--warm-bg)", color: "var(--warm)" },
    failed: { bg: "var(--hot-bg)", color: "var(--hot)" },
    pending: { bg: "rgba(85,85,106,0.15)", color: "var(--text-muted)" },
  };
  const c = colors[status] || colors.pending;
  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 600,
        padding: "3px 9px",
        borderRadius: 999,
        background: c.bg,
        color: c.color,
        textTransform: "capitalize",
      }}
    >
      {status}
    </span>
  );
}
