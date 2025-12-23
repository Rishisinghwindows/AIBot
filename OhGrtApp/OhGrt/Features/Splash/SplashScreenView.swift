import SwiftUI

/// Animated splash screen shown at app launch
struct SplashScreenView: View {
    @ObservedObject private var theme = ThemeManager.shared

    // Animation states
    @State private var logoScale: CGFloat = 0.3
    @State private var logoOpacity: Double = 0
    @State private var ringRotation: Double = 0
    @State private var ringScale: CGFloat = 0.5
    @State private var ringOpacity: Double = 0
    @State private var textOpacity: Double = 0
    @State private var textOffset: CGFloat = 20
    @State private var pulseRings: [Bool] = [false, false, false]
    @State private var glowOpacity: Double = 0
    @State private var particlesVisible = false

    let onFinished: () -> Void

    var body: some View {
        ZStack {
            // Animated gradient background
            AnimatedSplashBackground()

            // Floating particles
            if particlesVisible {
                FloatingSplashParticles()
            }

            VStack(spacing: 24) {
                Spacer()

                // Logo container
                ZStack {
                    // Pulse rings
                    ForEach(0..<3, id: \.self) { index in
                        Circle()
                            .stroke(
                                LinearGradient(
                                    colors: [
                                        theme.primaryColor.opacity(0.4),
                                        theme.secondaryColor.opacity(0.2)
                                    ],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ),
                                lineWidth: 2
                            )
                            .frame(width: 140 + CGFloat(index * 40), height: 140 + CGFloat(index * 40))
                            .scaleEffect(pulseRings[index] ? 1.3 : 1.0)
                            .opacity(pulseRings[index] ? 0 : 0.6)
                    }

                    // Rotating outer ring
                    Circle()
                        .stroke(
                            AngularGradient(
                                colors: theme.accentTheme.primaryColors + [theme.accentTheme.primaryColors[0]],
                                center: .center,
                                startAngle: .degrees(ringRotation),
                                endAngle: .degrees(ringRotation + 360)
                            ),
                            lineWidth: 4
                        )
                        .frame(width: 130, height: 130)
                        .scaleEffect(ringScale)
                        .opacity(ringOpacity)

                    // Glow effect
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [theme.primaryColor.opacity(0.5), .clear],
                                center: .center,
                                startRadius: 30,
                                endRadius: 90
                            )
                        )
                        .frame(width: 180, height: 180)
                        .opacity(glowOpacity)
                        .blur(radius: 20)

                    // Main logo circle
                    ZStack {
                        // Background circle with gradient
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [theme.primaryColor, theme.secondaryColor],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 120, height: 120)

                        // Inner shine
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.white.opacity(0.3), .clear],
                                    startPoint: .topLeading,
                                    endPoint: .center
                                )
                            )
                            .frame(width: 110, height: 110)
                            .offset(x: -15, y: -15)

                        // D23 Text
                        VStack(spacing: 0) {
                            Text("D23")
                                .font(.system(size: 36, weight: .black, design: .rounded))
                                .foregroundColor(.white)
                            Text("AI")
                                .font(.system(size: 16, weight: .bold, design: .rounded))
                                .foregroundColor(.white.opacity(0.9))
                        }
                        .shadow(color: .black.opacity(0.2), radius: 2, y: 2)
                    }
                    .shadow(color: theme.primaryColor.opacity(0.5), radius: 25, y: 12)
                    .scaleEffect(logoScale)
                    .opacity(logoOpacity)
                }

                // App name and tagline
                VStack(spacing: 8) {
                    HStack(spacing: 4) {
                        Text("D23")
                            .font(.system(size: 44, weight: .black, design: .rounded))
                            .foregroundStyle(
                                LinearGradient(
                                    colors: [theme.primaryColor, theme.secondaryColor],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                        Text("AI")
                            .font(.system(size: 32, weight: .bold, design: .rounded))
                            .foregroundColor(.primary.opacity(0.8))
                    }

                    Text("Your Intelligent Assistant")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.secondary)
                }
                .opacity(textOpacity)
                .offset(y: textOffset)

                Spacer()

                // Loading indicator
                HStack(spacing: 6) {
                    ForEach(0..<3, id: \.self) { index in
                        Circle()
                            .fill(theme.primaryColor)
                            .frame(width: 8, height: 8)
                            .scaleEffect(pulseRings[index] ? 1.2 : 0.8)
                            .opacity(pulseRings[index] ? 1.0 : 0.4)
                    }
                }
                .opacity(textOpacity)
                .padding(.bottom, 60)
            }
        }
        .onAppear {
            startAnimations()
        }
    }

    // MARK: - Animations

    private func startAnimations() {
        // Logo entrance
        withAnimation(.spring(response: 0.8, dampingFraction: 0.6).delay(0.1)) {
            logoScale = 1.0
            logoOpacity = 1.0
        }

        // Ring entrance
        withAnimation(.spring(response: 0.7, dampingFraction: 0.7).delay(0.2)) {
            ringScale = 1.0
            ringOpacity = 1.0
        }

        // Glow
        withAnimation(.easeInOut(duration: 0.8).delay(0.3)) {
            glowOpacity = 1.0
        }

        // Text entrance
        withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(0.4)) {
            textOpacity = 1.0
            textOffset = 0
        }

        // Start ring rotation
        withAnimation(.linear(duration: 8).repeatForever(autoreverses: false)) {
            ringRotation = 360
        }

        // Start pulse animations
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            startPulseAnimations()
            particlesVisible = true
        }

        // Finish splash after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
            withAnimation(.easeInOut(duration: 0.3)) {
                onFinished()
            }
        }
    }

    private func startPulseAnimations() {
        for i in 0..<3 {
            withAnimation(
                .easeOut(duration: 1.5)
                .repeatForever(autoreverses: false)
                .delay(Double(i) * 0.3)
            ) {
                pulseRings[i] = true
            }
        }
    }
}

