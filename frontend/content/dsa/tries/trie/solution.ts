class TrieNode {
  // One slot per lowercase letter. null means no stored word continues that way.
  children: (TrieNode | null)[] = new Array<TrieNode | null>(26).fill(null);
  isWord = false; // Whether a stored word ends exactly here.
}

// A prefix tree over lowercase words.
export class Trie {
  root = new TrieNode();

  insert(word: string): void {
    let node = this.root;
    for (const ch of word) {
      const i = ch.charCodeAt(0) - "a".charCodeAt(0);
      // Follow the shared prefix. Only create nodes where this word branches off.
      node = node.children[i] ??= new TrieNode();
    }
    node.isWord = true;
  }

  search(word: string): boolean {
    // The path has to exist and end on a node marked as a word.
    const node = this.walk(word);
    return node !== null && node.isWord;
  }

  startsWith(prefix: string): boolean {
    // Any path at all means some stored word continues it.
    return this.walk(prefix) !== null;
  }

  // The node at the end of `prefix`, or null if no stored word starts with it.
  private walk(prefix: string): TrieNode | null {
    let node: TrieNode | null = this.root;
    for (const ch of prefix) {
      node = node.children[ch.charCodeAt(0) - "a".charCodeAt(0)];
      if (node === null) return null; // Fell off the trie: nothing continues this way.
    }
    return node;
  }
}

const trie = new Trie();
trie.insert("apple");
console.log(trie.search("apple")); // true
console.log(trie.search("app")); // false
console.log(trie.startsWith("app")); // true
trie.insert("app");
console.log(trie.search("app")); // true
console.log(trie.startsWith("apx")); // false
