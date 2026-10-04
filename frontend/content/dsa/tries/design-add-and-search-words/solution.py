class TrieNode:
    def __init__(self) -> None:
        # One slot per lowercase letter. None means no stored word continues that way.
        self.children: list[TrieNode | None] = [None] * 26
        self.is_word = False  # Whether a stored word ends exactly here.


class WordDictionary:
    """Stores words and finds them by pattern, where "." matches any one letter."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def add_word(self, word: str) -> None:
        node = self.root
        for ch in word:
            i = ord(ch) - ord("a")
            if node.children[i] is None:
                node.children[i] = TrieNode()
            node = node.children[i]
        node.is_word = True

    def search(self, pattern: str) -> bool:
        return self._match(self.root, pattern, 0)

    def _match(self, node: TrieNode, pattern: str, i: int) -> bool:
        """Whether some stored word below `node` matches `pattern` from index `i` on."""
        # The pattern is used up, so it only matches if a word ends right here.
        if i == len(pattern):
            return node.is_word
        if pattern[i] == ".":
            # A dot can be any letter, so try every branch that exists.
            for branch in node.children:
                if branch is not None and self._match(branch, pattern, i + 1):
                    return True
            return False
        child = node.children[ord(pattern[i]) - ord("a")]
        return child is not None and self._match(child, pattern, i + 1)


if __name__ == "__main__":
    dictionary = WordDictionary()
    for word in ["bad", "dad", "mad"]:
        dictionary.add_word(word)
    print(dictionary.search("pad"))  # False
    print(dictionary.search("bad"))  # True
    print(dictionary.search(".ad"))  # True
    print(dictionary.search("b.."))  # True
    print(dictionary.search("b."))  # False
