class TrieNode {
  // One slot per lowercase letter. null means no stored word continues that way.
  children: (TrieNode | null)[] = new Array<TrieNode | null>(26).fill(null);
  isWord = false; // Whether a stored root ends exactly here.
}

// Adds `word` to the trie rooted at `trie`.
function insert(trie: TrieNode, word: string): void {
  let node = trie;
  for (const ch of word) {
    const i = ch.charCodeAt(0) - "a".charCodeAt(0);
    node = node.children[i] ??= new TrieNode();
  }
  node.isWord = true;
}

// The shortest stored root that `word` starts with, or `word` itself if none does.
function shortestRoot(trie: TrieNode, word: string): string {
  let node = trie;
  for (let i = 0; i < word.length; i++) {
    const child = node.children[word.charCodeAt(i) - "a".charCodeAt(0)];
    if (child === null) return word; // No root continues this way.
    // Prefixes come up shortest first, so the first root found is the answer.
    if (child.isWord) return word.slice(0, i + 1);
    node = child;
  }
  return word; // The whole word is a path, but no root ends on it.
}

// Replaces each word in `sentence` with the shortest root it starts with.
// Words that start with no root stay as they are.
export function replaceWords(roots: string[], sentence: string): string {
  const trie = new TrieNode();
  for (const root of roots) insert(trie, root);
  const words = sentence.split(" ");
  for (let i = 0; i < words.length; i++) words[i] = shortestRoot(trie, words[i]);
  return words.join(" ");
}

console.log(replaceWords(["cat", "bat", "rat"], "the cattle was rattled by the battery")); // the cat was rat by the bat
console.log(replaceWords(["a", "b", "c"], "aadsfasf absbs bbab cadsfafs")); // a a b c
console.log(replaceWords(["car", "ca", "dog"], "cart cab dot")); // ca ca dot
