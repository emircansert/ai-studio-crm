import type { SectionAccessLevel, User } from "@/types/api";

export const ACCESS_HIDDEN: SectionAccessLevel = "HIDDEN";
export const ACCESS_VIEW: SectionAccessLevel = "VIEW";
export const ACCESS_FULL: SectionAccessLevel = "FULL";

export const SECTION_BY_FRONTEND_PATH: Array<{ prefix: string; sectionKey: string; exact?: boolean }> = [
  { prefix: "/admin/champion-program", sectionKey: "CHAMPION_PROGRAM" },
  { prefix: "/admin/leaderboard", sectionKey: "LEADERBOARD_ADMIN" },
  { prefix: "/admin", sectionKey: "ADMIN_OVERVIEW", exact: true },
  { prefix: "/companies", sectionKey: "STARTUP_LIBRARY" },
  { prefix: "/use-cases", sectionKey: "USE_CASES" },
  { prefix: "/opportunities", sectionKey: "POC_PIPELINE" },
  { prefix: "/events", sectionKey: "EVENTS_LIBRARY" },
  { prefix: "/ai-tools", sectionKey: "AI_TOOLS_LIBRARY" },
  { prefix: "/network", sectionKey: "NETWORK_LIBRARY" },
  { prefix: "/vendors", sectionKey: "VENDOR_LIBRARY" },
  { prefix: "/follow-ups", sectionKey: "FOLLOW_UPS" },
  { prefix: "/leaderboard", sectionKey: "LEADERBOARD" }
].sort((a, b) => b.prefix.length - a.prefix.length);

export function fallbackAccessForUser(user: User | null | undefined): SectionAccessLevel {
  return user?.role === "ADMIN" ? ACCESS_FULL : ACCESS_HIDDEN;
}

export function getSectionAccess(
  access: Record<string, SectionAccessLevel> | null,
  user: User | null | undefined,
  sectionKey?: string
): SectionAccessLevel {
  if (!sectionKey) return ACCESS_FULL;
  return access?.[sectionKey] ?? fallbackAccessForUser(user);
}

export function canViewSection(
  access: Record<string, SectionAccessLevel> | null,
  user: User | null | undefined,
  sectionKey?: string
): boolean {
  const level = getSectionAccess(access, user, sectionKey);
  return level === ACCESS_VIEW || level === ACCESS_FULL;
}

export function canEditSection(
  access: Record<string, SectionAccessLevel> | null,
  user: User | null | undefined,
  sectionKey?: string
): boolean {
  return getSectionAccess(access, user, sectionKey) === ACCESS_FULL;
}

export function sectionKeyForPath(pathname: string): string | undefined {
  const match = SECTION_BY_FRONTEND_PATH.find(({ exact, prefix }) => pathname === prefix || (!exact && pathname.startsWith(`${prefix}/`)));
  return match?.sectionKey;
}
