import SwiftUI
import StoreKit

/// View for managing subscriptions with themed styling and animations
struct SubscriptionView: View {
    @StateObject private var manager = SubscriptionManager.shared
    @ObservedObject private var theme = ThemeManager.shared
    @Environment(\.dismiss) private var dismiss

    @State private var isPurchasing = false
    @State private var showError = false
    @State private var errorMessage = ""

    // Animation states
    @State private var headerAppeared = false
    @State private var statusAppeared = false
    @State private var featuresAppeared = false
    @State private var plansAppeared = false
    @State private var crownRotation: Double = 0
    @State private var glowPulse = false
    @State private var shimmerOffset: CGFloat = -300

    var body: some View {
        NavigationStack {
            ZStack {
                // Animated premium background
                AnimatedPremiumBackground()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 28) {
                        // Header
                        headerSection

                        // Current status
                        currentStatusSection

                        // Features list
                        featuresSection

                        // Subscription options
                        if !manager.subscriptionStatus.isActive {
                            subscriptionOptionsSection
                        }

                        // Restore purchases
                        restoreSection

                        // Terms
                        termsSection

                        Spacer(minLength: 40)
                    }
                    .padding()
                }
            }
            .navigationTitle("Premium")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                    .foregroundColor(theme.primaryColor)
                }
            }
            .alert("Error", isPresented: $showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(errorMessage)
            }
            .task {
                await manager.loadProducts()
            }
            .onAppear {
                startAnimations()
            }
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        VStack(spacing: 20) {
            ZStack {
                // Outer glow rings
                ForEach(0..<3, id: \.self) { i in
                    Circle()
                        .stroke(
                            LinearGradient(
                                colors: [.purple.opacity(0.3), .pink.opacity(0.3)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 2
                        )
                        .frame(width: 80 + CGFloat(i * 25), height: 80 + CGFloat(i * 25))
                        .scaleEffect(glowPulse ? 1.1 : 1.0)
                        .opacity(glowPulse ? 0 : 0.5)
                        .animation(
                            .easeOut(duration: 2)
                            .repeatForever(autoreverses: false)
                            .delay(Double(i) * 0.3),
                            value: glowPulse
                        )
                }

                // Rotating gradient ring
                Circle()
                    .stroke(
                        AngularGradient(
                            colors: [.purple, .pink, .orange, .purple],
                            center: .center,
                            startAngle: .degrees(crownRotation),
                            endAngle: .degrees(crownRotation + 360)
                        ),
                        lineWidth: 4
                    )
                    .frame(width: 100, height: 100)

                // Main circle with crown
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [.purple, .pink],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 85, height: 85)

                    Image(systemName: "crown.fill")
                        .font(.system(size: 40))
                        .foregroundColor(.white)
                        .shadow(color: .black.opacity(0.2), radius: 2, y: 2)
                }
                .shadow(color: .purple.opacity(0.5), radius: 20, y: 8)
            }

            VStack(spacing: 8) {
                Text("OhGrt Premium")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.primary, .primary.opacity(0.8)],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )

                Text("Unlock all features and get unlimited access")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }

            // Premium pills
            HStack(spacing: 10) {
                ThemedPillBadge(text: "Unlimited", icon: "infinity", color: .purple)
                ThemedPillBadge(text: "No Ads", icon: "xmark.circle.fill", color: .orange)
                ThemedPillBadge(text: "Priority", icon: "bolt.fill", color: .pink)
            }
        }
        .padding(.top, 20)
        .scaleEffect(headerAppeared ? 1.0 : 0.8)
        .opacity(headerAppeared ? 1.0 : 0)
    }

    // MARK: - Current Status Section

    private var currentStatusSection: some View {
        HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: manager.subscriptionStatus.isActive ?
                                [.green.opacity(0.2), .green.opacity(0.1)] :
                                [.gray.opacity(0.2), .gray.opacity(0.1)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 50, height: 50)

                Image(systemName: manager.subscriptionStatus.isActive ? "checkmark.seal.fill" : "seal")
                    .font(.system(size: 24))
                    .foregroundStyle(
                        manager.subscriptionStatus.isActive ?
                            LinearGradient(colors: [.green, .green.opacity(0.7)], startPoint: .topLeading, endPoint: .bottomTrailing) :
                            LinearGradient(colors: [.secondary, .secondary.opacity(0.7)], startPoint: .topLeading, endPoint: .bottomTrailing)
                    )
                    .symbolEffect(.pulse, options: manager.subscriptionStatus.isActive ? .repeating : .nonRepeating)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text("Current Plan")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(manager.subscriptionStatus.displayName)
                    .font(.headline)
                    .fontWeight(.semibold)
            }

            Spacer()

            if case .subscribed(_, let expiresDate) = manager.subscriptionStatus,
               let date = expiresDate {
                VStack(alignment: .trailing, spacing: 4) {
                    Text("Renews")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(date, style: .date)
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundStyle(
                            LinearGradient(
                                colors: [.purple, .pink],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                }
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(ThemeManager.CornerRadius.large)
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
        .offset(y: statusAppeared ? 0 : 20)
        .opacity(statusAppeared ? 1.0 : 0)
    }

    // MARK: - Features Section

    private var featuresSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                ThemedGradientIcon(systemName: "star.fill", size: 18, colors: [.purple, .pink])
                Text("Premium Features")
                    .font(.headline)
                    .fontWeight(.semibold)
            }

            VStack(spacing: 14) {
                AnimatedFeatureRow(
                    icon: "sparkles",
                    title: "Unlimited Astrology",
                    description: "Unlimited horoscopes, kundli, and predictions",
                    color: .purple,
                    index: 0,
                    isVisible: featuresAppeared
                )
                AnimatedFeatureRow(
                    icon: "train.side.front.car",
                    title: "Travel Tools",
                    description: "PNR status, train tracking, and more",
                    color: .blue,
                    index: 1,
                    isVisible: featuresAppeared
                )
                AnimatedFeatureRow(
                    icon: "message.fill",
                    title: "Priority Support",
                    description: "Get faster responses from our AI",
                    color: .green,
                    index: 2,
                    isVisible: featuresAppeared
                )
                AnimatedFeatureRow(
                    icon: "xmark.circle.fill",
                    title: "No Ads",
                    description: "Enjoy an ad-free experience",
                    color: .orange,
                    index: 3,
                    isVisible: featuresAppeared
                )
                AnimatedFeatureRow(
                    icon: "clock.arrow.circlepath",
                    title: "History Access",
                    description: "Access your complete chat history",
                    color: .pink,
                    index: 4,
                    isVisible: featuresAppeared
                )
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(ThemeManager.CornerRadius.large)
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
    }

    // MARK: - Subscription Options Section

    private var subscriptionOptionsSection: some View {
        VStack(spacing: 16) {
            HStack {
                ThemedGradientIcon(systemName: "creditcard.fill", size: 18, colors: [.blue, .purple])
                Text("Choose Your Plan")
                    .font(.headline)
                    .fontWeight(.semibold)
            }

            if manager.isLoading {
                VStack(spacing: 12) {
                    ProgressView()
                        .scaleEffect(1.2)
                    Text("Loading plans...")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .frame(height: 150)
            } else if manager.products.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.largeTitle)
                        .foregroundColor(.orange)
                    Text("Unable to load subscription options")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                .frame(height: 150)
            } else {
                ForEach(Array(manager.products.enumerated()), id: \.element.id) { index, product in
                    AnimatedSubscriptionOptionCard(
                        product: product,
                        isPopular: product.id.contains("yearly"),
                        isPurchasing: isPurchasing,
                        index: index,
                        isVisible: plansAppeared,
                        shimmerOffset: shimmerOffset
                    ) {
                        await purchaseProduct(product)
                    }
                }
            }
        }
    }

    // MARK: - Restore Section

    private var restoreSection: some View {
        Button {
            let feedback = UIImpactFeedbackGenerator(style: .light)
            feedback.impactOccurred()
            Task {
                await manager.restorePurchases()
            }
        } label: {
            HStack(spacing: 8) {
                Image(systemName: "arrow.clockwise")
                    .font(.subheadline)
                Text("Restore Purchases")
                    .font(.subheadline)
                    .fontWeight(.medium)
            }
            .foregroundColor(theme.primaryColor)
        }
        .disabled(manager.isLoading)
        .opacity(manager.isLoading ? 0.5 : 1.0)
    }

    // MARK: - Terms Section

    private var termsSection: some View {
        VStack(spacing: 12) {
            Text("Subscription Terms")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.secondary)

            Text("Subscriptions automatically renew unless cancelled at least 24 hours before the end of the current period. You can manage and cancel your subscriptions in your App Store account settings.")
                .font(.caption2)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .lineSpacing(2)

            HStack(spacing: 20) {
                Link(destination: URL(string: "https://ohgrt.com/privacy")!) {
                    HStack(spacing: 4) {
                        Image(systemName: "hand.raised.fill")
                            .font(.caption2)
                        Text("Privacy Policy")
                            .font(.caption2)
                    }
                    .foregroundColor(theme.primaryColor)
                }

                Link(destination: URL(string: "https://ohgrt.com/terms")!) {
                    HStack(spacing: 4) {
                        Image(systemName: "doc.text.fill")
                            .font(.caption2)
                        Text("Terms of Service")
                            .font(.caption2)
                    }
                    .foregroundColor(theme.primaryColor)
                }
            }
        }
        .padding(.top, 16)
    }

    // MARK: - Actions

    private func purchaseProduct(_ product: Product) async {
        isPurchasing = true
        defer { isPurchasing = false }

        do {
            let success = try await manager.purchase(product)
            if success {
                let feedback = UINotificationFeedbackGenerator()
                feedback.notificationOccurred(.success)
            }
        } catch {
            errorMessage = "Purchase failed: \(error.localizedDescription)"
            showError = true
        }
    }

    // MARK: - Animations

    private func startAnimations() {
        withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(0.1)) {
            headerAppeared = true
        }

        withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(0.3)) {
            statusAppeared = true
        }

        withAnimation(.easeOut(duration: 0.5).delay(0.4)) {
            featuresAppeared = true
        }

        withAnimation(.easeOut(duration: 0.5).delay(0.6)) {
            plansAppeared = true
        }

        // Continuous animations
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            glowPulse = true

            withAnimation(.linear(duration: 8).repeatForever(autoreverses: false)) {
                crownRotation = 360
            }

            withAnimation(.linear(duration: 3).repeatForever(autoreverses: false)) {
                shimmerOffset = 400
            }
        }
    }
}

