class TrieNode:
    def __init__(self) -> None:
        # One slot per lowercase letter. None means no stored word continues that way.
        self.children: list[TrieNode | None] = [None] * 26
        self.is_word = False  # Whether a stored word ends exactly here.


class Trie:
    """A prefix tree over lowercase words."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            i = ord(ch) - ord("a")
            # Follow the shared prefix. Only create nodes where this word branches off.
            if node.children[i] is None:
                node.children[i] = TrieNode()
            node = node.children[i]
        node.is_word = True

    def search(self, word: str) -> bool:
        # The path has to exist and end on a node marked as a word.
        node = self._walk(word)
        return node is not None and node.is_word

    def starts_with(self, prefix: str) -> bool:
        # Any path at all means some stored word continues it.
        return self._walk(prefix) is not None

    def _walk(self, prefix: str) -> TrieNode | None:
        """The node at the end of `prefix`, or None if no stored word starts with it."""
        node = self.root
        for ch in prefix:
            node = node.children[ord(ch) - ord("a")]
            if node is None:
                return None  # Fell off the trie: nothing continues this way.
        return node


if __name__ == "__main__":
    trie = Trie()
    trie.insert("apple")
    print(trie.search("apple"))  # True
    print(trie.search("app"))  # False
    print(trie.starts_with("app"))  # True
    trie.insert("app")
    print(trie.search("app"))  # True
    print(trie.starts_with("apx"))  # False
