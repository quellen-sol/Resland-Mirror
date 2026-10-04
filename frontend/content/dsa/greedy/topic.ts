import type { DsaTopic } from "../../../lib/dsa.ts";

export const topic: DsaTopic = {
  slug: "greedy",
  title: "Greedy Algorithms",
  seoTitle: "Greedy Algorithms Explained: Jump Game and Gas Station",
  category: "techniques",
  level: "INTERMEDIATE",
  summary:
    "Commit to the choice that looks best at each step and never revisit it. Fast and simple, but only correct when you can prove that choice is safe.",
  prerequisites: ["arrays-hashing"],
  overview: [
    {
      type: "p",
      text: "A greedy algorithm builds its answer one step at a time. At each step it commits to whatever looks best right now and never goes back. When that's correct, it's usually the simplest solution there is. Most greedy solutions take one of two shapes: sort the input so the best candidate comes first and take what fits, or make one pass while tracking a single running value, such as the farthest index you can reach.",
    },
    {
      type: "p",
      text: "Greedy is safe when the problem has the **greedy-choice property**: some optimal answer starts with the greedy choice, and what's left afterwards is a smaller copy of the same problem. You show it with an exchange argument. Take any optimal answer that disagrees with greedy's first choice, swap greedy's choice in, and check that the result is still valid and no worse. If that swap always works, greedy never loses.",
    },
    {
      type: "p",
      text: "For example, to fit the most non-overlapping meetings into one room, keep taking the meeting that ends first among those that don't clash with the ones you've already taken. Whatever meeting an optimal schedule starts with, you can swap in the earliest-ending one instead. It ends no later, so it can't run into any meeting the schedule had after it. The [Intervals](/dsa/intervals) topic uses the same rule.",
    },
    {
      type: "p",
      text: "Greedy fails when the best move now leaves you worse off later. Coin change is the classic trap. With coins `[1, 3, 4]` and amount `6`, taking the largest coin that fits gives `4 + 1 + 1`, three coins, while `3 + 3` needs only two. With US coins (1, 5, 10 and 25 cents) the same rule happens to work, which is exactly why it's tempting.",
    },
    {
      type: "diagram",
      text: "coins = [1, 3, 4], amount = 6\n\ngreedy   4 + 1 + 1   3 coins\noptimal  3 + 3       2 coins",
      caption: "Taking the 4 first leaves 2, which only two 1s can pay.",
    },
    {
      type: "p",
      text: "When a counterexample like that exists, you have to compare the choices instead of trusting one, which is what [Dynamic Programming: 1D](/dsa/dp-1d) does for coin change. Before you trust a greedy rule, spend a minute hunting for a small input that breaks it. If you can't find one, try to write the exchange argument.",
    },
  ],
  signals: [
    "The question asks for a minimum or maximum, like the fewest jumps or the most meetings, and one move looks clearly best at each step.",
    "Sorting by a single key, such as end time, deadline or size, makes every decision easy.",
    "The input is large (100,000 items or more), so an O(n²) dynamic program won't fit, but a single pass would.",
    "You only need one running value, like the farthest point reached or a running balance, rather than every possible state.",
  ],
  complexity: [
    { operation: "One pass with a running value (Jump Game, Gas Station)", time: "O(n)", space: "O(1)" },
    { operation: "Sort, then one pass (most non-overlapping meetings)", time: "O(n log n)", space: "O(1) to O(n), depending on the sort" },
    { operation: "Repeatedly take the best item from a heap", time: "O(n log n)", space: "O(n)" },
  ],
  template: {
    id: "jump-game",
    title: "Jump Game",
    explanation: [
      {
        type: "p",
        text: "Given `nums`, where `nums[i]` is the longest jump you can make from index `i`, can you get from index `0` to the last index? You don't need to decide which jump to take. Track `farthest`, the farthest index any jump so far can reach. Every index up to `farthest` is reachable too, because a jump from `i` can land anywhere from `i + 1` to `i + nums[i]`, not just at the end.",
      },
      {
        type: "p",
        text: "So walk left to right and extend `farthest` with `i + nums[i]`. If you ever stand on an index past `farthest`, nothing before it can reach it, and the answer is `false`. If the loop finishes, every index was reachable.",
      },
      {
        type: "tip",
        text: "This is LeetCode 55. A DP that marks each index reachable or not also works, but it checks every jump from every index, which is O(n²) in the worst case. The greedy version keeps one number instead of an array.",
      },
    ],
    time: "O(n)",
    space: "O(1)",
  },
  problems: [
    {
      id: "jump-game-ii",
      title: "Jump Game II",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Same setup as Jump Game: `nums[i]` is the longest jump you can make from index `i`, and you start at index `0`. This time the last index is always reachable. Return the fewest jumps it takes to get there.",
        },
        {
          type: "p",
          text: "Example: `[2, 3, 1, 1, 4]` returns `2`. Jump 1 step to index 1, then 3 steps to the last index.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Think of it as a [breadth-first search](/dsa/graph-traversal) over ranges of indices. With 0 jumps you can only stand at index 0. With 1 jump you can reach any index up to `nums[0]`. With each further jump, you can reach anything up to the farthest point the previous range can jump to. Count ranges until one covers the last index.",
        },
        {
          type: "diagram",
          text: "index    0  1  2  3  4\nnums     2  3  1  1  4\n\n0 jumps  0\n1 jump      1  2\n2 jumps           3  4",
          caption: "Each row holds the indices you first reach with that many jumps.",
        },
        {
          type: "p",
          text: "In the code, `currentEnd` is the end of the current range and `farthest` is the end of the next one, built up as you scan. When `i` reaches `currentEnd`, you've seen everything this many jumps can reach, so you take another jump and the next range begins. The loop stops before the last index, because standing on it means you've arrived. If it ran one step further, it would count an extra jump whenever a range ends exactly on the last index.",
        },
      ],
      time: "O(n)",
      space: "O(1)",
      link: {
        label: "LeetCode 45",
        url: "https://leetcode.com/problems/jump-game-ii/",
      },
    },
    {
      id: "gas-station",
      title: "Gas Station",
      difficulty: "MEDIUM",
      statement: [
        {
          type: "p",
          text: "Gas stations sit on a circular road. Station `i` has `gas[i]` fuel to pick up, and driving from station `i` to the next one burns `cost[i]`. Your tank starts empty and has no limit. Return the station to start from so you can drive all the way around once, or `-1` if no start works. When an answer exists, it's unique.",
        },
        {
          type: "p",
          text: "Example: `gas = [1, 2, 3, 4, 5]` and `cost = [3, 4, 5, 1, 2]` returns `3`. Starting at station 3, you pick up 4 and burn 1, leaving 3, and the tank never goes negative on the way around.",
        },
      ],
      explanation: [
        {
          type: "p",
          text: "Trying every start and simulating the loop is O(n²). Two observations bring it down to one pass:",
        },
        {
          type: "list",
          ordered: true,
          items: [
            "If the total gas is less than the total cost, no start can work, because the loop as a whole burns more than it gets. Otherwise some start does work, and the next point finds it.",
            "Drive from `start` and keep a running `tank`. If it drops below zero on the way to station `i + 1`, then `start` fails, and so does every station between `start` and `i`. You reached each of them with zero or more fuel, so starting there with an empty tank can only leave you worse off. Skip them all and try `i + 1`.",
          ],
        },
        {
          type: "diagram",
          text: "station      0   1   2   3   4\ngas - cost  -2  -2  -2  +3  +3\ntank        -2  -2  -2   3   6\nstart        1   2   3   3   3",
          caption: "The tank goes negative at stations 0, 1 and 2, so the start moves past each one and the tank resets. The total is 0, so station 3 works.",
        },
        {
          type: "p",
          text: "Why does the last candidate work? The stretch from it to the end of the array never ran dry, and every stretch before it ended in a deficit. A total of zero or more means the fuel you carry past the end is enough to cover those deficits as you wrap around.",
        },
      ],
      time: "O(n)",
      space: "O(1)",
      link: {
        label: "LeetCode 134",
        url: "https://leetcode.com/problems/gas-station/",
      },
    },
  ],
  pitfalls: [
    "Trusting a greedy rule because it passed the examples. Try small inputs where the best move now blocks a better one later, as coins `[1, 3, 4]` with amount `6` do.",
    "Sorting by the wrong key. To keep the most non-overlapping intervals, sort by end time. Sorting by start or by length can lock in a bad pick early.",
    "Assuming greedy means taking the biggest value. The safe choice is whatever an exchange argument supports, like the earliest end time, and often it isn't the largest anything.",
    "In Jump Game II, looping all the way to the last index. If a range ends exactly there, you count a jump you never take.",
    "In Gas Station, retrying from `start + 1` after running dry instead of jumping to `i + 1`. It still finds the answer, but it rechecks stations already ruled out and becomes O(n²).",
  ],
  practice: [
    { title: "Assign Cookies", url: "https://leetcode.com/problems/assign-cookies/", difficulty: "EASY" },
    { title: "Lemonade Change", url: "https://leetcode.com/problems/lemonade-change/", difficulty: "EASY" },
    { title: "Best Time to Buy and Sell Stock II", url: "https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/", difficulty: "MEDIUM" },
    { title: "Partition Labels", url: "https://leetcode.com/problems/partition-labels/", difficulty: "MEDIUM" },
    { title: "Hand of Straights", url: "https://leetcode.com/problems/hand-of-straights/", difficulty: "MEDIUM" },
    { title: "Candy", url: "https://leetcode.com/problems/candy/", difficulty: "HARD" },
  ],
};
