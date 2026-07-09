"use client";

import {
  Activity,
  BarChart3,
  Bell,
  Bot,
  Building2,
  CalendarDays,
  FileSpreadsheet,
  Gauge,
  KeyRound,
  Lightbulb,
  LogOut,
  Network,
  PanelLeft,
  Shield,
  Sparkles,
  Store,
  Trophy,
  UploadCloud
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";

import { Button } from "@/components/ui/Button";
import { apiRequest, apiUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ACCESS_VIEW, canViewSection, getSectionAccess, sectionKeyForPath } from "@/lib/sectionAccess";
import type { BrandingAsset, CurrentUserSectionAccessResponse, SectionAccessLevel } from "@/types/api";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  adminOnly?: boolean;
  sectionKey?: string;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

const navSections: NavSection[] = [
  {
    title: "Core CRM",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: Gauge },
      { href: "/companies", label: "Startup Library", icon: Building2, sectionKey: "STARTUP_LIBRARY" },
      { href: "/use-cases", label: "Use Cases", icon: Lightbulb, sectionKey: "USE_CASES" },
      { href: "/opportunities", label: "PoC Pipeline", icon: Activity, sectionKey: "POC_PIPELINE" },
      { href: "/events", label: "Events Library", icon: CalendarDays, sectionKey: "EVENTS_LIBRARY" },
      { href: "/ai-tools", label: "AI Tools Library", icon: Bot, sectionKey: "AI_TOOLS_LIBRARY" },
      { href: "/network", label: "Network Library", icon: Network, sectionKey: "NETWORK_LIBRARY" },
      { href: "/vendors", label: "Vendor Library", icon: Store, sectionKey: "VENDOR_LIBRARY" },
      { href: "/imports", label: "Import Center", icon: UploadCloud }
    ]
  },
  {
    title: "Engagement",
    items: [
      { href: "/follow-ups", label: "Follow-ups", icon: KeyRound, sectionKey: "FOLLOW_UPS" },
      { href: "/notifications", label: "Notifications", icon: Bell },
      { href: "/leaderboard", label: "Leaderboard", icon: Trophy, sectionKey: "LEADERBOARD" },
      { href: "/admin/champion-program", label: "Champion Program", icon: Trophy, adminOnly: true, sectionKey: "CHAMPION_PROGRAM" }
    ]
  },
  {
    title: "Admin",
    items: [
      { href: "/admin", label: "Admin Overview", icon: Shield, adminOnly: true, sectionKey: "ADMIN_OVERVIEW" },
      { href: "/admin/users", label: "User Management", icon: KeyRound, adminOnly: true },
      { href: "/admin/leaderboard", label: "Leaderboard Admin", icon: Trophy, adminOnly: true, sectionKey: "LEADERBOARD_ADMIN" },
      { href: "/admin/activity", label: "CRM Activity", icon: Activity, adminOnly: true },
      { href: "/admin/branding", label: "Admin Branding", icon: Sparkles, adminOnly: true },
      { href: "/admin/audit-logs", label: "Audit Logs", icon: FileSpreadsheet, adminOnly: true },
      { href: "/admin/diagnostics", label: "Diagnostics", icon: Activity, adminOnly: true }
    ]
  }
];

