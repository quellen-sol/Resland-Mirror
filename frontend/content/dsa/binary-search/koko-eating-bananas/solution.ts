// Slowest whole-number speed that lets Koko eat every pile within `h` hours.
export function minEatingSpeed(piles: number[], h: number): number {
  let lo = 1;
  let hi = Math.max(...piles); // At max(piles) every pile takes one hour.
  while (lo < hi) {
    const mid = lo + Math.floor((hi - lo) / 2);
    if (hoursNeeded(piles, mid) <= h) hi = mid; // Fast enough: the answer is mid or slower.
    else lo = mid + 1; // Too slow, and so is every speed below mid.
  }
  return lo;
}

// Hours to finish every pile at `speed` bananas per hour.
function hoursNeeded(piles: number[], speed: number): number {
  let hours = 0;
  // Round up: a partly eaten pile still costs a whole hour.
  for (const pile of piles) hours += Math.ceil(pile / speed);
  return hours;
}

console.log(minEatingSpeed([3, 6, 7, 11], 8)); // 4
console.log(minEatingSpeed([30, 11, 23, 4, 20], 5)); // 30
console.log(minEatingSpeed([30, 11, 23, 4, 20], 6)); // 23
