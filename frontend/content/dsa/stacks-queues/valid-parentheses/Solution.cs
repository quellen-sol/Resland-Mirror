using System;
using System.Collections.Generic;

public class Solution
{
    // Each closing bracket and the opener it must match.
    static readonly Dictionary<char, char> Pairs = new() { [')'] = '(', [']'] = '[', ['}'] = '{' };

    // Whether every bracket in s is closed by the same type, in the right order.
    public static bool IsValid(string s)
    {
        var stack = new Stack<char>();
        foreach (char ch in s)
        {
            if (!Pairs.TryGetValue(ch, out char opener))
            {
                stack.Push(ch); // An opener waits on the stack for its closer.
            }
            else if (stack.Count == 0 || stack.Pop() != opener)
            {
                return false; // A closer must match the most recent unclosed opener.
            }
        }
        return stack.Count == 0; // Anything left was never closed.
    }

    public static void Main()
    {
        Console.WriteLine(IsValid("([]){}")); // True
        Console.WriteLine(IsValid("([)]")); // False
        Console.WriteLine(IsValid("((")); // False
        Console.WriteLine(IsValid("]")); // False
    }
}
