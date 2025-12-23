import SwiftUI

/// D23 AI App Icon Generator - Use the preview to capture and export the icon
/// Instructions:
/// 1. Run the preview in Xcode
/// 2. Right-click on the preview and select "Export as Image..."
/// 3. Save as 1024x1024 PNG
/// 4. Add to Assets.xcassets/AppIcon.appiconset/
struct AppIconGenerator: View {
    let size: CGFloat

    init(size: CGFloat = 1024) {
        self.size = size
    }

    var body: some View {
        ZStack {
            // Background gradient - Deep purple to blue
            LinearGradient(
                colors: [
                    Color(red: 0.35, green: 0.15, blue: 0.85),
                    Color(red: 0.20, green: 0.10, blue: 0.70),
                    Color(red: 0.15, green: 0.08, blue: 0.55)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            // Neural network pattern
            NeuralPatternBackground(size: size)
                .opacity(0.15)

            // Decorative glowing orbs
            Circle()
                .fill(
                    RadialGradient(
                        colors: [Color.cyan.opacity(0.4), .clear],
                        center: .center,
                        startRadius: 0,
                        endRadius: size * 0.35
                    )
                )
                .frame(width: size * 0.7, height: size * 0.7)
                .offset(x: -size * 0.25, y: -size * 0.25)
                .blur(radius: size * 0.05)

            Circle()
                .fill(
                    RadialGradient(
                        colors: [Color.purple.opacity(0.5), .clear],
                        center: .center,
                        startRadius: 0,
                        endRadius: size * 0.3
                    )
                )
                .frame(width: size * 0.6, height: size * 0.6)
                .offset(x: size * 0.2, y: size * 0.25)
                .blur(radius: size * 0.04)

            // Main content container
            ZStack {
                // Outer glow ring
                Circle()
                    .stroke(
                        AngularGradient(
                            colors: [
                                Color.cyan,
                                Color.purple,
                                Color.pink,
                                Color.cyan
                            ],
                            center: .center
                        ),
                        lineWidth: size * 0.02
                    )
                    .frame(width: size * 0.72, height: size * 0.72)
                    .blur(radius: size * 0.01)

                // White/light background circle
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.white, Color(white: 0.95)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: size * 0.62, height: size * 0.62)
                    .shadow(color: .black.opacity(0.2), radius: size * 0.04, y: size * 0.02)

                // D23 Text with gradient
                Text("D23")
                    .font(.system(size: size * 0.22, weight: .black, design: .rounded))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [
                                Color(red: 0.35, green: 0.15, blue: 0.85),
                                Color(red: 0.55, green: 0.25, blue: 0.90)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .offset(y: -size * 0.04)

                // AI text below
                Text("AI")
                    .font(.system(size: size * 0.10, weight: .bold, design: .rounded))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [
                                Color(red: 0.0, green: 0.75, blue: 0.85),
                                Color(red: 0.55, green: 0.25, blue: 0.90)
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .offset(y: size * 0.12)

                // Small sparkle accents
                Image(systemName: "sparkle")
                    .font(.system(size: size * 0.06, weight: .bold))
                    .foregroundColor(Color.cyan)
                    .offset(x: size * 0.18, y: -size * 0.12)

                Image(systemName: "sparkle")
                    .font(.system(size: size * 0.04, weight: .bold))
                    .foregroundColor(Color.purple)
                    .offset(x: -size * 0.20, y: size * 0.08)
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: size * 0.22))
    }
}

/// Neural network pattern for background
private struct NeuralPatternBackground: View {
    let size: CGFloat

    var body: some View {
        Canvas { context, canvasSize in
            let nodePositions: [CGPoint] = [
                CGPoint(x: 0.15, y: 0.20),
                CGPoint(x: 0.30, y: 0.10),
                CGPoint(x: 0.70, y: 0.15),
                CGPoint(x: 0.85, y: 0.25),
                CGPoint(x: 0.10, y: 0.50),
                CGPoint(x: 0.90, y: 0.55),
                CGPoint(x: 0.20, y: 0.80),
                CGPoint(x: 0.75, y: 0.85),
                CGPoint(x: 0.50, y: 0.95)
            ]

            let connections: [(Int, Int)] = [
                (0, 1), (1, 2), (2, 3),
                (0, 4), (3, 5),
                (4, 6), (5, 7),
                (6, 8), (7, 8)
            ]

            // Draw connections
            for (from, to) in connections {
                let fromPoint = CGPoint(
                    x: nodePositions[from].x * canvasSize.width,
                    y: nodePositions[from].y * canvasSize.height
                )
                let toPoint = CGPoint(
                    x: nodePositions[to].x * canvasSize.width,
                    y: nodePositions[to].y * canvasSize.height
                )

                var path = Path()
                path.move(to: fromPoint)
                path.addLine(to: toPoint)

                context.stroke(
                    path,
                    with: .color(.white.opacity(0.5)),
                    lineWidth: size * 0.003
                )
            }

            // Draw nodes
            for pos in nodePositions {
                let point = CGPoint(
                    x: pos.x * canvasSize.width,
                    y: pos.y * canvasSize.height
                )
                let nodeSize = size * 0.02

                context.fill(
                    Circle().path(in: CGRect(
                        x: point.x - nodeSize/2,
                        y: point.y - nodeSize/2,
                        width: nodeSize,
                        height: nodeSize
                    )),
                    with: .color(.white.opacity(0.6))
                )
            }
        }
    }
}

/// D23 AI Dark App Icon
struct AppIconDarkGenerator: View {
    let size: CGFloat

    init(size: CGFloat = 1024) {
        self.size = size
    }

    var body: some View {
        ZStack {
            // Dark background
            LinearGradient(
                colors: [
                    Color(red: 0.08, green: 0.05, blue: 0.15),
                    Color(red: 0.05, green: 0.03, blue: 0.10),
                    Color(red: 0.02, green: 0.01, blue: 0.05)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            // Subtle neural pattern
            NeuralPatternBackground(size: size)
                .opacity(0.1)

            // Glowing orbs
            Circle()
                .fill(
                    RadialGradient(
                        colors: [Color.cyan.opacity(0.3), .clear],
                        center: .center,
                        startRadius: 0,
                        endRadius: size * 0.3
                    )
                )
                .frame(width: size * 0.6, height: size * 0.6)
                .offset(x: -size * 0.2, y: -size * 0.2)
                .blur(radius: size * 0.06)

            Circle()
                .fill(
                    RadialGradient(
                        colors: [Color.purple.opacity(0.4), .clear],
                        center: .center,
                        startRadius: 0,
                        endRadius: size * 0.25
                    )
                )
                .frame(width: size * 0.5, height: size * 0.5)
                .offset(x: size * 0.2, y: size * 0.2)
                .blur(radius: size * 0.05)

            // Main content
            ZStack {
                // Glowing ring
                Circle()
                    .stroke(
                        AngularGradient(
                            colors: [
                                Color.cyan,
                                Color.purple,
                                Color.pink,
                                Color.cyan
                            ],
                            center: .center
                        ),
                        lineWidth: size * 0.03
                    )
                    .frame(width: size * 0.65, height: size * 0.65)
                    .blur(radius: size * 0.008)

                // Inner circle with gradient
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [
                                Color(red: 0.35, green: 0.15, blue: 0.85),
                                Color(red: 0.20, green: 0.10, blue: 0.60)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: size * 0.55, height: size * 0.55)
                    .shadow(color: Color.purple.opacity(0.5), radius: size * 0.05)

                // D23 Text
                Text("D23")
                    .font(.system(size: size * 0.20, weight: .black, design: .rounded))
                    .foregroundColor(.white)
                    .offset(y: -size * 0.035)

                // AI text
                Text("AI")
                    .font(.system(size: size * 0.09, weight: .bold, design: .rounded))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [Color.cyan, Color.white],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .offset(y: size * 0.11)

                // Sparkles
                Image(systemName: "sparkle")
                    .font(.system(size: size * 0.055, weight: .bold))
                    .foregroundColor(.cyan)
                    .offset(x: size * 0.16, y: -size * 0.10)

                Image(systemName: "sparkle")
                    .font(.system(size: size * 0.035, weight: .bold))
                    .foregroundColor(.white.opacity(0.8))
                    .offset(x: -size * 0.18, y: size * 0.07)
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: size * 0.22))
    }
}

/// D23 AI Tinted App Icon (grayscale)
struct AppIconTintedGenerator: View {
    let size: CGFloat

    init(size: CGFloat = 1024) {
        self.size = size
    }

    var body: some View {
        ZStack {
            // Light gray background
            LinearGradient(
                colors: [
                    Color(white: 0.95),
                    Color(white: 0.88)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            // Main content
            ZStack {
                // Circle background
                Circle()
                    .fill(Color(white: 0.75))
                    .frame(width: size * 0.55, height: size * 0.55)

                // D23 Text
                Text("D23")
                    .font(.system(size: size * 0.20, weight: .black, design: .rounded))
                    .foregroundColor(Color(white: 0.35))
                    .offset(y: -size * 0.035)

                // AI text
                Text("AI")
                    .font(.system(size: size * 0.09, weight: .bold, design: .rounded))
                    .foregroundColor(Color(white: 0.45))
                    .offset(y: size * 0.11)
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: size * 0.22))
    }
}

// MARK: - Previews

#Preview("D23 AI Icon - Light (1024x1024)") {
    AppIconGenerator(size: 1024)
        .frame(width: 512, height: 512)
        .previewLayout(.sizeThatFits)
}

#Preview("D23 AI Icon - Dark (1024x1024)") {
    AppIconDarkGenerator(size: 1024)
        .frame(width: 512, height: 512)
        .previewLayout(.sizeThatFits)
}

#Preview("D23 AI Icon - Tinted (1024x1024)") {
    AppIconTintedGenerator(size: 1024)
        .frame(width: 512, height: 512)
        .previewLayout(.sizeThatFits)
}

#Preview("D23 AI Icon Showcase") {
    HStack(spacing: 20) {
        VStack {
            AppIconGenerator(size: 200)
                .frame(width: 100, height: 100)
            Text("Light")
                .font(.caption)
        }

        VStack {
            AppIconDarkGenerator(size: 200)
                .frame(width: 100, height: 100)
            Text("Dark")
                .font(.caption)
        }

        VStack {
            AppIconTintedGenerator(size: 200)
                .frame(width: 100, height: 100)
            Text("Tinted")
                .font(.caption)
        }
    }
    .padding()
}
