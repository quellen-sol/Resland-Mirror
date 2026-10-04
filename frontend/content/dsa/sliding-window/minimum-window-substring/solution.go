package main

import "fmt"

// minWindow returns the shortest substring of s that contains every character
// of t, repeats included, or "" if there isn't one.
func minWindow(s, t string) string {
	// need[c] is how many more copies of c the window has to take in.
	// It goes negative when the window holds spares.
	need := map[byte]int{}
	for i := 0; i < len(t); i++ {
		need[t[i]]++
	}
	missing := len(t) // Characters of t the window still lacks.
	bestStart := 0
	bestLength := len(s) + 1 // Longer than any real window.
	left := 0
	for right := 0; right < len(s); right++ {
		c := s[right]
		if need[c] > 0 {
			missing-- // This copy was still needed.
		}
		need[c]--
		// The window covers t. Shrink it while it still does, keeping the smallest.
		for missing == 0 {
			if right-left+1 < bestLength {
				bestStart = left
				bestLength = right - left + 1
			}
			dropped := s[left]
			need[dropped]++
			if need[dropped] > 0 {
				missing++ // Dropped a copy the window needed.
			}
			left++
		}
	}
	if bestLength > len(s) {
		return ""
	}
	return s[bestStart : bestStart+bestLength]
}

func main() {
	fmt.Printf("%q\n", minWindow("ADOBECODEBANC", "ABC")) // "BANC"
	fmt.Printf("%q\n", minWindow("a", "aa"))              // ""
	fmt.Printf("%q\n", minWindow("a", "a"))               // "a"
}
