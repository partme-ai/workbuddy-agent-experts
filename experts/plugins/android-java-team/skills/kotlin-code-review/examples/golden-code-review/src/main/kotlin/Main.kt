data class ContractResult(val value: String, val successful: Boolean)

fun evaluateContract(input: String): ContractResult =
    ContractResult(input.trim().lowercase(), input.isNotBlank())

fun main() {
    check(evaluateContract(" Kotlin ").value == "kotlin")
    check(!evaluateContract("   ").successful)
}

