// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "GoldenTesting",
    products: [
        .library(name: "GoldenTesting", targets: ["GoldenTesting"]),
        .executable(name: "GoldenVerifier", targets: ["GoldenVerifier"])
    ],
    targets: [
        .target(name: "GoldenTesting"),
        .executableTarget(name: "GoldenVerifier", dependencies: ["GoldenTesting"])
    ]
)
