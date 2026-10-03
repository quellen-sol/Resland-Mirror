import Image from "next/image";
import Link from "next/link";

export interface FooterLink {
  href: string;
  label: string;
}

// Legal pages land here once they exist, e.g.
//   { href: "/privacy", label: "Privacy Policy" },
//   { href: "/terms", label: "Terms of Service" },
const LEGAL_LINKS: FooterLink[] = [];

const HELP_LINK: FooterLink = { href: "/help", label: "Help & FAQ" };

export default function SiteFooter({
  links = [],
}: {
  links?: FooterLink[];
}) {
  return (
    <footer className="relative border-t border-white/[.07] px-6 py-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 text-sm text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Image
            src="/resland-logo.png"
            alt=""
            width={20}
            height={20}
          />
          © {new Date().getFullYear()} Quellen Ventures LLC
        </div>
        <nav className="flex flex-wrap gap-x-4 gap-y-2">
          {[...links, HELP_LINK, ...LEGAL_LINKS].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="hover:text-zinc-200"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
