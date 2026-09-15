// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "GoldenJavaMigration",
    products: [
        .library(name: "GoldenJavaMigration", targets: ["GoldenJavaMigration"]),
        .executable(name: "GoldenVerifier", targets: ["GoldenVerifier"])
    ],
    targets: [
        .target(name: "GoldenJavaMigration"),
        .executableTarget(name: "GoldenVerifier", dependencies: ["GoldenJavaMigration"])
    ]
)
