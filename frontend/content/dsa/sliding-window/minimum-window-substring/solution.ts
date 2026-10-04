// Shortest substring of `s` that contains every character of `t`, repeats
// included, or "" if there isn't one.
export function minWindow(s: string, t: string): string {
  // need.get(c) is how many more copies of c the window has to take in.
  // It goes negative when the window holds spares.
  const need = new Map<string, number>();
  for (const c of t) need.set(c, (need.get(c) ?? 0) + 1);
  let missing = t.length; // Characters of t the window still lacks.
  let bestStart = 0;
  let bestLength = s.length + 1; // Longer than any real window.
  let left = 0;
  for (let right = 0; right < s.length; right++) {
    const c = s[right];
    const count = need.get(c) ?? 0;
    if (count > 0) missing--; // This copy was still needed.
    need.set(c, count - 1);
    // The window covers t. Shrink it while it still does, keeping the smallest.
    while (missing === 0) {
      if (right - left + 1 < bestLength) {
        bestStart = left;
        bestLength = right - left + 1;
      }
      const dropped = s[left];
      const dropCount = (need.get(dropped) ?? 0) + 1;
      need.set(dropped, dropCount);
      if (dropCount > 0) missing++; // Dropped a copy the window needed.
      left++;
    }
  }
  return bestLength > s.length ? "" : s.slice(bestStart, bestStart + bestLength);
}

console.log(JSON.stringify(minWindow("ADOBECODEBANC", "ABC"))); // "BANC"
console.log(JSON.stringify(minWindow("a", "aa"))); // ""
console.log(JSON.stringify(minWindow("a", "a"))); // "a"