// MARK: - Animated Feature Row

struct AnimatedFeatureRow: View {
    let icon: String
    let title: String
    let description: String
    let color: Color
    let index: Int
    let isVisible: Bool

    @State private var appeared = false
    @State private var checkmarkScale: CGFloat = 0

    var body: some View {
        HStack(spacing: 14) {
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(
                        LinearGradient(
                            colors: [color.opacity(0.2), color.opacity(0.1)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 44, height: 44)

                Image(systemName: icon)
                    .font(.system(size: 20, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [color, color.opacity(0.7)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }

            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }

            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 22))
                .foregroundColor(.green)
                .scaleEffect(checkmarkScale)
        }
        .offset(x: appeared ? 0 : -20)
        .opacity(appeared ? 1 : 0)
        .onAppear {
            if isVisible {
                let delay = Double(index) * 0.08
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(delay)) {
                    appeared = true
                }
                withAnimation(.spring(response: 0.4, dampingFraction: 0.5).delay(delay + 0.2)) {
                    checkmarkScale = 1.0
                }
            }
        }
        .onChange(of: isVisible) { _, newValue in
            if newValue && !appeared {
                let delay = Double(index) * 0.08
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(delay)) {
                    appeared = true
                }
                withAnimation(.spring(response: 0.4, dampingFraction: 0.5).delay(delay + 0.2)) {
                    checkmarkScale = 1.0
                }
            }
        }
    }
}

