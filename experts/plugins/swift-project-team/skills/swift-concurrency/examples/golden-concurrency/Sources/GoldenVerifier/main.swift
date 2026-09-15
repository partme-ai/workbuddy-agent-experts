import GoldenConcurrency

precondition(evaluateContract(" Swift ").value == "swift")
precondition(!evaluateContract("   ").successful)
print("golden verification passed")

