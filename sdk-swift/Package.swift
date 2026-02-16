// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "DecibelSDK",
    platforms: [
        .iOS(.v15),
        .macOS(.v12)
    ],
    products: [
        .library(name: "DecibelSDK", targets: ["DecibelSDK"]),
    ],
    targets: [
        .target(
            name: "DecibelSDK",
            path: "Sources/DecibelSDK"
        ),
        .testTarget(
            name: "DecibelSDKTests",
            dependencies: ["DecibelSDK"],
            path: "Tests/DecibelSDKTests"
        ),
    ]
)
