import { DSA_TOPICS } from "@/content/dsa/index.ts";
import { groupTopicsByCategory, orderTopics, toTopicRef } from "@/lib/dsa";
import TopicNav from "../topic-nav";

// A layout rather than part of the page so the sidebar (and its scroll
// position) stays put while you move between topics.
export default function TopicLayout({ children }: { children: React.ReactNode }) {
  const groups = groupTopicsByCategory(orderTopics(DSA_TOPICS).map(toTopicRef));
  return (
    <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 pt-4 pb-16 lg:flex-row lg:gap-10">
      <TopicNav groups={groups} />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
