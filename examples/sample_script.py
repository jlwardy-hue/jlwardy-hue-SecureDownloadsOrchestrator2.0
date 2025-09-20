#!/usr/bin/env python3
"""
Sample Python script for AI classification testing.
"""

def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    """Main function to demonstrate Fibonacci calculation."""
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")

if __name__ == "__main__":
    main()
