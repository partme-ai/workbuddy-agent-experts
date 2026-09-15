// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "GoldenCodeReview",
    products: [
        .library(name: "GoldenCodeReview", targets: ["GoldenCodeReview"]),
        .executable(name: "GoldenVerifier", targets: ["GoldenVerifier"])
    ],
    targets: [
        .target(name: "GoldenCodeReview"),
        .executableTarget(name: "GoldenVerifier", dependencies: ["GoldenCodeReview"])
    ]
)
