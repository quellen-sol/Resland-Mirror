package main

import "fmt"

// TrieNode is one node of a trie.
type TrieNode struct {
	// One slot per lowercase letter. nil means no stored word continues that way.
	children [26]*TrieNode
	isWord   bool // Whether a stored word ends exactly here.
}

// Trie is a prefix tree over lowercase words.
type Trie struct {
	root *TrieNode
}

func newTrie() *Trie {
	return &Trie{root: &TrieNode{}}
}

func (t *Trie) insert(word string) {
	node := t.root
	for _, ch := range word {
		i := ch - 'a'
		// Follow the shared prefix. Only create nodes where this word branches off.
		if node.children[i] == nil {
			node.children[i] = &TrieNode{}
		}
		node = node.children[i]
	}
	node.isWord = true
}

func (t *Trie) search(word string) bool {
	// The path has to exist and end on a node marked as a word.
	node := t.walk(word)
	return node != nil && node.isWord
}

func (t *Trie) startsWith(prefix string) bool {
	// Any path at all means some stored word continues it.
	return t.walk(prefix) != nil
}

// walk returns the node at the end of prefix, or nil if no stored word starts
// with it.
func (t *Trie) walk(prefix string) *TrieNode {
	node := t.root
	for _, ch := range prefix {
		node = node.children[ch-'a']
		if node == nil {
			return nil // Fell off the trie: nothing continues this way.
		}
	}
	return node
}

func main() {
	trie := newTrie()
	trie.insert("apple")
	fmt.Println(trie.search("apple"))   // true
	fmt.Println(trie.search("app"))     // false
	fmt.Println(trie.startsWith("app")) // true
	trie.insert("app")
	fmt.Println(trie.search("app"))     // true
	fmt.Println(trie.startsWith("apx")) // false
}
