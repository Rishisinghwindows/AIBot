import SwiftUI

/// Onboarding data model
struct OnboardingPage: Identifiable {
    let id = UUID()
    let icon: String
    let title: String
    let subtitle: String
    let description: String
    let color: Color
    let secondaryColor: Color
    let features: [OnboardingFeature]
    let illustration: OnboardingIllustration
}

struct OnboardingFeature: Identifiable {
    let id = UUID()
    let icon: String
    let text: String
}

enum OnboardingIllustration {
    case aiAssistant
    case astrology
    case travel
    case integrations
}

/// Main Onboarding View with animated pages
struct OnboardingView: View {
    @ObservedObject private var theme = ThemeManager.shared
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false

    @State private var currentPage = 0
    @State private var dragOffset: CGFloat = 0

    private let pages: [OnboardingPage] = [
        OnboardingPage(
            icon: "brain.head.profile",
            title: "Welcome to D23 AI",
            subtitle: "Your Intelligent Assistant",
            description: "Experience next-generation AI powered conversations designed for you.",
            color: Color(red: 0.35, green: 0.15, blue: 0.85),
            secondaryColor: .cyan,
            features: [
                OnboardingFeature(icon: "sparkles", text: "Smart AI"),
                OnboardingFeature(icon: "globe.asia.australia.fill", text: "22 Languages"),
                OnboardingFeature(icon: "bolt.fill", text: "Lightning Fast")
            ],
            illustration: .aiAssistant
        ),
        OnboardingPage(
            icon: "moon.stars.fill",
            title: "Astrology & Insights",
            subtitle: "Discover Your Cosmic Path",
            description: "Get personalized horoscopes, kundli analysis, and spiritual guidance.",
            color: .indigo,
            secondaryColor: .purple,
            features: [
                OnboardingFeature(icon: "sun.max.fill", text: "Daily Horoscope"),
                OnboardingFeature(icon: "circle.hexagongrid", text: "Birth Charts"),
                OnboardingFeature(icon: "sparkle", text: "Predictions")
            ],
            illustration: .astrology
        ),
        OnboardingPage(
            icon: "train.side.front.car",
            title: "Travel Made Easy",
            subtitle: "Your Journey Companion",
            description: "Track trains, check PNR status, and plan your travels seamlessly.",
            color: .blue,
            secondaryColor: .teal,
            features: [
                OnboardingFeature(icon: "ticket.fill", text: "PNR Status"),
                OnboardingFeature(icon: "location.fill", text: "Live Tracking"),
                OnboardingFeature(icon: "map.fill", text: "Route Plans")
            ],
            illustration: .travel
        ),
        OnboardingPage(
            icon: "square.stack.3d.up.fill",
            title: "Powerful Integrations",
            subtitle: "Connect Your World",
            description: "Seamlessly integrate with your favorite tools and services.",
            color: .orange,
            secondaryColor: .pink,
            features: [
                OnboardingFeature(icon: "message.fill", text: "Slack & Teams"),
                OnboardingFeature(icon: "doc.text.fill", text: "Jira & GitHub"),
                OnboardingFeature(icon: "cloud.fill", text: "Cloud Sync")
            ],
            illustration: .integrations
        )
    ]

