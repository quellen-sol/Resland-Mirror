"use client";

import { useState } from "react";
import Link from "next/link";
import {
  LogOut,
  Menu,
  PenLine,
  ShieldCheck,
  Sparkles,
  Zap,
  type LucideIcon,
} from "lucide-react";
import BalanceChip from "@/components/balance-chip";
import { buttonVariants } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "cn";
import {
  getDashboardMenuItems,
  type DashboardMenuItemKey,
} from "@/lib/dashboard-menu";
import UploadResumeDialog from "./upload-resume-dialog";
import ExportResumeButton from "./export-resume-button";

const LINK_ICONS: Partial<Record<DashboardMenuItemKey, LucideIcon>> = {
  tailor: Sparkles,
  admin: ShieldCheck,
  "edit-profile": PenLine,
  billing: Zap,
};

const menuRowClass =
  "inline-flex w-full items-center justify-start gap-2 rounded-md px-3 py-2 text-sm font-medium text-zinc-200 transition-colors hover:bg-zinc-800/60 hover:text-zinc-100 [&_svg]:size-4 [&_svg]:shrink-0";

// Upload/export render their own styled buttons; normalize them into menu rows.
const menuActionClass =
  "[&_button]:h-auto [&_button]:w-full [&_button]:justify-start [&_button]:px-3 [&_button]:py-2";

export default function DashboardMenu({
  accessToken,
  isAdmin,
  uploadDisabled,
}: {
  accessToken: string;
  isAdmin: boolean;
  uploadDisabled?: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        aria-label="Open menu"
        title="Menu"
        className={cn(
          buttonVariants({ variant: "outline", size: "icon-sm" }),
          "border-zinc-700 bg-transparent text-zinc-200 hover:bg-zinc-800/60 hover:text-zinc-100",
        )}
      >
        <Menu />
      </SheetTrigger>
      <SheetContent
        side="right"
        className="border-zinc-800 bg-zinc-950 text-zinc-100"
      >
        <SheetHeader>
          <SheetTitle className="text-zinc-100">Menu</SheetTitle>
        </SheetHeader>
        <div className="flex min-h-0 flex-1 flex-col gap-4">
          <div onClick={() => setOpen(false)} className="self-start">
            <BalanceChip accessToken={accessToken} />
          </div>
          <nav className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
            {getDashboardMenuItems(isAdmin).map((item) => {
              switch (item.key) {
                case "upload":
                  return (
                    <div key={item.key} className={menuActionClass}>
                      <UploadResumeDialog
                        accessToken={accessToken}
                        disabled={uploadDisabled}
                      />
                    </div>
                  );
                case "export":
                  return (
                    <div key={item.key} className={menuActionClass}>
                      <ExportResumeButton accessToken={accessToken} />
                    </div>
                  );
                case "sign-out":
                  return (
                    <a
                      key={item.key}
                      href={item.href}
                      className={cn(
                        menuRowClass,
                        "text-zinc-500 hover:text-zinc-300",
                      )}
                    >
                      <LogOut /> {item.label}
                    </a>
                  );
                default: {
                  const Icon = LINK_ICONS[item.key];
                  return (
                    <Link
                      key={item.key}
                      href={item.href ?? "/dashboard"}
                      onClick={() => setOpen(false)}
                      className={menuRowClass}
                    >
                      {Icon && <Icon />} {item.label}
                    </Link>
                  );
                }
              }
            })}
          </nav>
        </div>
      </SheetContent>
    </Sheet>
  );
}
