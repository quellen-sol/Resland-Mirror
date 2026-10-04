using System;

public class Solution
{
    // Most money you can take from a row of houses without robbing two neighbors.
    public static int Rob(int[] nums)
    {
        // best(i) = most money from the first i houses
        //         = max(best(i - 1), best(i - 2) + nums[i - 1])
        // Each value reads only the two before it, so keep just those two.
        int twoBack = 0; // best(i - 2)
        int oneBack = 0; // best(i - 1)
        foreach (int money in nums)
        {
            // Skip this house and keep oneBack, or rob it on top of twoBack.
            int here = Math.Max(oneBack, twoBack + money);
            twoBack = oneBack;
            oneBack = here;
        }
        return oneBack;
    }

    public static void Main()
    {
        Console.WriteLine(Rob(new[] { 1, 2, 3, 1 })); // 4
        Console.WriteLine(Rob(new[] { 2, 7, 9, 3, 1 })); // 12
        Console.WriteLine(Rob(new[] { 2, 1, 1, 2 })); // 4
    }
}
