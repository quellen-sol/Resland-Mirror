package main

import (
	"fmt"
	"slices"
	"strings"
)

// groupAnagrams groups the words in words that are anagrams of each other.
func groupAnagrams(words []string) [][]string {
	groups := map[string][]string{} // sorted letters -> words
	for _, word := range words {
		// Anagrams have the same letters, so sorting them gives the same key.
		letters := []byte(word)
		slices.Sort(letters)
		key := string(letters)
		groups[key] = append(groups[key], word)
	}
	result := [][]string{}
	for _, group := range groups {
		result = append(result, group)
	}
	return result
}

// canonical sorts each group, then sorts the groups by their first word.
// Groups can come back in any order, and this makes every language print the
// same answer.
func canonical(groups [][]string) [][]string {
	for _, group := range groups {
		slices.Sort(group)
	}
	slices.SortFunc(groups, func(a, b []string) int { return strings.Compare(a[0], b[0]) })
	return groups
}

func main() {
	fmt.Println(canonical(groupAnagrams([]string{"eat", "tea", "tan", "ate", "nat", "bat"}))) // [[ate eat tea] [bat] [nat tan]]
	fmt.Println(canonical(groupAnagrams([]string{"a"})))                                      // [[a]]
	fmt.Println(canonical(groupAnagrams([]string{"listen", "silent", "enlist", "google"})))   // [[enlist listen silent] [google]]
}
