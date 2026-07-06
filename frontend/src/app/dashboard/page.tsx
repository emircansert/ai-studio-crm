"use client";

import {
  ArrowRight,
  Bot,
  Building2,
  CalendarDays,
  Clock,
  FileText,
  Lightbulb,
  Network,
  Plus,
  Trophy
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { apiRequest } from "@/lib/api";
import type {
  ChampionLeaderboardResponse,
  ChampionLeaderboardRow,
  DashboardSummary,
  LeaderboardResponse,
  LeaderboardRow
} from "@/types/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [me, setMe] = useState<LeaderboardRow | null>(null);
  const [championLeaderboard, setChampionLeaderboard] = useState<ChampionLeaderboardResponse | null>(null);
  const [championMe, setChampionMe] = useState<ChampionLeaderboardRow | null>(null);
  const [error, setError] = useState<unknown>(null);

  async function load() {
    setError(null);
    Promise.all([
      apiRequest<DashboardSummary>("/api/v1/dashboard/summary"),
      apiRequest<LeaderboardResponse>("/api/v1/leaderboard?period=last_30_days&metric=points&limit=1"),
      apiRequest<LeaderboardRow>("/api/v1/leaderboard/me?period=last_30_days&metric=points"),
      apiRequest<ChampionLeaderboardResponse>("/api/v1/leaderboard/champion?period=last_30_days&limit=1"),
      apiRequest<ChampionLeaderboardRow>("/api/v1/leaderboard/champion/me?period=last_30_days")
    ])
      .then(([summaryData, leaderboardData, myData, championData, championMyData]) => {
        setSummary(summaryData);
        setLeaderboard(leaderboardData);
        setMe(myData);
        setChampionLeaderboard(championData);
        setChampionMe(championMyData);
      })
      .catch((caught) => setError(caught));
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const topChampion = championLeaderboard?.items[0] ?? null;

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Operations"
        title="Ecosystem Intelligence Operations"
        description="Manage startup discovery, use-case development, PoC movement, ecosystem engagement, and YZ Champion progress."
        actions={
          <div className="button-row">
            <Link className="button button--primary" href="/companies">
              <Plus size={16} />
              Add Startup
            </Link>
            <Link className="button button--secondary" href="/use-cases">
              <Lightbulb size={16} />
              Add Use Case
            </Link>
            <Link className="button button--secondary" href="/ai-tools">
              <Bot size={16} />
              Add AI Tool
            </Link>
            <Link className="button button--secondary" href="/events">
              <CalendarDays size={16} />
              Add Event/Training
            </Link>
          </div>
        }
      />

      {error ? <ErrorState title="Could not load dashboard data" error={error} onRetry={() => void load()} /> : null}

      <div className="stat-grid dashboard-kpi-grid">
        <StatCard
          label="Total startups"
          value={String(summary?.total_startups ?? "--")}
          detail={`${summary?.total_vendors ?? "--"} vendors tracked`}
          icon={<Building2 size={18} />}
        />
        <StatCard
          label="Open follow-ups"
          value={String(summary?.open_follow_ups ?? "--")}
          detail={`${summary?.overdue_follow_ups ?? "--"} overdue`}
          icon={<Clock size={18} />}
        />
        <StatCard label="Use cases" value="--" detail="Tracked in Use Cases" icon={<Lightbulb size={18} />} />
        <StatCard
          label="Startup decks"
          value={String(summary?.total_startup_decks ?? "--")}
          detail="Uploaded pitch decks"
          icon={<FileText size={18} />}
        />
        <StatCard
          label="YZ Champion leader"
          value={topChampion?.full_name ?? summary?.top_champion?.full_name ?? "--"}
          detail={topChampion ? `${topChampion.champion_score}/100 score` : "No program activity"}
          icon={<Trophy size={18} />}
        />
        <StatCard
          label="Events / trainings"
          value={String(summary?.total_events ?? "--")}
          detail="Events Library records"
          icon={<CalendarDays size={18} />}
        />
      </div>

      <div className="dashboard-ops-grid">
        <div className="dashboard-main-stack">
          <SectionCard>
            <div className="section-heading section-heading--inline">
              <div>
                <h2>Priority follow-ups</h2>
                <p>Open and overdue actions that need attention.</p>
              </div>
              <Link className="link-button" href="/follow-ups">
                View all
              </Link>
            </div>
            <div className="placeholder-grid dashboard-metric-grid">
              <div>
                <strong>{summary?.open_follow_ups ?? "--"}</strong>
                <p className="record-subtitle">Open follow-ups</p>
              </div>
              <div>
                <strong>{summary?.overdue_follow_ups ?? "--"}</strong>
                <p className="record-subtitle">Overdue follow-ups</p>
              </div>
            </div>
          </SectionCard>

          <SectionCard>
            <div className="section-heading section-heading--inline">
              <div>
                <h2>Recently added startups</h2>
                <p>Use Startup Library filters to review newly added records by date, category, source, and owner.</p>
              </div>
              <Link className="link-button" href="/companies">
                Open library
              </Link>
            </div>
            <EmptyState
              title="Recent startup feed is not available yet"
              description="The Startup Library is ready for date sorting and filtering; a compact recent feed can be added when the workspace needs it."
            />
          </SectionCard>

          <SectionCard>
            <div className="section-heading section-heading--inline">
              <div>
                <h2>Recent ecosystem activity</h2>
                <p>Operational movement across imports, opportunities, use cases, events, and library enrichment.</p>
              </div>
              <Link className="link-button" href="/imports">
                Import Center
              </Link>
            </div>
            <div className="placeholder-grid dashboard-metric-grid">
              <div>
                <strong>{summary?.active_imported_batches ?? "--"}</strong>
                <p className="record-subtitle">Active import batches</p>
              </div>
              <div>
                <strong>{summary?.total_opportunities ?? "--"}</strong>
                <p className="record-subtitle">PoC opportunities</p>
              </div>
              <div>
                <strong>{summary?.total_network_institutions ?? "--"}</strong>
                <p className="record-subtitle">Network institutions</p>
              </div>
              <div>
                <strong>{summary?.total_organizations ?? "--"}</strong>
                <p className="record-subtitle">Total organizations</p>
              </div>
            </div>
          </SectionCard>
        </div>

        <aside className="dashboard-side-stack">
          <SectionCard className="dashboard-scorecard">
            <div className="section-heading">
              <h2>YZ Champion leader</h2>
              <p>Weighted Champion Score, last 30 days.</p>
            </div>
            <div className="scorecard-value">
              <Trophy size={20} />
              <div>
                <strong>{topChampion?.full_name ?? summary?.top_champion?.full_name ?? "No leader yet"}</strong>
                <span>{topChampion ? `${topChampion.champion_score}/100` : "No program activity recorded"}</span>
              </div>
            </div>
            <div className="leaderboard-row">
              <div className="rank">My score</div>
              <strong>
                {championMe?.rank
                  ? `#${championMe.rank} - ${championMe.champion_score}/100`
                  : summary?.my_champion_score
                    ? `${summary.my_champion_score.champion_score}/100`
                    : "Unranked"}
              </strong>
            </div>
            <Link className="button button--secondary button--full" href="/leaderboard">
              Open leaderboard
            </Link>
          </SectionCard>

          <SectionCard>
            <div className="section-heading">
              <h2>Latest import</h2>
              <p>Current Excel library ingestion status.</p>
            </div>
            <div className="leaderboard-row">
              <div className="rank">Status</div>
              <strong>{summary?.latest_import_status ?? "No import yet"}</strong>
            </div>
            <Link className="button button--secondary button--full" href="/imports">
              Open Import Center
            </Link>
          </SectionCard>

          <SectionCard>
            <div className="section-heading">
              <h2>Quick links</h2>
              <p>Jump into common workspaces.</p>
            </div>
            <div className="dashboard-quick-grid">
              <Link className="quick-action-card" href="/companies">
                <Building2 size={16} />
                <div>
                  <strong>Startup Library</strong>
                  <span>Search, filter, and enrich records.</span>
                </div>
                <ArrowRight size={15} />
              </Link>
              <Link className="quick-action-card" href="/use-cases">
                <Lightbulb size={16} />
                <div>
                  <strong>Use Cases</strong>
                  <span>Capture project ideas and status.</span>
                </div>
                <ArrowRight size={15} />
              </Link>
              <Link className="quick-action-card" href="/events">
                <CalendarDays size={16} />
                <div>
                  <strong>Events Library</strong>
                  <span>Track events, training, and participation.</span>
                </div>
                <ArrowRight size={15} />
              </Link>
            </div>
          </SectionCard>

          <SectionCard>
            <div className="section-heading">
              <h2>Borusan fit distribution</h2>
              <p>Committed fit signals by company.</p>
            </div>
            {summary?.top_borusan_company_fit_counts?.length ? (
              <div className="leaderboard-list">
                {summary.top_borusan_company_fit_counts.map((item) => (
                  <div className="leaderboard-row" key={item.code}>
                    <div className="rank">
                      <Network size={15} />
                      {item.code}
                    </div>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No fit data yet" description="Fit counts appear after import commit or manual fit entry." />
            )}
          </SectionCard>

          <SectionCard>
            <div className="section-heading">
              <h2>CRM activity points</h2>
              <p>Operational contribution signal for CRM usage.</p>
            </div>
            <div className="leaderboard-row">
              <div className="rank">Me</div>
              <strong>{me?.rank ? `#${me.rank} - ${me.total_points} pts` : "No activity yet"}</strong>
            </div>
            <div className="leaderboard-row">
              <div className="rank">Top</div>
              <strong>{leaderboard?.items[0]?.full_name ?? "No activity yet"}</strong>
            </div>
          </SectionCard>
        </aside>
      </div>
    </ProtectedPage>
  );
}
