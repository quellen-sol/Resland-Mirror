package main

import "fmt"

// TrieNode is one node of a trie.
type TrieNode struct {
	// One slot per lowercase letter. nil means no stored word continues that way.
	children [26]*TrieNode
	isWord   bool // Whether a stored word ends exactly here.
}

// WordDictionary stores words and finds them by pattern, where "." matches
// any one letter.
type WordDictionary struct {
	root *TrieNode
}

func newWordDictionary() *WordDictionary {
	return &WordDictionary{root: &TrieNode{}}
}

func (d *WordDictionary) addWord(word string) {
	node := d.root
	for _, ch := range word {
		i := ch - 'a'
		if node.children[i] == nil {
			node.children[i] = &TrieNode{}
		}
		node = node.children[i]
	}
	node.isWord = true
}

func (d *WordDictionary) search(pattern string) bool {
	return d.match(d.root, pattern, 0)
}

// match reports whether some stored word below node matches pattern from
// index i on.
func (d *WordDictionary) match(node *TrieNode, pattern string, i int) bool {
	// The pattern is used up, so it only matches if a word ends right here.
	if i == len(pattern) {
		return node.isWord
	}
	if pattern[i] == '.' {
		// A dot can be any letter, so try every branch that exists.
		for _, branch := range node.children {
			if branch != nil && d.match(branch, pattern, i+1) {
				return true
			}
		}
		return false
	}
	child := node.children[pattern[i]-'a']
	return child != nil && d.match(child, pattern, i+1)
}

func main() {
	dictionary := newWordDictionary()
	for _, word := range []string{"bad", "dad", "mad"} {
		dictionary.addWord(word)
	}
	fmt.Println(dictionary.search("pad")) // false
	fmt.Println(dictionary.search("bad")) // true
	fmt.Println(dictionary.search(".ad")) // true
	fmt.Println(dictionary.search("b..")) // true
	fmt.Println(dictionary.search("b."))  // false
}
