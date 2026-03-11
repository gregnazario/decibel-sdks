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
    dependencies: [
        .package(url: "https://github.com/Quick/Quick.git", from: "7.0.0"),
        .package(url: "https://github.com/Quick/Nimble.git", from: "12.0.0")
    ],
    targets: [
        .target(
            name: "DecibelSDK",
            path: "Sources/DecibelSDK"
        ),
        .testTarget(
            name: "DecibelSDKTests",
            dependencies: [
                "DecibelSDK",
                "Quick",
                "Nimble"
            ],
            path: "Tests/DecibelSDKTests"
        ),
    ]
)
