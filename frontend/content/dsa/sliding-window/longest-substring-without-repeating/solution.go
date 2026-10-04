package main

import "fmt"

// lengthOfLongestSubstring returns the length of the longest substring of s
// with no repeated character.
func lengthOfLongestSubstring(s string) int {
	inWindow := map[byte]bool{}
	left := 0
	best := 0
	for right := 0; right < len(s); right++ {
		c := s[right]
		// A repeat breaks the window, and growing it can't fix that.
		// Drop characters from the left until the earlier copy of c is gone.
		for inWindow[c] {
			delete(inWindow, s[left])
			left++
		}
		inWindow[c] = true
		best = max(best, right-left+1)
	}
	return best
}

func main() {
	fmt.Println(lengthOfLongestSubstring("abcabcbb")) // 3
	fmt.Println(lengthOfLongestSubstring("bbbbb"))    // 1
	fmt.Println(lengthOfLongestSubstring("pwwkew"))   // 3
	fmt.Println(lengthOfLongestSubstring(""))         // 0
}
