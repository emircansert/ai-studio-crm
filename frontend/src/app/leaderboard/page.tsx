"use client";

import { ChevronDown, ChevronRight, Medal, Sparkles, Trophy } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { PageHeader } from "@/components/ui/PageHeader";
import { Select } from "@/components/ui/Input";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import type { ChampionLeaderboardResponse, ChampionLeaderboardRow, ChampionScoreRule, LeaderboardResponse, LeaderboardRow } from "@/types/api";

type Period = "all_time" | "last_30_days" | "last_7_days";
type Metric = "points" | "organizations" | "notes" | "contacts" | "opportunities";
type Tab = "champion" | "activity" | "rules";

const CATEGORY_KEYS = [
  "VISION_STRATEGY",
  "ECOSYSTEM_LIBRARY",
  "STARTUP_SCOUTING",
  "COMMUNICATION_CASE_STUDY",
  "COMMUNICATION_EVENT",
  "TRAINING"
];

const CATEGORY_LABELS: Record<string, string> = {
  VISION_STRATEGY: "Use Case & Project Development",
  ECOSYSTEM_LIBRARY: "Ecosystem Library Contribution",
  STARTUP_SCOUTING: "Startup Scouting & AI Studio Support",
  COMMUNICATION_CASE_STUDY: "Case Study Contribution",
  COMMUNICATION_EVENT: "Events & Communication Participation",
  TRAINING: "Training Completion"
};

