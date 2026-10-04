// Every topic in the study center, in study order within each category
// (category order comes from DSA_CATEGORIES in lib/dsa.ts). Imports keep the
// .ts extension so node --test can load this file directly.
import type { DsaTopic } from "../../lib/dsa.ts";
import { topic as bigO } from "./big-o/topic.ts";
import { topic as arraysHashing } from "./arrays-hashing/topic.ts";
import { topic as recursion } from "./recursion/topic.ts";
import { topic as twoPointers } from "./two-pointers/topic.ts";
import { topic as slidingWindow } from "./sliding-window/topic.ts";
import { topic as prefixSums } from "./prefix-sums/topic.ts";
import { topic as binarySearch } from "./binary-search/topic.ts";
import { topic as sorting } from "./sorting/topic.ts";
import { topic as intervals } from "./intervals/topic.ts";
import { topic as greedy } from "./greedy/topic.ts";
import { topic as bitManipulation } from "./bit-manipulation/topic.ts";
import { topic as linkedLists } from "./linked-lists/topic.ts";
import { topic as stacksQueues } from "./stacks-queues/topic.ts";
import { topic as monotonicStack } from "./monotonic-stack/topic.ts";
import { topic as binaryTrees } from "./binary-trees/topic.ts";
import { topic as binarySearchTrees } from "./binary-search-trees/topic.ts";
import { topic as heaps } from "./heaps/topic.ts";
import { topic as tries } from "./tries/topic.ts";
import { topic as segmentAndFenwickTrees } from "./segment-and-fenwick-trees/topic.ts";
import { topic as graphTraversal } from "./graph-traversal/topic.ts";
import { topic as topologicalSort } from "./topological-sort/topic.ts";
import { topic as unionFind } from "./union-find/topic.ts";
import { topic as shortestPaths } from "./shortest-paths/topic.ts";
import { topic as minimumSpanningTrees } from "./minimum-spanning-trees/topic.ts";
import { topic as backtracking } from "./backtracking/topic.ts";
import { topic as dp1D } from "./dp-1d/topic.ts";
import { topic as dp2D } from "./dp-2d/topic.ts";
import { topic as dpKnapsack } from "./dp-knapsack/topic.ts";

export const DSA_TOPICS: readonly DsaTopic[] = [
  bigO,
  arraysHashing,
  recursion,
  twoPointers,
  slidingWindow,
  prefixSums,
  binarySearch,
  sorting,
  intervals,
  greedy,
  bitManipulation,
  linkedLists,
  stacksQueues,
  monotonicStack,
  binaryTrees,
  binarySearchTrees,
  heaps,
  tries,
  segmentAndFenwickTrees,
  graphTraversal,
  topologicalSort,
  unionFind,
  shortestPaths,
  minimumSpanningTrees,
  backtracking,
  dp1D,
  dp2D,
  dpKnapsack,
];
