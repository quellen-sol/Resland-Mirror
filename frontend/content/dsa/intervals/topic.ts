import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "intervals",
  title: "Intervals",
  seoTitle: "Interval Problems: Merge, Insert and Meeting Rooms",
  category: "techniques",
  level: "INTERMEDIATE",
  summary:
    "Sort ranges by their start so overlaps sit side by side, then merge, insert or count them in a single pass.",
  prerequisites: ["sorting"],
  overview: [
    {
      type: "p",
      text: "An interval is a pair `[start, end]`: a meeting, a booking, a range of numbers. Interval problems ask you to merge the ones that overlap, slot a new one in, or count how many are active at once. Comparing every pair with every other works, but it costs O(n²).",
    },
    {
      type: "p",
      text: "**Sort by start** and the problem becomes local. Walk the intervals in order while you build one merged block at a time. The next interval can only overlap the block you're building: every finished block ended before this block began, and the next interval starts no earlier than this block did.",
    },
    {
      type: "diagram",
      text: "         0    5    10   15\n         |    |    |    |\n[1,3]     ===\n[2,6]      =====\n[8,10]           ===\n[15,18]                 ====\n\nmerged    ====== ===    ====",
      caption: "Sorted by start, each interval either overlaps the block being built or starts a new one.",
    },
    {
      type: "p",
      text: "Two intervals `[a, b]` and `[c, d]` overlap when `a <= d` and `c <= b`. Once they're sorted so that `a <= c`, the first half always holds, which leaves one check: does the next interval start before the current block ends? Whether touching counts depends on the problem. Merge Intervals treats `[1, 4]` and `[4, 5]` as overlapping, so it uses `<=`. Two meetings at those times don't clash, because the first ends as the second starts.",
    },
    {
      type: "p",
      text: "The common shapes:",
    },
    {
      type: "list",
      items: [
        "**Merge.** Sort by start and keep extending the current block while the next interval overlaps it. That's the template below.",
        "**Insert.** When the list is already sorted and overlap-free, skip the sort: copy what comes before the new interval, absorb what overlaps it, copy what comes after. That's O(n).",
        "**Count overlaps.** Sort the start times and end times separately and sweep through them in time order. The most intervals active at once answers meeting rooms, car pooling and similar questions.",
        "**Keep the most.** To keep as many non-overlapping intervals as possible, sort by end and keep taking the next one that starts after the last one you kept ends. Finishing as early as possible leaves the most room for the rest, which is a [greedy](/dsa/greedy) choice.",
      ],
    },
  ],
  signals: [
    "The input is a list of `[start, end]` pairs: meetings, bookings, time slots or number ranges.",
    "The question asks you to merge, insert or remove overlapping ranges.",
    "You need the most things happening at the same moment: rooms, platforms, servers, passengers in a car.",
    "You need the gaps between ranges, such as the free time in a calendar.",
  ],
  complexity: [
    { operation: "Sort by start", time: "O(n log n)", space: "O(1) to O(n), depending on the sort" },
    { operation: "Merge after sorting", time: "O(n)", space: "O(n) for the output" },
    { operation: "Insert into a sorted, overlap-free list", time: "O(n)", space: "O(n) for the output" },
    { operation: "Most intervals active at once", time: "O(n log n)", space: "O(n)" },
  ],
  template: {
    id: "merge-intervals",
    title: "Merge Intervals",
    explanation: [
      {
        type: "p",
        text: "Sort a copy of the intervals by start, then walk it while building the result. If the next interval starts at or before the end of the last merged block, the two overlap, so extend that block. Otherwise there's a gap, and the interval starts a new block. After the sort, each interval is handled once, so the sort dominates the running time.",
      },
      {
        type: "tip",
        text: "Extend the block to the **larger** of the two ends, not to the new interval's end. A short interval can sit entirely inside a long one: `[1, 10]` followed by `[2, 3]` must stay `[1, 10]`, which is the third case in the demo.",
      },
    ],
    time: "O(n log n)",
    space: "O(n)",
  },
  problems: [
    {
      id: "insert-interval",
      title: "Insert Interval",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "You're given a list of intervals that don't overlap and are sorted by start, plus one new interval. Add the new interval, merging it with anything it overlaps, so the result is still sorted and overlap-free.",
        },
        {
          type: "p",
          text: "Example: inserting `[4, 8]` into `[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]]` returns `[[1, 2], [3, 10], [12, 16]]`. The new interval swallows `[3, 5]`, `[6, 7]` and `[8, 10]`.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "You could append it and run Merge Intervals, but that sorts a list that's already sorted. Because the list is in order, it splits into three runs, and one pass handles each:",
        },
        {
          type: "list",
          ordered: true,
          items: [
            "Intervals that end before the new one starts can't touch it. Copy them over unchanged.",
            "Intervals that start at or before the new one's end overlap it. Absorb each one by widening the new interval to the smaller start and the larger end.",
            "Add the widened interval, then copy everything that's left. All of it starts after the widened interval ends.",
          ],
        },
        {
          type: "p",
          text: "The checks match the merge template, where touching counts as overlapping. That's why the first run uses a strict `<` and the second uses `<=`. Every interval is visited once, so the whole thing is O(n).",
        },
      ],
      time: "O(n)",
      space: "O(n) for the output",
      link: {
        label: "LeetCode 57",
        url: "https://leetcode.com/problems/insert-interval/",
      },
    },
    {
      id: "meeting-rooms-ii",
      title: "Meeting Rooms II",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Each meeting is a pair `[start, end]` with `start < end`. Find the fewest conference rooms that can host all of them. A room is free the moment its meeting ends, so a meeting that ends at `10` and one that starts at `10` can share it.",
        },
        {
          type: "p",
          text: "Example: `[[0, 30], [5, 10], [15, 20]]` returns `2`. The long meeting needs a room the whole time, and the other two take turns in a second one.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "The answer is the largest number of meetings running at the same moment. You need at least that many rooms, and that many is enough, because a room that frees up can go to any meeting that starts later.",
        },
        {
          type: "diagram",
          text: "time     0    5    10   15   20   25   30\n[0,30]   ==============================\n[5,10]        =====\n[15,20]                 =====\nrooms    1    2    1    2    1         0",
          caption: "Rooms in use after each start or end. It never goes above two.",
        },
        {
          type: "p",
          text: "To find that peak, sort the start times and the end times **separately**, then walk the starts in order. Before each start, release every meeting that has ended by then, and then give the new meeting a room. The count of rooms in use rises and falls exactly as it does on the timeline, and its highest point is the answer. Splitting starts from ends is safe because you only ever count how many meetings are running, never which ones.",
        },
        {
          type: "tip",
          text: "A min-heap of end times works too. Sort the meetings by start, and for each one, pop the earliest end if that meeting is already over, then push this meeting's end. The heap never shrinks, so its final size is the answer. See [Heaps & Priority Queues](/dsa/heaps).",
        },
      ],
      time: "O(n log n)",
      space: "O(n)",
      link: {
        label: "LintCode 919",
        url: "https://www.lintcode.com/problem/919/",
      },
    },
  ],
  pitfalls: [
    "Scanning without sorting first. The one-pass merge only works because sorting by start puts every overlap right next to the block it joins.",
    "Setting the merged end to the new interval's end instead of the larger of the two. `[1, 10]` followed by `[2, 3]` would shrink to `[1, 3]`.",
    "Comparing each interval with the previous input interval instead of the merged block. In `[1, 10], [2, 3], [4, 5]`, the last one doesn't overlap `[2, 3]`, but it does overlap `[1, 10]`.",
    "Getting the boundary wrong. Decide whether touching intervals like `[1, 4]` and `[4, 5]` overlap in this problem, then use `<=` or `<` to match.",
  ],
  practice: [
    { title: "Teemo Attacking", url: "https://leetcode.com/problems/teemo-attacking/", difficulty: "EASY" },
    { title: "Non-overlapping Intervals", url: "https://leetcode.com/problems/non-overlapping-intervals/", difficulty: "MEDIUM" },
    { title: "Minimum Number of Arrows to Burst Balloons", url: "https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/", difficulty: "MEDIUM" },
    { title: "Interval List Intersections", url: "https://leetcode.com/problems/interval-list-intersections/", difficulty: "MEDIUM" },
    { title: "Car Pooling", url: "https://leetcode.com/problems/car-pooling/", difficulty: "MEDIUM" },
    { title: "Minimum Interval to Include Each Query", url: "https://leetcode.com/problems/minimum-interval-to-include-each-query/", difficulty: "HARD" },
  ],
};
