// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "GoldenPackageManager",
    products: [
        .library(name: "GoldenPackageManager", targets: ["GoldenPackageManager"]),
        .executable(name: "GoldenVerifier", targets: ["GoldenVerifier"])
    ],
    targets: [
        .target(name: "GoldenPackageManager"),
        .executableTarget(name: "GoldenVerifier", dependencies: ["GoldenPackageManager"])
    ]
)
