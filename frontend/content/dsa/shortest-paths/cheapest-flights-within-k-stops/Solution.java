import java.util.Arrays;

public class Solution {
    // Cheapest price from src to dst using at most k stops (so at most k + 1
    // flights), where each flight is [u, v, price]. -1 if no such route exists.
    static int findCheapestPrice(int n, int[][] flights, int src, int dst, int k) {
        int[] prices = new int[n];
        Arrays.fill(prices, Integer.MAX_VALUE);
        prices[src] = 0;
        // After round i, prices[v] is the cheapest way to reach v in at most i flights.
        for (int round = 1; round <= k + 1; round++) {
            // Read last round's prices and write into a copy. Updating in place would let
            // one round chain several flights and slip past the stop limit.
            int[] nextPrices = prices.clone();
            for (int[] flight : flights) {
                int u = flight[0], v = flight[1], price = flight[2];
                // Only fly out of cities an earlier round already reached.
                if (prices[u] != Integer.MAX_VALUE && prices[u] + price < nextPrices[v]) {
                    nextPrices[v] = prices[u] + price;
                }
            }
            prices = nextPrices;
        }
        return prices[dst] == Integer.MAX_VALUE ? -1 : prices[dst];
    }

    public static void main(String[] args) {
        System.out.println(findCheapestPrice(4, new int[][] {{0, 1, 100}, {1, 2, 100}, {2, 0, 100}, {1, 3, 600}, {2, 3, 200}}, 0, 3, 1)); // 700
        System.out.println(findCheapestPrice(3, new int[][] {{0, 1, 100}, {1, 2, 100}, {0, 2, 500}}, 0, 2, 1)); // 200
        System.out.println(findCheapestPrice(3, new int[][] {{0, 1, 100}, {1, 2, 100}, {0, 2, 500}}, 0, 2, 0)); // 500
        System.out.println(findCheapestPrice(3, new int[][] {{0, 1, 100}, {1, 2, 100}}, 0, 2, 0)); // -1
    }
}
