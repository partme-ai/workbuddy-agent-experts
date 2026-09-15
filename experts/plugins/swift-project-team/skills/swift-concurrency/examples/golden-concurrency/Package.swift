// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "GoldenConcurrency",
    products: [
        .library(name: "GoldenConcurrency", targets: ["GoldenConcurrency"]),
        .executable(name: "GoldenVerifier", targets: ["GoldenVerifier"])
    ],
    targets: [
        .target(name: "GoldenConcurrency"),
        .executableTarget(name: "GoldenVerifier", dependencies: ["GoldenConcurrency"])
    ]
)