    var body: some View {
        ZStack {
            // Animated background
            AnimatedOnboardingBackground(
                primaryColor: pages[currentPage].color,
                secondaryColor: pages[currentPage].secondaryColor
            )

            VStack(spacing: 0) {
                // Top bar
                HStack {
                    // D23 Logo
                    HStack(spacing: 6) {
                        Text("D23")
                            .font(.system(size: 18, weight: .black, design: .rounded))
                            .foregroundStyle(
                                LinearGradient(
                                    colors: [pages[currentPage].color, pages[currentPage].secondaryColor],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                        Text("AI")
                            .font(.system(size: 14, weight: .bold, design: .rounded))
                            .foregroundColor(.secondary)
                    }

                    Spacer()

                    if currentPage < pages.count - 1 {
                        Button(action: completeOnboarding) {
                            Text("Skip")
                                .font(.subheadline)
                                .fontWeight(.medium)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 16)
                .frame(height: 50)

                // Page content with swipe gesture
                TabView(selection: $currentPage) {
                    ForEach(Array(pages.enumerated()), id: \.element.id) { index, page in
                        OnboardingPageView(
                            page: page,
                            isActive: currentPage == index,
                            isLastPage: index == pages.count - 1,
                            onGetStarted: completeOnboarding
                        )
                        .tag(index)
                    }
                }
                .tabViewStyle(.page(indexDisplayMode: .never))
                .animation(.spring(response: 0.5, dampingFraction: 0.8), value: currentPage)

                // Bottom navigation
                bottomNavigation
                    .padding(.bottom, 40)
            }
        }
    }

    // MARK: - Bottom Navigation

    private var bottomNavigation: some View {
        HStack(spacing: 20) {
            // Back button
            Button(action: previousPage) {
                ZStack {
                    Circle()
                        .fill(Color(.tertiarySystemBackground))
                        .frame(width: 50, height: 50)
                        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)

                    Image(systemName: "chevron.left")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(currentPage > 0 ? .primary : .secondary.opacity(0.3))
                }
            }
            .disabled(currentPage == 0)
            .opacity(currentPage > 0 ? 1 : 0.5)

            // Progress indicator
            HStack(spacing: 6) {
                ForEach(0..<pages.count, id: \.self) { index in
                    Capsule()
                        .fill(
                            index == currentPage
                            ? LinearGradient(
                                colors: [pages[currentPage].color, pages[currentPage].secondaryColor],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                            : LinearGradient(
                                colors: [Color.gray.opacity(0.3), Color.gray.opacity(0.3)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: index == currentPage ? 24 : 8, height: 8)
                        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: currentPage)
                        .onTapGesture {
                            goToPage(index)
                        }
                }
            }
            .frame(maxWidth: .infinity)

            // Next button
            Button(action: {
                if currentPage < pages.count - 1 {
                    nextPage()
                } else {
                    completeOnboarding()
                }
            }) {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [pages[currentPage].color, pages[currentPage].secondaryColor],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 56, height: 56)
                        .shadow(color: pages[currentPage].color.opacity(0.4), radius: 12, y: 6)

                    Image(systemName: currentPage < pages.count - 1 ? "chevron.right" : "checkmark")
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.white)
                }
            }
        }
        .padding(.horizontal, 32)
    }

    // MARK: - Navigation Actions

    private func nextPage() {
        let feedback = UIImpactFeedbackGenerator(style: .light)
        feedback.impactOccurred()
        withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
            currentPage = min(currentPage + 1, pages.count - 1)
        }
    }

    private func previousPage() {
        let feedback = UIImpactFeedbackGenerator(style: .light)
        feedback.impactOccurred()
        withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
            currentPage = max(currentPage - 1, 0)
        }
    }

    private func goToPage(_ index: Int) {
        let feedback = UIImpactFeedbackGenerator(style: .light)
        feedback.impactOccurred()
        withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
            currentPage = index
        }
    }

    private func completeOnboarding() {
        let feedback = UIImpactFeedbackGenerator(style: .medium)
        feedback.impactOccurred()
        withAnimation(.easeInOut(duration: 0.3)) {
            hasCompletedOnboarding = true
        }
    }
}

// MARK: - Onboarding Page View

private struct OnboardingPageView: View {
    let page: OnboardingPage
    let isActive: Bool
    let isLastPage: Bool
    let onGetStarted: () -> Void