export default function LeaderboardPage() {
  const [tab, setTab] = useState<Tab>("champion");
  const [period, setPeriod] = useState<Period>("all_time");
  const [metric, setMetric] = useState<Metric>("points");
  const [champion, setChampion] = useState<ChampionLeaderboardResponse | null>(null);
  const [championMe, setChampionMe] = useState<ChampionLeaderboardRow | null>(null);
  const [activity, setActivity] = useState<LeaderboardResponse | null>(null);
  const [activityMe, setActivityMe] = useState<LeaderboardRow | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedUserId, setExpandedUserId] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    setError(null);
    if (tab === "champion" || tab === "rules") {
      Promise.all([
        apiRequest<ChampionLeaderboardResponse>(`/api/v1/leaderboard/champion?period=${period}&limit=50`),
        apiRequest<ChampionLeaderboardRow>(`/api/v1/leaderboard/champion/me?period=${period}`)
      ])
        .then(([leaderboardData, myData]) => {
          setChampion(leaderboardData);
          setChampionMe(myData);
        })
        .catch((caught) => setError(caught))
        .finally(() => setIsLoading(false));
      return;
    }
    Promise.all([
      apiRequest<LeaderboardResponse>(`/api/v1/leaderboard?period=${period}&metric=${metric}&limit=50`),
      apiRequest<LeaderboardRow>(`/api/v1/leaderboard/me?period=${period}&metric=${metric}`)
    ])
      .then(([leaderboardData, myData]) => {
        setActivity(leaderboardData);
        setActivityMe(myData);
      })
      .catch((caught) => setError(caught))
      .finally(() => setIsLoading(false));
  }, [period, metric, tab]);

  const topThree = useMemo(() => champion?.items.slice(0, 3) ?? [], [champion]);
  const rules = champion?.scorecard ?? fallbackRules;

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="YZ Champion Program"
        title="Leaderboard"
        description="YZ Champion Score is calculated only from the six weighted program categories in the slide. CRM Activity Points remain preserved as the operational evidence log behind qualifying CRM actions."
      />

      <div className="command-hero">
        <div>
          <h2>YZ Champion Score</h2>
          <p>
            CRM Activity Points are operational CRM contribution logs. In the YZ Champion Program, qualifying CRM actions
            such as adding startups, events, tools, contacts, and decks are counted under Ecosystem Library Contribution
            according to the program target thresholds.
          </p>
        </div>
        <div className="button-row">
          <button className={`button ${tab === "champion" ? "button--primary" : "button--secondary"}`} onClick={() => setTab("champion")} type="button">
            YZ Champion Score
          </button>
          <button className={`button ${tab === "activity" ? "button--primary" : "button--secondary"}`} onClick={() => setTab("activity")} type="button">
            CRM Activity Points
          </button>
          <button className={`button ${tab === "rules" ? "button--primary" : "button--secondary"}`} onClick={() => setTab("rules")} type="button">
            Score Rules
          </button>
        </div>
      </div>

      {error ? <ErrorState title="Could not load leaderboard" error={error} /> : null}

      {tab === "champion" ? (
        <>
          <div className="section-toolbar">
            <Select aria-label="Champion leaderboard period" value={period} onChange={(event) => setPeriod(event.target.value as Period)}>
              <option value="all_time">All time</option>
              <option value="last_30_days">Last 30 days</option>
              <option value="last_7_days">Last 7 days</option>
            </Select>
            <Badge tone="info">Excel imports excluded</Badge>
          </div>

          <div className="leaderboard-top-grid">
            {topThree.map((row, index) => (
              <section className={`leader-card leader-card--${index + 1}`} key={row.user_id}>
                <div className="rank">{index === 0 ? <Trophy size={20} /> : <Medal size={20} />}#{row.rank}</div>
                <h2>{row.full_name}</h2>
                <p>{row.email}</p>
                <strong>{row.champion_score}/100</strong>
                <div className="chip-row">
                  <Badge>{row.weighted_breakdown?.VISION_STRATEGY?.category_score ?? 0} Use Case</Badge>
                  <Badge tone="success">{row.ecosystem_library_raw_count ?? row.raw_counts?.ECOSYSTEM_LIBRARY ?? 0} Ecosystem evidence</Badge>
                </div>
              </section>
            ))}
          </div>

          <SectionCard>
            <div className="section-heading section-heading--inline">
              <div>
                <h2>YZ Champion ranking</h2>
                <p>{isLoading ? "Loading..." : `${champion?.total_users ?? 0} ranked users`}</p>
              </div>
              <Badge tone="success">Official weighted score</Badge>
            </div>
            {champion?.items.length ? (
              <Table
                rows={champion.items}
                getRowKey={(row) => row.user_id}
                columns={[
                  {
                    key: "rank",
                    header: "Rank",
                    render: (row) => (
                      <button className="icon-button" type="button" onClick={() => setExpandedUserId(expandedUserId === row.user_id ? null : row.user_id)}>
                        {expandedUserId === row.user_id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}#{row.rank}
                      </button>
                    )
                  },
                  {
                    key: "user",
                    header: "User",
                    render: (row) => (
                      <div className="record-title">
                        <strong>{row.full_name}</strong>
                        <span className="record-subtitle">{row.email}</span>
                        {expandedUserId === row.user_id ? <ExpandedScore row={row} /> : null}
                      </div>
                    )
                  },
                  { key: "score", header: "YZ Champion Score", render: (row) => <Badge tone="success">{row.champion_score}/100</Badge> },
                  { key: "use-case", header: "Use Case & Project Development", render: (row) => <CategoryCell row={row} category="VISION_STRATEGY" /> },
                  { key: "ecosystem", header: "Ecosystem Library Contribution", render: (row) => <CategoryCell row={row} category="ECOSYSTEM_LIBRARY" /> },
                  { key: "scouting", header: "Startup Scouting & AI Studio Support", render: (row) => <CategoryCell row={row} category="STARTUP_SCOUTING" /> },
                  { key: "case", header: "Case Study Contribution", render: (row) => <CategoryCell row={row} category="COMMUNICATION_CASE_STUDY" /> },
                  { key: "event", header: "Events & Communication Participation", render: (row) => <CategoryCell row={row} category="COMMUNICATION_EVENT" /> },
                  { key: "training", header: "Training Completion", render: (row) => <CategoryCell row={row} category="TRAINING" /> },
                  { key: "last", header: "Last Program Activity", render: (row) => formatDate(row.last_activity_at) }
                ]}
              />
            ) : (
              <EmptyState title="No Champion activity yet" description="Manual CRM actions and admin-recorded program activities will activate the scorecard." />
            )}
          </SectionCard>

          <SectionCard>
            <div className="section-heading">
              <h2>My Champion card</h2>
              <p>Your current weighted score, target progress, and supporting CRM evidence.</p>
            </div>
            {championMe ? (
              <div className="my-rank-card">
                <div className="rank"><Sparkles size={20} />{championMe.rank ? `#${championMe.rank}` : "Unranked"}</div>
                <h2>{championMe.full_name}</h2>
                <strong>{championMe.champion_score}/100 YZ Champion Score</strong>
                <Badge tone="info">{championMe.ecosystem_library_raw_count ?? championMe.raw_counts?.ECOSYSTEM_LIBRARY ?? 0} Ecosystem Library evidence items</Badge>
                <div className="candidate-count-grid">
                  {CATEGORY_KEYS.map((category) => (
                    <div className="mini-stat" key={category}>
                      <span>{CATEGORY_LABELS[category]}</span>
                      <strong>{championMe.weighted_breakdown?.[category]?.category_score ?? 0}</strong>
                    </div>
                  ))}
                </div>
                <div className="phase-note">{championMe.missing_targets?.[0] ?? "All scorecard targets are complete for this period."}</div>
              </div>
            ) : null}
          </SectionCard>
        </>
      ) : null}

      {tab === "activity" ? <ActivityPointsTab period={period} metric={metric} setPeriod={setPeriod} setMetric={setMetric} leaderboard={activity} me={activityMe} isLoading={isLoading} /> : null}
      {tab === "rules" ? <ScoreRulesTab rules={rules} /> : null}
    </ProtectedPage>
  );
}

