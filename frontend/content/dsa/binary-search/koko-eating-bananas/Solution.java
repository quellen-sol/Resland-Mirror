import java.util.Arrays;

public class Solution {
    // Slowest whole-number speed that lets Koko eat every pile within h hours.
    static int minEatingSpeed(int[] piles, int h) {
        int lo = 1;
        int hi = Arrays.stream(piles).max().getAsInt(); // At max(piles) every pile takes one hour.
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (hoursNeeded(piles, mid) <= h) hi = mid; // Fast enough: the answer is mid or slower.
            else lo = mid + 1; // Too slow, and so is every speed below mid.
        }
        return lo;
    }

    // Hours to finish every pile at speed bananas per hour. A long, because
    // slow speeds over many big piles overflow an int.
    static long hoursNeeded(int[] piles, int speed) {
        long hours = 0;
        // Round up: a partly eaten pile still costs a whole hour.
        for (int pile : piles) hours += (pile + speed - 1) / speed;
        return hours;
    }

    public static void main(String[] args) {
        System.out.println(minEatingSpeed(new int[] {3, 6, 7, 11}, 8)); // 4
        System.out.println(minEatingSpeed(new int[] {30, 11, 23, 4, 20}, 5)); // 30
        System.out.println(minEatingSpeed(new int[] {30, 11, 23, 4, 20}, 6)); // 23
    }
}
