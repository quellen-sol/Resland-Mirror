// Length of the longest substring of `s` with no repeated character.
export function lengthOfLongestSubstring(s: string): number {
  const inWindow = new Set<string>();
  let left = 0;
  let best = 0;
  for (let right = 0; right < s.length; right++) {
    const c = s[right];
    // A repeat breaks the window, and growing it can't fix that.
    // Drop characters from the left until the earlier copy of c is gone.
    while (inWindow.has(c)) {
      inWindow.delete(s[left]);
      left++;
    }
    inWindow.add(c);
    best = Math.max(best, right - left + 1);
  }
  return best;
}

console.log(lengthOfLongestSubstring("abcabcbb")); // 3
console.log(lengthOfLongestSubstring("bbbbb")); // 1
console.log(lengthOfLongestSubstring("pwwkew")); // 3
console.log(lengthOfLongestSubstring("")); // 0