    @State private var illustrationScale: CGFloat = 0.8
    @State private var illustrationOpacity: Double = 0
    @State private var illustrationOffset: CGFloat = 30
    @State private var contentOffset: CGFloat = 40
    @State private var contentOpacity: Double = 0
    @State private var featuresVisible: [Bool] = [false, false, false]
    @State private var buttonScale: CGFloat = 0.8
    @State private var buttonOpacity: Double = 0
    @State private var floatingOffset: CGFloat = 0

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 24) {
                Spacer(minLength: 20)

                // Custom illustration
                illustrationView
                    .scaleEffect(illustrationScale)
                    .opacity(illustrationOpacity)
                    .offset(y: illustrationOffset + floatingOffset)

                // Text content
                VStack(spacing: 12) {
                    Text(page.title)
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .multilineTextAlignment(.center)

                    Text(page.subtitle)
                        .font(.title3)
                        .fontWeight(.semibold)
                        .foregroundStyle(
                            LinearGradient(
                                colors: [page.color, page.secondaryColor],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )

                    Text(page.description)
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .lineSpacing(4)
                        .padding(.top, 4)
                }
                .padding(.horizontal, 32)
                .offset(y: contentOffset)
                .opacity(contentOpacity)

                // Feature cards
                featureCards
                    .padding(.top, 8)

                // Get Started button on last page
                if isLastPage {
                    getStartedButton
                        .padding(.top, 20)
                }

                Spacer(minLength: 120)
            }
        }
        .onAppear {
            if isActive {
                startAnimations()
            }
        }
        .onChange(of: isActive) { _, newValue in
            if newValue {
                resetAnimations()
                startAnimations()
            }
        }
    }

    // MARK: - Illustration View

    @ViewBuilder
    private var illustrationView: some View {
        switch page.illustration {
        case .aiAssistant:
            AIAssistantIllustration(primaryColor: page.color, secondaryColor: page.secondaryColor)
        case .astrology:
            AstrologyIllustration(primaryColor: page.color, secondaryColor: page.secondaryColor)
        case .travel:
            TravelIllustration(primaryColor: page.color, secondaryColor: page.secondaryColor)
        case .integrations:
            IntegrationsIllustration(primaryColor: page.color, secondaryColor: page.secondaryColor)
        }
    }

    // MARK: - Feature Cards

    private var featureCards: some View {
        HStack(spacing: 12) {
            ForEach(Array(page.features.enumerated()), id: \.element.id) { index, feature in
                FeatureCard(
                    feature: feature,
                    primaryColor: page.color,
                    secondaryColor: page.secondaryColor,
                    isVisible: featuresVisible.indices.contains(index) ? featuresVisible[index] : false,
                    delay: Double(index) * 0.1
                )
            }
        }
        .padding(.horizontal, 20)
    }

    // MARK: - Get Started Button

    private var getStartedButton: some View {
        Button(action: onGetStarted) {
            HStack(spacing: 12) {
                Text("Get Started")
                    .font(.headline)
                    .fontWeight(.bold)

                Image(systemName: "arrow.right")
                    .font(.system(size: 16, weight: .bold))
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .frame(height: 56)
            .background(
                LinearGradient(
                    colors: [page.color, page.secondaryColor],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .cornerRadius(16)
            .shadow(color: page.color.opacity(0.4), radius: 16, y: 8)
        }
        .padding(.horizontal, 32)
        .scaleEffect(buttonScale)
        .opacity(buttonOpacity)
    }

    // MARK: - Animation Helpers

    private func resetAnimations() {
        illustrationScale = 0.8
        illustrationOpacity = 0
        illustrationOffset = 30
        contentOffset = 40
        contentOpacity = 0
        featuresVisible = [false, false, false]
        buttonScale = 0.8
        buttonOpacity = 0
        floatingOffset = 0
    }

    private func startAnimations() {
        // Illustration entrance
        withAnimation(.spring(response: 0.7, dampingFraction: 0.7).delay(0.1)) {
            illustrationScale = 1.0
            illustrationOpacity = 1.0
            illustrationOffset = 0
        }

        // Content entrance
        withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(0.25)) {
            contentOffset = 0
            contentOpacity = 1.0
        }

        // Staggered feature animations
        for i in 0..<3 {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.4 + Double(i) * 0.1) {
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
                    if featuresVisible.indices.contains(i) {
                        featuresVisible[i] = true
                    }
                }
            }
        }

        // Button animation
        if isLastPage {
            withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(0.7)) {
                buttonScale = 1.0
                buttonOpacity = 1.0
            }
        }

        // Floating animation
        withAnimation(.easeInOut(duration: 3).repeatForever(autoreverses: true).delay(0.5)) {
            floatingOffset = -8
        }
    }
}

// MARK: - Feature Card

private struct FeatureCard: View {
    let feature: OnboardingFeature
    let primaryColor: Color
    let secondaryColor: Color
    let isVisible: Bool
    let delay: Double

    @State private var isHovered = false

