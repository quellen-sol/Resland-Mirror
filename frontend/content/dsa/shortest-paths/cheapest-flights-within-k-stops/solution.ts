// Cheapest price from src to dst using at most k stops (so at most k + 1
// flights), where each flight is [u, v, price]. -1 if no such route exists.
export function findCheapestPrice(n: number, flights: number[][], src: number, dst: number, k: number): number {
  let prices = new Array<number>(n).fill(Infinity);
  prices[src] = 0;
  // After round i, prices[v] is the cheapest way to reach v in at most i flights.
  for (let round = 1; round <= k + 1; round++) {
    // Read last round's prices and write into a copy. Updating in place would let
    // one round chain several flights and slip past the stop limit.
    const nextPrices = [...prices];
    for (const [u, v, price] of flights) {
      // Only fly out of cities an earlier round already reached.
      if (prices[u] !== Infinity && prices[u] + price < nextPrices[v]) {
        nextPrices[v] = prices[u] + price;
      }
    }
    prices = nextPrices;
  }
  return prices[dst] === Infinity ? -1 : prices[dst];
}

console.log(findCheapestPrice(4, [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]], 0, 3, 1)); // 700
console.log(findCheapestPrice(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1)); // 200
console.log(findCheapestPrice(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0)); // 500
console.log(findCheapestPrice(3, [[0, 1, 100], [1, 2, 100]], 0, 2, 0)); // -1
