// Groups the words in words that are anagrams of each other.
export function groupAnagrams(words: string[]): string[][] {
  const groups = new Map<string, string[]>(); // sorted letters -> words
  for (const word of words) {
    // Anagrams have the same letters, so sorting them gives the same key.
    const key = [...word].sort().join("");
    const group = groups.get(key);
    if (group) group.push(word);
    else groups.set(key, [word]);
  }
  return [...groups.values()];
}

// Groups can come back in any order. Sort each group, then sort the groups by
// their first word, so every language prints the same answer.
function canonical(groups: string[][]): string[][] {
  for (const group of groups) group.sort();
  return groups.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
}

console.log(JSON.stringify(canonical(groupAnagrams(["eat", "tea", "tan", "ate", "nat", "bat"])))); // [["ate","eat","tea"],["bat"],["nat","tan"]]
console.log(JSON.stringify(canonical(groupAnagrams(["a"])))); // [["a"]]
console.log(JSON.stringify(canonical(groupAnagrams(["listen", "silent", "enlist", "google"])))); // [["enlist","listen","silent"],["google"]]
