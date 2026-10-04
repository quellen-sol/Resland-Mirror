class TrieNode {
  // One slot per lowercase letter. null means no stored word continues that way.
  children: (TrieNode | null)[] = new Array<TrieNode | null>(26).fill(null);
  isWord = false; // Whether a stored word ends exactly here.
}

// Stores words and finds them by pattern, where "." matches any one letter.
export class WordDictionary {
  root = new TrieNode();

  addWord(word: string): void {
    let node = this.root;
    for (const ch of word) {
      const i = ch.charCodeAt(0) - "a".charCodeAt(0);
      node = node.children[i] ??= new TrieNode();
    }
    node.isWord = true;
  }

  search(pattern: string): boolean {
    return this.match(this.root, pattern, 0);
  }

  // Whether some stored word below `node` matches `pattern` from index `i` on.
  private match(node: TrieNode, pattern: string, i: number): boolean {
    // The pattern is used up, so it only matches if a word ends right here.
    if (i === pattern.length) return node.isWord;
    if (pattern[i] === ".") {
      // A dot can be any letter, so try every branch that exists.
      for (const branch of node.children) {
        if (branch !== null && this.match(branch, pattern, i + 1)) return true;
      }
      return false;
    }
    const child = node.children[pattern.charCodeAt(i) - "a".charCodeAt(0)];
    return child !== null && this.match(child, pattern, i + 1);
  }
}

const dictionary = new WordDictionary();
for (const word of ["bad", "dad", "mad"]) dictionary.addWord(word);
console.log(dictionary.search("pad")); // false
console.log(dictionary.search("bad")); // true
console.log(dictionary.search(".ad")); // true
console.log(dictionary.search("b..")); // true
console.log(dictionary.search("b.")); // false
