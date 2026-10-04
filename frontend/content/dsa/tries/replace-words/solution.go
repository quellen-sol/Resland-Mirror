package main

import (
	"fmt"
	"strings"
)

// TrieNode is one node of a trie.
type TrieNode struct {
	// One slot per lowercase letter. nil means no stored word continues that way.
	children [26]*TrieNode
	isWord   bool // Whether a stored root ends exactly here.
}

// insert adds word to the trie rooted at trie.
func insert(trie *TrieNode, word string) {
	node := trie
	for _, ch := range word {
		i := ch - 'a'
		if node.children[i] == nil {
			node.children[i] = &TrieNode{}
		}
		node = node.children[i]
	}
	node.isWord = true
}

// shortestRoot returns the shortest stored root that word starts with, or
// word itself if none does.
func shortestRoot(trie *TrieNode, word string) string {
	node := trie
	for i := 0; i < len(word); i++ {
		child := node.children[word[i]-'a']
		if child == nil {
			return word // No root continues this way.
		}
		// Prefixes come up shortest first, so the first root found is the answer.
		if child.isWord {
			return word[:i+1]
		}
		node = child
	}
	return word // The whole word is a path, but no root ends on it.
}

// replaceWords replaces each word in sentence with the shortest root it
// starts with. Words that start with no root stay as they are.
func replaceWords(roots []string, sentence string) string {
	trie := &TrieNode{}
	for _, root := range roots {
		insert(trie, root)
	}
	words := strings.Split(sentence, " ")
	for i := range words {
		words[i] = shortestRoot(trie, words[i])
	}
	return strings.Join(words, " ")
}

func main() {
	fmt.Println(replaceWords([]string{"cat", "bat", "rat"}, "the cattle was rattled by the battery")) // the cat was rat by the bat
	fmt.Println(replaceWords([]string{"a", "b", "c"}, "aadsfasf absbs bbab cadsfafs"))                // a a b c
	fmt.Println(replaceWords([]string{"car", "ca", "dog"}, "cart cab dot"))                           // ca ca dot
}
