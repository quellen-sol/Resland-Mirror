export type DashboardMenuItemKey =
  | "upload"
  | "tailor"
  | "tailored"
  | "system-design"
  | "export"
  | "admin"
  | "edit-profile"
  | "billing"
  | "help"
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
  { key: "tailor", label: "Tailor Resume", href: "/tailor" },
  { key: "tailored", label: "Tailored Resumes", href: "/tailored" },
  { key: "system-design", label: "System Design Mock", href: "/system-design" },
  { key: "export", label: "Export Resume" },
  { key: "admin", label: "Admin Dashboard", href: "/admin", adminOnly: true },
  { key: "edit-profile", label: "Edit Profile", href: "/edit-profile" },
  { key: "billing", label: "Billing", href: "/billing" },
  { key: "help", label: "Help & FAQ", href: "/help" },
  { key: "sign-out", label: "Sign Out", href: "/auth/logout" },
];

export function getDashboardMenuItems(isAdmin: boolean): DashboardMenuItem[] {
  return DASHBOARD_MENU_ITEMS.filter((item) => !item.adminOnly || isAdmin);
}
