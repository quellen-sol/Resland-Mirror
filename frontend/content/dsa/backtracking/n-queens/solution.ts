// Every way to place n queens on an n x n board so no two attack each other.
// Each board is a list of rows, with "Q" for a queen and "." for an empty square.
export function solveNQueens(n: number): string[][] {
  const result: string[][] = [];
  const queens = new Array<number>(n).fill(0); // queens[row] = column of that row's queen
  const cols = new Array<boolean>(n).fill(false);
  const diags = new Array<boolean>(2 * n - 1).fill(false); // Indexed by row - col + n - 1.
  const antiDiags = new Array<boolean>(2 * n - 1).fill(false); // Indexed by row + col.

  function backtrack(row: number): void {
    if (row === n) {
      result.push(queens.map((col) => ".".repeat(col) + "Q" + ".".repeat(n - col - 1)));
      return;
    }
    for (let col = 0; col < n; col++) {
      const d = row - col + n - 1;
      const a = row + col;
      if (cols[col] || diags[d] || antiDiags[a]) continue; // Attacked: prune this branch.
      queens[row] = col; // Choose: put this row's queen in col.
      cols[col] = diags[d] = antiDiags[a] = true;
      backtrack(row + 1); // Explore the next row (one queen per row).
      // Un-choose. The next choice overwrites queens[row], so only the flags need resetting.
      cols[col] = diags[d] = antiDiags[a] = false;
    }
  }

  backtrack(0);
  return result;
}

const boards = solveNQueens(4);
console.log(boards.length); // 2
for (const row of boards[0]) console.log(row); // .Q.. then ...Q then Q... then ..Q.
console.log(solveNQueens(8).length); // 92