// AppShell is rendered per-page (via ProtectedPage), so it remounts on every
// client-side navigation. This module-level cache survives those remounts so
// the notification unread-count is fetched at most once per interval no matter
// how often the user navigates, rather than on every page change.
const UNREAD_POLL_MS = 60000;
let unreadCache = { count: 0, fetchedAt: 0 };
let unreadInFlight = false;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isReady, token, user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeLogo, setActiveLogo] = useState<BrandingAsset | null>(null);
  const [sectionAccess, setSectionAccess] = useState<Record<string, SectionAccessLevel> | null>(null);
  const [sectionAccessError, setSectionAccessError] = useState<string | null>(null);
  const [readOnlyNotice, setReadOnlyNotice] = useState<string | null>(null);
  const [unreadNotifications, setUnreadNotifications] = useState(0);

  useEffect(() => {
    if (isReady && !token) {
      router.replace("/login");
    }
  }, [isReady, router, token]);

  useEffect(() => {
    if (!token) return;
    apiRequest<BrandingAsset | null>("/api/v1/admin/branding/active")
      .then(setActiveLogo)
      .catch(() => undefined);
  }, [token]);

  useEffect(() => {
    if (!token) {
      unreadCache = { count: 0, fetchedAt: 0 };
      setUnreadNotifications(0);
      return;
    }
    // Show whatever is cached immediately, then hit the network only when the
    // cached value is older than the poll interval. Because the cache lives at
    // module scope, navigating between pages reuses it instead of refetching.
    let active = true;
    setUnreadNotifications(unreadCache.count);
    const maybeRefresh = () => {
      if (unreadInFlight || Date.now() - unreadCache.fetchedAt < UNREAD_POLL_MS) {
        return;
      }
      unreadInFlight = true;
      apiRequest<{ unread_count: number }>("/api/v1/notifications/unread-count")
        .then((response) => {
          unreadCache = { count: response.unread_count, fetchedAt: Date.now() };
          if (active) setUnreadNotifications(response.unread_count);
        })
        .catch(() => undefined)
        .finally(() => {
          unreadInFlight = false;
        });
    };
    maybeRefresh();
    const interval = window.setInterval(maybeRefresh, UNREAD_POLL_MS);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [token]);

  useEffect(() => {
    if (!token) {
      setSectionAccess(null);
      return;
    }
    apiRequest<CurrentUserSectionAccessResponse>("/api/v1/users/me/section-access")
      .then((response) => {
        setSectionAccess(response.access);
        setSectionAccessError(null);
      })
      .catch((caught) => {
        setSectionAccess(null);
        setSectionAccessError(caught instanceof Error ? caught.message : "Could not load section access.");
      });
  }, [token]);

  if (!isReady || !token) {
    return (
      <main className="loading-screen">
        <div className="loading-mark">
          <BarChart3 size={26} />
        </div>
      </main>
    );
  }

  if (pathname.startsWith("/admin") && user?.role !== "ADMIN") {
    return (
      <div className="app-shell">
        <aside className="sidebar">
          <Brand activeLogo={activeLogo} />
        </aside>
        <main className="content">
          <div className="section-card">
            <div className="section-heading">
              <h1>Access denied</h1>
              <p>Admin permissions are required for this area.</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const currentSectionKey = sectionKeyForPath(pathname);
  const currentSectionAccess = getSectionAccess(sectionAccess, user, currentSectionKey);
  const currentSectionIsHidden = currentSectionKey ? !canViewSection(sectionAccess, user, currentSectionKey) : false;
  const isViewOnlySection = currentSectionAccess === ACCESS_VIEW;

  function handleContentClickCapture(event: ReactMouseEvent<HTMLElement>) {
    if (!isViewOnlySection) return;
    const target = event.target as HTMLElement | null;
    const actionElement = target?.closest("button, a");
    if (!actionElement) return;
    const label = `${actionElement.textContent ?? ""} ${actionElement.getAttribute("aria-label") ?? ""}`.trim();
    const mutatingActionPattern = /\b(add|assign|archive|cancel|commit|complete|create|delete|edit|rate|rating|remove|reset|save|unarchive|upload)\b/i;
    if (mutatingActionPattern.test(label)) {
      event.preventDefault();
      event.stopPropagation();
      setReadOnlyNotice("This section is view-only for your account. Ask an admin for full access to make changes.");
    }
  }

  if (currentSectionIsHidden) {
    return (
      <div className="app-shell">
        <aside className="sidebar">
          <Brand activeLogo={activeLogo} />
        </aside>
        <main className="content">
          <div className="section-card">
            <div className="section-heading">
              <h1>Access denied</h1>
              <p>This section is hidden for your account. Ask an admin to grant view or full access if you need it.</p>
            </div>
            {sectionAccessError ? <div className="alert alert--warning">{sectionAccessError}</div> : null}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "sidebar--open" : ""}`}>
        <Brand activeLogo={activeLogo} />

        <nav className="nav">
          {navSections.map((section) => {
            const visibleItems = section.items.filter((item) => {
              if (item.adminOnly && user?.role !== "ADMIN") return false;
              return canViewSection(sectionAccess, user, item.sectionKey);
            });
            if (!visibleItems.length) return null;

            return (
              <div className="nav-section" key={section.title}>
                <span className="nav-section-title">{section.title}</span>
                {visibleItems.map((item) => {
                  const Icon = item.icon;
                  const active =
                    pathname === item.href ||
                    (item.href !== "/dashboard" && item.href !== "/admin" && pathname.startsWith(item.href));
                  return (
                    <Link
                      className={`nav-item ${active ? "nav-item--active" : ""}`}
                      href={item.href}
                      key={item.href}
                      onClick={() => setSidebarOpen(false)}
                    >
                      <Icon size={18} />
                      <span>{item.label}</span>
                      {item.href === "/notifications" && unreadNotifications > 0 ? (
                        <span className="nav-pill">{unreadNotifications}</span>
                      ) : null}
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </nav>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <button
            aria-label="Open navigation"
            className="icon-button mobile-only"
            onClick={() => setSidebarOpen((value) => !value)}
            type="button"
          >
            <PanelLeft size={20} />
          </button>
          <div className="topbar-title">
            <span>Workspace</span>
            <strong>Ecosystem intelligence operations</strong>
          </div>
          <div className="profile-chip">
            <div>
              <strong>{user?.full_name ?? "CRM User"}</strong>
              <span>{user?.role ?? "USER"}</span>
            </div>
            <Link className="button button--ghost" href="/account">
              Account
            </Link>
            <Button variant="ghost" onClick={logout} aria-label="Logout">
              <LogOut size={17} />
              Logout
            </Button>
          </div>
        </header>

        <main className="content">
          {sectionAccessError ? <div className="alert alert--warning">Could not load section access. Conservative defaults are active.</div> : null}
          {isViewOnlySection ? (
            <div className="alert alert--warning">
              You have view-only access in this section. Create, edit, archive, upload, and delete actions are blocked by the API.
            </div>
          ) : null}
          {readOnlyNotice && isViewOnlySection ? <div className="alert alert--warning">{readOnlyNotice}</div> : null}
          <div onClickCapture={handleContentClickCapture}>{children}</div>
        </main>
      </div>
    </div>
  );
}

function Brand({ activeLogo }: { activeLogo: BrandingAsset | null }) {
  const logoUrl = activeLogo?.content_url ? apiUrl(activeLogo.content_url) : null;
  return (
    <Link className="brand" href="/dashboard">
      {logoUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img className="brand-logo" src={logoUrl} alt="Borusan AI Studio" />
      ) : (
        <div className="brand-mark">AI</div>
      )}
      <div>
        <strong>Borusan AI Studio</strong>
        <span>Ecosystem CRM</span>
      </div>
    </Link>
  );
}