// MARK: - Animated Background

private struct AnimatedSplashBackground: View {
    @ObservedObject private var theme = ThemeManager.shared
    @State private var animateGradient = false

    var body: some View {
        ZStack {
            // Base color
            Color(.systemBackground)
                .ignoresSafeArea()

            // Animated gradient orbs
            GeometryReader { geo in
                ZStack {
                    // Top orb
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [theme.primaryColor.opacity(0.25), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 250
                            )
                        )
                        .frame(width: 500, height: 500)
                        .offset(
                            x: animateGradient ? -50 : -100,
                            y: animateGradient ? -100 : -150
                        )
                        .blur(radius: 60)

                    // Bottom orb
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [theme.secondaryColor.opacity(0.2), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 200
                            )
                        )
                        .frame(width: 400, height: 400)
                        .offset(
                            x: animateGradient ? 100 : 150,
                            y: geo.size.height - (animateGradient ? 150 : 200)
                        )
                        .blur(radius: 50)

                    // Center accent
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [Color.pink.opacity(0.15), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 150
                            )
                        )
                        .frame(width: 300, height: 300)
                        .offset(
                            x: animateGradient ? 20 : -20,
                            y: geo.size.height * 0.3
                        )
                        .blur(radius: 40)
                }
            }
            .ignoresSafeArea()
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 3).repeatForever(autoreverses: true)) {
                animateGradient = true
            }
        }
    }
}

// MARK: - Floating Particles

private struct FloatingSplashParticles: View {
    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        GeometryReader { geo in
            ZStack {
                ForEach(0..<12, id: \.self) { index in
                    ParticleView(
                        size: CGFloat.random(in: 4...10),
                        color: index % 2 == 0 ? theme.primaryColor : theme.secondaryColor,
                        delay: Double(index) * 0.15,
                        screenSize: geo.size
                    )
                }
            }
        }
        .ignoresSafeArea()
    }
}

private struct ParticleView: View {
    let size: CGFloat
    let color: Color
    let delay: Double
    let screenSize: CGSize

    @State private var isAnimating = false
    @State private var position: CGPoint
    @State private var opacity: Double = 0

    init(size: CGFloat, color: Color, delay: Double, screenSize: CGSize) {
        self.size = size
        self.color = color
        self.delay = delay
        self.screenSize = screenSize
        self._position = State(initialValue: CGPoint(
            x: CGFloat.random(in: 50...(screenSize.width - 50)),
            y: CGFloat.random(in: 100...(screenSize.height - 100))
        ))
    }

    var body: some View {
        Circle()
            .fill(color.opacity(0.6))
            .frame(width: size, height: size)
            .blur(radius: size / 4)
            .position(position)
            .opacity(opacity)
            .onAppear {
                withAnimation(.easeInOut(duration: 0.5).delay(delay)) {
                    opacity = 1
                }

                withAnimation(
                    .easeInOut(duration: Double.random(in: 2...4))
                    .repeatForever(autoreverses: true)
                    .delay(delay)
                ) {
                    position = CGPoint(
                        x: position.x + CGFloat.random(in: -30...30),
                        y: position.y + CGFloat.random(in: -50...50)
                    )
                }
            }
    }
}

// MARK: - Preview

#Preview("Splash Screen") {
    SplashScreenView(onFinished: {})
}