    var body: some View {
        VStack(spacing: 10) {
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [primaryColor.opacity(0.15), secondaryColor.opacity(0.1)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 44, height: 44)

                Image(systemName: feature.icon)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [primaryColor, secondaryColor],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }

            Text(feature.text)
                .font(.caption)
                .fontWeight(.medium)
                .foregroundColor(.primary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .padding(.horizontal, 8)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(.secondarySystemBackground))
                .shadow(color: .black.opacity(0.03), radius: 8, y: 4)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(
                    LinearGradient(
                        colors: [primaryColor.opacity(0.2), secondaryColor.opacity(0.1)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 1
                )
        )
        .scaleEffect(isVisible ? 1 : 0.8)
        .opacity(isVisible ? 1 : 0)
    }
}

// MARK: - Custom Illustrations

private struct AIAssistantIllustration: View {
    let primaryColor: Color
    let secondaryColor: Color

    @State private var ringRotation: Double = 0
    @State private var pulseScale: CGFloat = 1.0
    @State private var particleOffset: CGFloat = 0

    var body: some View {
        ZStack {
            // Outer pulse rings
            ForEach(0..<3, id: \.self) { i in
                Circle()
                    .stroke(
                        LinearGradient(
                            colors: [primaryColor.opacity(0.3), secondaryColor.opacity(0.1)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 2
                    )
                    .frame(width: 160 + CGFloat(i * 35), height: 160 + CGFloat(i * 35))
                    .scaleEffect(pulseScale)
                    .opacity(Double(3 - i) / 5)
            }

            // Rotating gradient ring
            Circle()
                .stroke(
                    AngularGradient(
                        colors: [primaryColor, secondaryColor, primaryColor.opacity(0.3), primaryColor],
                        center: .center,
                        startAngle: .degrees(ringRotation),
                        endAngle: .degrees(ringRotation + 360)
                    ),
                    lineWidth: 4
                )
                .frame(width: 150, height: 150)

            // Glow
            Circle()
                .fill(
                    RadialGradient(
                        colors: [primaryColor.opacity(0.3), .clear],
                        center: .center,
                        startRadius: 30,
                        endRadius: 90
                    )
                )
                .frame(width: 180, height: 180)
                .blur(radius: 15)

            // Main circle
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [primaryColor, primaryColor.opacity(0.8)],
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
                VStack(spacing: 2) {
                    Text("D23")
                        .font(.system(size: 32, weight: .black, design: .rounded))
                        .foregroundColor(.white)

                    Text("AI")
                        .font(.system(size: 14, weight: .bold, design: .rounded))
                        .foregroundColor(.white.opacity(0.9))
                }
            }
            .shadow(color: primaryColor.opacity(0.5), radius: 20, y: 10)

            // Floating particles
            ForEach(0..<6, id: \.self) { i in
                Circle()
                    .fill(i % 2 == 0 ? primaryColor : secondaryColor)
                    .frame(width: 6, height: 6)
                    .offset(
                        x: cos(Double(i) * .pi / 3) * (90 + particleOffset),
                        y: sin(Double(i) * .pi / 3) * (90 + particleOffset)
                    )
                    .opacity(0.6)
            }
        }
        .frame(height: 280)
        .onAppear {
            withAnimation(.linear(duration: 12).repeatForever(autoreverses: false)) {
                ringRotation = 360
            }
            withAnimation(.easeInOut(duration: 2).repeatForever(autoreverses: true)) {
                pulseScale = 1.08
            }
            withAnimation(.easeInOut(duration: 3).repeatForever(autoreverses: true)) {
                particleOffset = 15
            }
        }
    }
}

private struct AstrologyIllustration: View {
    let primaryColor: Color
    let secondaryColor: Color

    @State private var moonRotation: Double = 0
    @State private var starsOpacity: Double = 0.3

