using System;

public class Solution
{
    // Cheapest price from src to dst using at most k stops (so at most k + 1
    // flights), where each flight is [u, v, price]. -1 if no such route exists.
    public static int FindCheapestPrice(int n, int[][] flights, int src, int dst, int k)
    {
        var prices = new int[n];
        Array.Fill(prices, int.MaxValue);
        prices[src] = 0;
        // After round i, prices[v] is the cheapest way to reach v in at most i flights.
        for (int round = 1; round <= k + 1; round++)
        {
            // Read last round's prices and write into a copy. Updating in place would let
            // one round chain several flights and slip past the stop limit.
            var nextPrices = (int[])prices.Clone();
            foreach (var flight in flights)
            {
                int u = flight[0], v = flight[1], price = flight[2];
                // Only fly out of cities an earlier round already reached.
                if (prices[u] != int.MaxValue && prices[u] + price < nextPrices[v])
                {
                    nextPrices[v] = prices[u] + price;
                }
            }
            prices = nextPrices;
        }
        return prices[dst] == int.MaxValue ? -1 : prices[dst];
    }

    public static void Main()
    {
        Console.WriteLine(FindCheapestPrice(4, [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]], 0, 3, 1)); // 700
        Console.WriteLine(FindCheapestPrice(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1)); // 200
        Console.WriteLine(FindCheapestPrice(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0)); // 500
        Console.WriteLine(FindCheapestPrice(3, [[0, 1, 100], [1, 2, 100]], 0, 2, 0)); // -1
    }
}
