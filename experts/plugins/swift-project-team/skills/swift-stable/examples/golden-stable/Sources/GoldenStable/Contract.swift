import Foundation

public struct ContractResult: Equatable, Sendable {
    public let value: String
    public let successful: Bool

    public init(value: String, successful: Bool) {
        self.value = value
        self.successful = successful
    }
}

public func evaluateContract(_ input: String) -> ContractResult {
    let value = input.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    return ContractResult(value: value, successful: !value.isEmpty)
}
