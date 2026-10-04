public class Solution {
    // Most money you can take from a row of houses without robbing two neighbors.
    static int rob(int[] nums) {
        // best(i) = most money from the first i houses
        //         = max(best(i - 1), best(i - 2) + nums[i - 1])
        // Each value reads only the two before it, so keep just those two.
        int twoBack = 0; // best(i - 2)
        int oneBack = 0; // best(i - 1)
        for (int money : nums) {
            // Skip this house and keep oneBack, or rob it on top of twoBack.
            int here = Math.max(oneBack, twoBack + money);
            twoBack = oneBack;
            oneBack = here;
        }
        return oneBack;
    }

    public static void main(String[] args) {
        System.out.println(rob(new int[] {1, 2, 3, 1})); // 4
        System.out.println(rob(new int[] {2, 7, 9, 3, 1})); // 12
        System.out.println(rob(new int[] {2, 1, 1, 2})); // 4
    }
}
