def group_anagrams(words: list[str]) -> list[list[str]]:
    """Groups the words in `words` that are anagrams of each other."""
    groups: dict[str, list[str]] = {}  # sorted letters -> words
    for word in words:
        # Anagrams have the same letters, so sorting them gives the same key.
        key = "".join(sorted(word))
        groups.setdefault(key, []).append(word)
    return list(groups.values())


def canonical(groups: list[list[str]]) -> list[list[str]]:
    """Groups can come back in any order. Sort each group, then sort the groups
    by their first word, so every language prints the same answer."""
    return sorted((sorted(group) for group in groups), key=lambda group: group[0])


if __name__ == "__main__":
    print(canonical(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])))  # [['ate', 'eat', 'tea'], ['bat'], ['nat', 'tan']]
    print(canonical(group_anagrams(["a"])))  # [['a']]
    print(canonical(group_anagrams(["listen", "silent", "enlist", "google"])))  # [['enlist', 'listen', 'silent'], ['google']]
