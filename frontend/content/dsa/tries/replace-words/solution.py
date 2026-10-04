class TrieNode:
    def __init__(self) -> None:
        # One slot per lowercase letter. None means no stored word continues that way.
        self.children: list[TrieNode | None] = [None] * 26
        self.is_word = False  # Whether a stored root ends exactly here.


def insert(trie: TrieNode, word: str) -> None:
    """Adds `word` to the trie rooted at `trie`."""
    node = trie
    for ch in word:
        i = ord(ch) - ord("a")
        if node.children[i] is None:
            node.children[i] = TrieNode()
        node = node.children[i]
    node.is_word = True


def shortest_root(trie: TrieNode, word: str) -> str:
    """The shortest stored root that `word` starts with, or `word` itself if none does."""
    node = trie
    for i in range(len(word)):
        child = node.children[ord(word[i]) - ord("a")]
        if child is None:
            return word  # No root continues this way.
        # Prefixes come up shortest first, so the first root found is the answer.
        if child.is_word:
            return word[: i + 1]
        node = child
    return word  # The whole word is a path, but no root ends on it.


def replace_words(roots: list[str], sentence: str) -> str:
    """Replaces each word in `sentence` with the shortest root it starts with.
    Words that start with no root stay as they are."""
    trie = TrieNode()
    for root in roots:
        insert(trie, root)
    words = sentence.split(" ")
    for i in range(len(words)):
        words[i] = shortest_root(trie, words[i])
    return " ".join(words)


if __name__ == "__main__":
    print(replace_words(["cat", "bat", "rat"], "the cattle was rattled by the battery"))  # the cat was rat by the bat
    print(replace_words(["a", "b", "c"], "aadsfasf absbs bbab cadsfafs"))  # a a b c
    print(replace_words(["car", "ca", "dog"], "cart cab dot"))  # ca ca dot
