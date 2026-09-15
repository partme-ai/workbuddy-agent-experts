// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "GoldenJavaMigrationTesting",
    products: [
        .library(name: "GoldenJavaMigrationTesting", targets: ["GoldenJavaMigrationTesting"]),
        .executable(name: "GoldenVerifier", targets: ["GoldenVerifier"])
    ],
    targets: [
        .target(name: "GoldenJavaMigrationTesting"),
        .executableTarget(name: "GoldenVerifier", dependencies: ["GoldenJavaMigrationTesting"])
    ]
)