// MARK: - Animated Subscription Option Card

struct AnimatedSubscriptionOptionCard: View {
    let product: Product
    let isPopular: Bool
    let isPurchasing: Bool
    let index: Int
    let isVisible: Bool
    let shimmerOffset: CGFloat
    let onPurchase: () async -> Void

    @State private var appeared = false
    @State private var buttonPressed = false

    var body: some View {
        VStack(spacing: 14) {
            // Popular badge
            if isPopular {
                HStack {
                    Spacer()
                    HStack(spacing: 4) {
                        Image(systemName: "star.fill")
                            .font(.caption2)
                        Text("BEST VALUE")
                            .font(.caption2)
                            .fontWeight(.bold)
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(
                        LinearGradient(
                            colors: [.orange, .pink],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(6)
                }
            }

            HStack {
                VStack(alignment: .leading, spacing: 6) {
                    Text(product.displayName)
                        .font(.headline)
                        .fontWeight(.semibold)

                    Text(product.periodDescription)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    Text(product.displayPrice)
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundStyle(
                            LinearGradient(
                                colors: isPopular ? [.orange, .pink] : [.purple, .blue],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )

                    if let monthlyPrice = product.monthlyEquivalentPrice {
                        Text("\(monthlyPrice)/mo")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }

            // Subscribe button
            Button {
                let feedback = UIImpactFeedbackGenerator(style: .medium)
                feedback.impactOccurred()

                withAnimation(ThemeManager.AnimationSettings.quickSpring) {
                    buttonPressed = true
                }
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                    withAnimation(ThemeManager.AnimationSettings.quickSpring) {
                        buttonPressed = false
                    }
                }

                Task {
                    await onPurchase()
                }
            } label: {
                HStack(spacing: 8) {
                    if isPurchasing {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        Image(systemName: "crown.fill")
                            .font(.subheadline)
                        Text("Subscribe")
                            .fontWeight(.semibold)
                    }
                }
                .frame(maxWidth: .infinity)
                .frame(height: 48)
                .background(
                    ZStack {
                        LinearGradient(
                            colors: isPopular ? [.orange, .pink] : [.purple, .blue],
                            startPoint: .leading,
                            endPoint: .trailing
                        )

                        // Shimmer effect
                        if !isPurchasing {
                            LinearGradient(
                                colors: [.clear, .white.opacity(0.3), .clear],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                            .offset(x: shimmerOffset)
                        }
                    }
                )
                .foregroundColor(.white)
                .cornerRadius(ThemeManager.CornerRadius.medium)
                .shadow(
                    color: isPopular ? .orange.opacity(0.3) : .purple.opacity(0.3),
                    radius: 8,
                    y: 4
                )
            }
            .disabled(isPurchasing)
            .scaleEffect(buttonPressed ? 0.96 : 1.0)
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(ThemeManager.CornerRadius.large)
        .overlay(
            RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.large)
                .stroke(
                    isPopular ?
                        LinearGradient(colors: [.orange, .pink], startPoint: .topLeading, endPoint: .bottomTrailing) :
                        LinearGradient(colors: [Color.clear], startPoint: .topLeading, endPoint: .bottomTrailing),
                    lineWidth: 2
                )
        )
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
        .scaleEffect(appeared ? 1.0 : 0.9)
        .opacity(appeared ? 1.0 : 0)
        .offset(y: appeared ? 0 : 20)
        .onAppear {
            if isVisible {
                let delay = Double(index) * 0.1
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(delay)) {
                    appeared = true
                }
            }
        }
        .onChange(of: isVisible) { _, newValue in
            if newValue && !appeared {
                let delay = Double(index) * 0.1
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(delay)) {
                    appeared = true
                }
            }
        }
    }
}

// MARK: - Animated Premium Background

private struct AnimatedPremiumBackground: View {
    @State private var animate = false

    var body: some View {
        ZStack {
            Color(.systemBackground)
                .ignoresSafeArea()

            // Gradient overlay
            LinearGradient(
                colors: [
                    .purple.opacity(0.05),
                    .clear,
                    .pink.opacity(0.03),
                    .clear
                ],
                startPoint: animate ? .topLeading : .bottomTrailing,
                endPoint: animate ? .bottomTrailing : .topLeading
            )
            .ignoresSafeArea()

            // Floating orbs
            GeometryReader { geo in
                ZStack {
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [.purple.opacity(0.15), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 150
                            )
                        )
                        .frame(width: 300, height: 300)
                        .offset(x: -100, y: animate ? -50 : 0)
                        .blur(radius: 50)

                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [.pink.opacity(0.12), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 120
                            )
                        )
                        .frame(width: 250, height: 250)
                        .offset(x: 120, y: geo.size.height - (animate ? 200 : 250))
                        .blur(radius: 40)

                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [.orange.opacity(0.1), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 100
                            )
                        )
                        .frame(width: 200, height: 200)
                        .offset(x: 80, y: animate ? 300 : 350)
                        .blur(radius: 35)
                }
            }
            .ignoresSafeArea()
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 6).repeatForever(autoreverses: true)) {
                animate = true
            }
        }
    }
}

// MARK: - Previews

#Preview("Subscription View") {
    SubscriptionView()
}

#Preview("Feature Row") {
    VStack(spacing: 14) {
        AnimatedFeatureRow(
            icon: "sparkles",
            title: "Unlimited Astrology",
            description: "Unlimited horoscopes, kundli, and predictions",
            color: .purple,
            index: 0,
            isVisible: true
        )
        AnimatedFeatureRow(
            icon: "train.side.front.car",
            title: "Travel Tools",
            description: "PNR status, train tracking, and more",
            color: .blue,
            index: 1,
            isVisible: true
        )
        AnimatedFeatureRow(
            icon: "message.fill",
            title: "Priority Support",
            description: "Get faster responses from our AI",
            color: .green,
            index: 2,
            isVisible: true
        )
    }
    .padding()
    .background(Color(.secondarySystemBackground))
    .cornerRadius(16)
    .padding()
}

#Preview("Premium Background") {
    ZStack {
        AnimatedPremiumBackground()
        Text("Premium Content")
            .font(.title)
    }
}
