using System;
using System.Collections.Generic;

public class Solution
{
    static readonly HashSet<string> Operators = new() { "+", "-", "*", "/" };

    // Evaluates an expression in Reverse Polish Notation, where each operator
    // comes after its two operands. Division truncates toward zero.
    public static int EvalRpn(string[] tokens)
    {
        var stack = new Stack<int>();
        foreach (string token in tokens)
        {
            if (Operators.Contains(token))
            {
                // The right operand was pushed last, so it comes off first.
                int b = stack.Pop();
                int a = stack.Pop();
                stack.Push(Apply(a, b, token));
            }
            else
            {
                stack.Push(int.Parse(token));
            }
        }
        return stack.Pop(); // A valid expression leaves exactly one value.
    }

    static int Apply(int a, int b, string op) => op switch
    {
        "+" => a + b,
        "-" => a - b,
        "*" => a * b,
        _ => a / b, // Integer division in C# already truncates toward zero.
    };

    public static void Main()
    {
        Console.WriteLine(EvalRpn(new[] { "2", "1", "+", "3", "*" })); // 9
        Console.WriteLine(EvalRpn(new[] { "4", "13", "5", "/", "+" })); // 6
        Console.WriteLine(EvalRpn(new[] { "10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+" })); // 22
        Console.WriteLine(EvalRpn(new[] { "-7", "2", "/" })); // -3
    }
}
