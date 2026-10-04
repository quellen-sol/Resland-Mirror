// The station to start from to drive once around the loop, or -1 if none
// works. gas[i] is the fuel at station i, and cost[i] is the fuel it takes to
// drive from station i to the next one.
export function startingStation(gas: number[], cost: number[]): number {
  let total = 0; // Net fuel over the whole loop.
  let tank = 0; // Fuel left since leaving start.
  let start = 0;
  for (let i = 0; i < gas.length; i++) {
    total += gas[i] - cost[i];
    tank += gas[i] - cost[i];
    if (tank < 0) {
      // Stuck before station i + 1. Every station from start to i fails too,
      // since you reached each one with zero or more fuel. Try i + 1 next.
      start = i + 1;
      tank = 0;
    }
  }
  return total >= 0 ? start : -1; // A non-negative total means start works.
}

console.log(startingStation([1, 2, 3, 4, 5], [3, 4, 5, 1, 2])); // 3
console.log(startingStation([2, 3, 4], [3, 4, 3])); // -1
console.log(startingStation([3, 1, 1], [1, 2, 2])); // 0