    var body: some View {
        ZStack {
            // Outer constellation ring
            Circle()
                .stroke(
                    AngularGradient(
                        colors: [primaryColor.opacity(0.5), secondaryColor.opacity(0.3), primaryColor.opacity(0.5)],
                        center: .center
                    ),
                    style: StrokeStyle(lineWidth: 2, dash: [5, 5])
                )
                .frame(width: 220, height: 220)
                .rotationEffect(.degrees(moonRotation))

            // Stars
            ForEach(0..<8, id: \.self) { i in
                Image(systemName: "star.fill")
                    .font(.system(size: CGFloat.random(in: 6...12)))
                    .foregroundColor(i % 2 == 0 ? primaryColor : secondaryColor)
                    .offset(
                        x: cos(Double(i) * .pi / 4 + moonRotation / 100) * 100,
                        y: sin(Double(i) * .pi / 4 + moonRotation / 100) * 100
                    )
                    .opacity(starsOpacity + Double(i % 3) * 0.2)
            }

            // Glow
            Circle()
                .fill(
                    RadialGradient(
                        colors: [primaryColor.opacity(0.25), .clear],
                        center: .center,
                        startRadius: 20,
                        endRadius: 100
                    )
                )
                .frame(width: 200, height: 200)
                .blur(radius: 20)

            // Moon circle
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [primaryColor, secondaryColor],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 110, height: 110)

                Image(systemName: "moon.stars.fill")
                    .font(.system(size: 50, weight: .medium))
                    .foregroundColor(.white)
            }
            .shadow(color: primaryColor.opacity(0.5), radius: 20, y: 8)
        }
        .frame(height: 280)
        .onAppear {
            withAnimation(.linear(duration: 30).repeatForever(autoreverses: false)) {
                moonRotation = 360
            }
            withAnimation(.easeInOut(duration: 2).repeatForever(autoreverses: true)) {
                starsOpacity = 0.8
            }
        }
    }
}

private struct TravelIllustration: View {
    let primaryColor: Color
    let secondaryColor: Color

    @State private var trainOffset: CGFloat = -200
    @State private var trackDash: CGFloat = 0

    var body: some View {
        ZStack {
            // Track lines
            ForEach(0..<3, id: \.self) { i in
                RoundedRectangle(cornerRadius: 2)
                    .fill(
                        LinearGradient(
                            colors: [primaryColor.opacity(0.3), secondaryColor.opacity(0.1)],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .frame(width: 250, height: 3)
                    .offset(y: CGFloat(i - 1) * 50)
            }

            // Animated dashes on track
            Path { path in
                path.move(to: CGPoint(x: -125, y: 0))
                path.addLine(to: CGPoint(x: 125, y: 0))
            }
            .stroke(
                primaryColor.opacity(0.5),
                style: StrokeStyle(lineWidth: 2, dash: [10, 10], dashPhase: trackDash)
            )

            // Glow
            Circle()
                .fill(
                    RadialGradient(
                        colors: [primaryColor.opacity(0.25), .clear],
                        center: .center,
                        startRadius: 20,
                        endRadius: 100
                    )
                )
                .frame(width: 200, height: 200)
                .blur(radius: 20)

            // Main circle with train icon
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [primaryColor, secondaryColor],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 110, height: 110)

                Image(systemName: "train.side.front.car")
                    .font(.system(size: 45, weight: .medium))
                    .foregroundColor(.white)
            }
            .shadow(color: primaryColor.opacity(0.5), radius: 20, y: 8)

            // Location pins
            ForEach(0..<2, id: \.self) { i in
                Image(systemName: "mappin.circle.fill")
                    .font(.system(size: 24))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [primaryColor, secondaryColor],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .offset(x: i == 0 ? -100 : 100, y: 0)
            }
        }
        .frame(height: 280)
        .onAppear {
            withAnimation(.linear(duration: 1).repeatForever(autoreverses: false)) {
                trackDash = 20
            }
        }
    }
}

private struct IntegrationsIllustration: View {
    let primaryColor: Color
    let secondaryColor: Color

    @State private var connectionPulse: CGFloat = 1.0
    @State private var iconRotation: Double = 0

