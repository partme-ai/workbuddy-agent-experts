// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "GoldenStable",
    products: [
        .library(name: "GoldenStable", targets: ["GoldenStable"]),
        .executable(name: "GoldenVerifier", targets: ["GoldenVerifier"])
    ],
    targets: [
        .target(name: "GoldenStable"),
        .executableTarget(name: "GoldenVerifier", dependencies: ["GoldenStable"])
    ]
)