function CategoryCell({ row, category }: { row: ChampionLeaderboardRow; category: string }) {
  const item = row.weighted_breakdown?.[category];
  if (!item) return "-";
  return (
    <div className="record-title">
      <strong>{item.category_score}/100</strong>
      <span className="record-subtitle">{item.weighted_score}/{item.weight} weighted</span>
    </div>
  );
}

function ExpandedScore({ row }: { row: ChampionLeaderboardRow }) {
  const recentEvidence = row.recent_crm_activity_evidence ?? [];
  return (
    <div className="phase-note">
      {CATEGORY_KEYS.map((category) => {
        const item = row.weighted_breakdown?.[category];
        return item ? `${CATEGORY_LABELS[category]}: ${item.raw_count} activity (${item.category_score}/100)` : null;
      }).filter(Boolean).join(" | ")}
      {` | CRM Activity Points evidence: ${row.crm_activity_points} pts`}
      {` | Ecosystem qualifying count: ${row.ecosystem_library_raw_count ?? row.raw_counts?.ECOSYSTEM_LIBRARY ?? 0}`}
      {recentEvidence.length ? ` | Recent CRM evidence: ${recentEvidence.map((item) => `${item.contribution_type} (+${item.points})`).join(", ")}` : ""}
      {row.missing_targets?.[0] ? ` | Next: ${row.missing_targets[0]}` : ""}
    </div>
  );
}