    var body: some View {
        ZStack {
            // Connection lines
            ForEach(0..<4, id: \.self) { i in
                let angle = Double(i) * 90.0
                Path { path in
                    path.move(to: CGPoint(x: 0, y: 0))
                    path.addLine(to: CGPoint(
                        x: cos(angle * .pi / 180) * 80,
                        y: sin(angle * .pi / 180) * 80
                    ))
                }
                .stroke(
                    LinearGradient(
                        colors: [primaryColor.opacity(0.5), secondaryColor.opacity(0.2)],
                        startPoint: .center,
                        endPoint: UnitPoint(
                            x: 0.5 + cos(angle * .pi / 180) * 0.5,
                            y: 0.5 + sin(angle * .pi / 180) * 0.5
                        )
                    ),
                    lineWidth: 2
                )
                .scaleEffect(connectionPulse)
            }

            // Outer icons
            ForEach(0..<4, id: \.self) { i in
                let icons = ["message.fill", "doc.text.fill", "calendar", "cloud.fill"]
                let angle = Double(i) * 90.0

                ZStack {
                    Circle()
                        .fill(Color(.secondarySystemBackground))
                        .frame(width: 44, height: 44)
                        .shadow(color: .black.opacity(0.1), radius: 8, y: 4)

                    Image(systemName: icons[i])
                        .font(.system(size: 18, weight: .medium))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [primaryColor, secondaryColor],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }
                .offset(
                    x: cos(angle * .pi / 180) * 90,
                    y: sin(angle * .pi / 180) * 90
                )
            }

            // Glow
            Circle()
                .fill(
                    RadialGradient(
                        colors: [primaryColor.opacity(0.25), .clear],
                        center: .center,
                        startRadius: 20,
                        endRadius: 80
                    )
                )
                .frame(width: 160, height: 160)
                .blur(radius: 15)

            // Central hub
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [primaryColor, secondaryColor],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 100, height: 100)

                Image(systemName: "square.stack.3d.up.fill")
                    .font(.system(size: 40, weight: .medium))
                    .foregroundColor(.white)
                    .rotationEffect(.degrees(iconRotation))
            }
            .shadow(color: primaryColor.opacity(0.5), radius: 20, y: 8)
        }
        .frame(height: 280)
        .onAppear {
            withAnimation(.easeInOut(duration: 2).repeatForever(autoreverses: true)) {
                connectionPulse = 1.1
            }
            withAnimation(.easeInOut(duration: 4).repeatForever(autoreverses: true)) {
                iconRotation = 10
            }
        }
    }
}

// MARK: - Animated Background

private struct AnimatedOnboardingBackground: View {
    let primaryColor: Color
    let secondaryColor: Color

    @State private var floatOffset1: CGFloat = 0
    @State private var floatOffset2: CGFloat = 0
    @State private var floatOffset3: CGFloat = 0

    var body: some View {
        ZStack {
            Color(.systemBackground)
                .ignoresSafeArea()

            GeometryReader { geo in
                ZStack {
                    // Top orb
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [primaryColor.opacity(0.2), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 200
                            )
                        )
                        .frame(width: 400, height: 400)
                        .offset(x: -100, y: floatOffset1 - 100)
                        .blur(radius: 60)

                    // Bottom orb
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [secondaryColor.opacity(0.15), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 180
                            )
                        )
                        .frame(width: 360, height: 360)
                        .offset(x: 120, y: geo.size.height - floatOffset2 - 180)
                        .blur(radius: 50)

                    // Center accent
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [primaryColor.opacity(0.1), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 140
                            )
                        )
                        .frame(width: 280, height: 280)
                        .offset(x: 30, y: floatOffset3 + geo.size.height * 0.3)
                        .blur(radius: 40)
                }
            }
            .ignoresSafeArea()
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 4).repeatForever(autoreverses: true)) {
                floatOffset1 = 40
            }
            withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true).delay(0.3)) {
                floatOffset2 = 50
            }
            withAnimation(.easeInOut(duration: 3.5).repeatForever(autoreverses: true).delay(0.6)) {
                floatOffset3 = 30
            }
        }
        .animation(.easeInOut(duration: 0.5), value: primaryColor)
        .animation(.easeInOut(duration: 0.5), value: secondaryColor)
    }
}

// MARK: - Previews

#Preview("Onboarding View") {
    OnboardingView()
}

#Preview("AI Illustration") {
    AIAssistantIllustration(primaryColor: Color(red: 0.35, green: 0.15, blue: 0.85), secondaryColor: .cyan)
        .frame(height: 300)
        .background(Color(.systemBackground))
}

#Preview("Feature Card") {
    FeatureCard(
        feature: OnboardingFeature(icon: "sparkles", text: "Smart AI"),
        primaryColor: .purple,
        secondaryColor: .cyan,
        isVisible: true,
        delay: 0
    )
    .frame(width: 120)
    .padding()
}
