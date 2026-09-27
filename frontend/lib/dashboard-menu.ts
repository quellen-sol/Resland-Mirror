export type DashboardMenuItemKey =
  | "upload"
  | "tailor"
  | "export"
  | "admin"
  | "edit-profile"
  | "billing"
  | "sign-out";

export interface DashboardMenuItem {
  key: DashboardMenuItemKey;
  label: string;
  href?: string;
  adminOnly?: boolean;
}

// Order mirrors the dashboard header row the menu replaces.
const DASHBOARD_MENU_ITEMS: DashboardMenuItem[] = [
  { key: "upload", label: "Upload New Resume" },
  { key: "tailor", label: "Tailor resume", href: "/tailor" },
  { key: "export", label: "Export resume" },
  { key: "admin", label: "Admin Dashboard", href: "/admin", adminOnly: true },
  { key: "edit-profile", label: "Edit profile", href: "/edit-profile" },
  { key: "billing", label: "Billing", href: "/billing" },
  { key: "sign-out", label: "Sign out", href: "/auth/logout" },
];

export function getDashboardMenuItems(isAdmin: boolean): DashboardMenuItem[] {
  return DASHBOARD_MENU_ITEMS.filter((item) => !item.adminOnly || isAdmin);
}
