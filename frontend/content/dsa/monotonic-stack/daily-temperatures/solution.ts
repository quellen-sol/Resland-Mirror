// For each day, how many days you wait for a strictly warmer one, or 0 if
// none comes.
export function dailyTemperatures(temperatures: number[]): number[] {
  const answer = new Array<number>(temperatures.length).fill(0);
  // Days still waiting for a warmer day, coldest on top. The answer is a
  // distance, so the stack holds indices rather than temperatures.
  const stack: number[] = [];
  for (let i = 0; i < temperatures.length; i++) {
    // Today is the first warmer day for every colder day on top of the stack.
    while (stack.length > 0 && temperatures[stack[stack.length - 1]] < temperatures[i]) {
      const day = stack.pop()!;
      answer[day] = i - day;
    }
    stack.push(i);
  }
  return answer; // Days left on the stack never warm up, so they keep 0.
}

console.log(JSON.stringify(dailyTemperatures([73, 74, 75, 71, 69, 72, 76, 73]))); // [1,1,4,2,1,1,0,0]
console.log(JSON.stringify(dailyTemperatures([30, 40, 50, 60]))); // [1,1,1,0]
console.log(JSON.stringify(dailyTemperatures([60, 50, 50, 70]))); // [3,2,1,0]