function ActivityPointsTab({ period, metric, setPeriod, setMetric, leaderboard, me, isLoading }: {
  period: Period;
  metric: Metric;
  setPeriod: (period: Period) => void;
  setMetric: (metric: Metric) => void;
  leaderboard: LeaderboardResponse | null;
  me: LeaderboardRow | null;
  isLoading: boolean;
}) {
  return (
    <>
      <div className="section-toolbar">
        <Select aria-label="Leaderboard period" value={period} onChange={(event) => setPeriod(event.target.value as Period)}>
          <option value="all_time">All time</option>
          <option value="last_30_days">Last 30 days</option>
          <option value="last_7_days">Last 7 days</option>
        </Select>
        <Select aria-label="Leaderboard metric" value={metric} onChange={(event) => setMetric(event.target.value as Metric)}>
          <option value="points">Total points</option>
          <option value="organizations">Organizations added</option>
          <option value="notes">Notes added</option>
          <option value="contacts">Contacts added</option>
          <option value="opportunities">Opportunities created</option>
        </Select>
      </div>
      <div className="two-column">
        <SectionCard>
          <div className="section-heading section-heading--inline">
            <div><h2>CRM Activity Points</h2><p>{isLoading ? "Loading..." : `${leaderboard?.total_users ?? 0} ranked users`}</p></div>
            <Badge tone="info">Operational contribution score</Badge>
          </div>
          {leaderboard?.items.length ? (
            <Table
              rows={leaderboard.items}
              getRowKey={(row) => row.user_id}
              columns={[
                { key: "rank", header: "Rank", render: (row) => <strong>#{row.rank}</strong> },
                { key: "user", header: "User", render: (row) => <div className="record-title"><strong>{row.full_name}</strong><span className="record-subtitle">{row.email}</span></div> },
                { key: "points", header: "CRM Activity Points", render: (row) => <Badge tone="success">{row.total_points}</Badge> },
                { key: "orgs", header: "Startups/Vendors", render: (row) => row.organizations_created },
                { key: "notes", header: "Notes", render: (row) => row.notes_created },
                { key: "contacts", header: "Contacts", render: (row) => row.contacts_created },
                { key: "opps", header: "Opportunities", render: (row) => row.opportunities_created },
                { key: "last", header: "Last contribution", render: (row) => formatDate(row.last_contribution_at) }
              ]}
            />
          ) : (
            <EmptyState title="No manual contributions yet" description="CRM Activity Points appear after manual CRM actions." />
          )}
        </SectionCard>
        <SectionCard>
          <div className="section-heading"><h2>My CRM Activity Points</h2><p>Operational CRM contribution total retained alongside Champion Score.</p></div>
          {me ? <div className="my-rank-card"><div className="rank">{me.rank ? `#${me.rank}` : "Unranked"}</div><h2>{me.full_name}</h2><strong>{me.total_points} points</strong></div> : null}
        </SectionCard>
      </div>
    </>
  );
}

function ScoreRulesTab({ rules }: { rules: ChampionScoreRule[] }) {
  return (
    <SectionCard>
      <div className="section-heading">
        <h2>YZ Champion Score rules</h2>
        <p>Slide-aligned areas, tasks, KPIs, target thresholds, weights, and tracking owners.</p>
      </div>
      <Table
        rows={rules}
        getRowKey={(row) => row.category}
        columns={[
          { key: "area", header: "Area", render: (row) => <div className="record-title"><strong>{row.label}</strong>{row.helper_label ? <span className="record-subtitle">{row.helper_label}</span> : null}</div> },
          { key: "task", header: "Task", render: (row) => row.task },
          { key: "kpi", header: "KPI", render: (row) => row.kpi },
          { key: "target", header: "Target", render: (row) => <div className="record-title"><span>{row.thresholds}</span>{row.note ? <span className="record-subtitle">{row.note}</span> : null}</div> },
          { key: "weight", header: "Weight", render: (row) => <Badge tone="info">{row.weight}%</Badge> },
          { key: "owner", header: "Tracking Owner", render: (row) => row.tracking_owner }
        ]}
      />
    </SectionCard>
  );
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

const fallbackRules: ChampionScoreRule[] = [
  {
    category: "VISION_STRATEGY",
    label: "Use Case & Project Development",
    helper_label: "Use-case Önerisi ve Projelendirme",
    weight: 40,
    task: "Support business units in identifying AI development areas, sharing global use-case examples, and helping projectize ideas.",
    kpi: "Department use-case recommendation and projectization.",
    tracking_owner: "YZ Dönüşüm Ofisi",
    qualifying_activity_types: ["OPPORTUNITY_CREATED", "USE_CASE_PROPOSED", "USE_CASE_PROJECTIZED", "OPPORTUNITY_MOVED_TO_PROJECT"],
    thresholds: "0 project = 0; 1 project = 50; 2+ projects = 100"
  },
  {
    category: "ECOSYSTEM_LIBRARY",
    label: "Ecosystem Library Contribution",
    weight: 15,
    task: "Discover new technology vendors, startups, tools, products, and events; improve Ecosystem Library.",
    kpi: "Pre-evaluated vendor/product/tool/startup/event recommendation.",
    tracking_owner: "YZ Dönüşüm Ofisi",
    qualifying_activity_types: ["STARTUP_ADDED", "VENDOR_ADDED", "AI_TOOL_ADDED", "EVENT_ADDED", "CONTACT_ADDED", "DECK_UPLOADED", "ORGANIZATION_ENRICHED"],
    thresholds: "0 contribution = 0; 1-7 contributions = 50; 8+ contributions = 100",
    note: "Qualifying CRM actions such as adding startups, events, AI tools, contacts, and startup decks are counted here."
  },
  {
    category: "STARTUP_SCOUTING",
    label: "Startup Scouting & AI Studio Support",
    weight: 15,
    task: "Actively support startup-related AI Studio work.",
    kpi: "Startup scouting/review actions.",
    tracking_owner: "YZ Dönüşüm Ofisi",
    qualifying_activity_types: ["STARTUP_REVIEWED", "STARTUP_SHORTLISTED", "FOLLOW_UP_COMPLETED"],
    thresholds: "0 scouting = 0; 1-4 scouting = 50; 5+ scouting = 100"
  },
  {
    category: "COMMUNICATION_CASE_STUDY",
    label: "Case Study Contribution",
    weight: 10,
    task: "Contribute to company success/learning stories as case studies.",
    kpi: "Case study content contribution.",
    tracking_owner: "YZ Dönüşüm Ofisi",
    qualifying_activity_types: ["CASE_STUDY_SUBMITTED", "CASE_STUDY_APPROVED"],
    thresholds: "0 case study = 0; 1 case study = 50; 2+ case studies = 100"
  },
  {
    category: "COMMUNICATION_EVENT",
    label: "Events & Communication Participation",
    weight: 10,
    task: "Take roles in AI Transformation Office communication events.",
    kpi: "Event participation/support.",
    tracking_owner: "YZ Dönüşüm Ofisi",
    qualifying_activity_types: ["EVENT_PARTICIPATION"],
    thresholds: "0-1 event = 0; 2-4 events = 50; 5+ events = 100"
  },
  {
    category: "TRAINING",
    label: "Training Completion",
    weight: 10,
    task: "Participate in Borusan Academy AI training programs.",
    kpi: "Complete required internal AI training programs.",
    tracking_owner: "Akademi",
    qualifying_activity_types: ["TRAINING_COMPLETED"],
    thresholds: "Incomplete/missing = 0; complete = 100"
  }
];
