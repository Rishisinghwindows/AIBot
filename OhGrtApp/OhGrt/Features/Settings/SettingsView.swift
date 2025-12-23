import SwiftUI

/// Settings view with theme customization and app preferences
struct SettingsView: View {
    @ObservedObject private var theme = ThemeManager.shared
    @Environment(\.dismiss) private var dismiss

    // Animation states
    @State private var headerScale: CGFloat = 0.8
    @State private var headerOpacity: Double = 0
    @State private var sectionsAppeared = false
    @State private var selectedThemeScale: [AccentTheme: CGFloat] = [:]
    @State private var rotationAngle: Double = 0
    @State private var glowPulse = false

    @State private var showingProfile = false
    @State private var showingPersonas = false

    var body: some View {
        NavigationStack {
            ZStack {
                // Animated background
                AnimatedSettingsBackground()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 24) {
                        // Header
                        headerSection
                            .padding(.top, 20)

                        // Account Section
                        accountSection

                        // Theme Selection
                        themeSelectionSection

                        // Appearance Mode
                        appearanceModeSection

                        // App Info
                        appInfoSection

                        Spacer(minLength: 40)
                    }
                    .padding(.horizontal, 20)
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title3)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .sheet(isPresented: $showingProfile) {
                ProfileView()
            }
            .sheet(isPresented: $showingPersonas) {
                PersonasView()
            }
        }
        .onAppear {
            startAnimations()
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        VStack(spacing: 16) {
            // Animated icon
            ZStack {
                // Outer glow rings
                ForEach(0..<3, id: \.self) { i in
                    Circle()
                        .stroke(
                            theme.primaryGradient,
                            lineWidth: 2
                        )
                        .frame(width: 90 + CGFloat(i * 20), height: 90 + CGFloat(i * 20))
                        .scaleEffect(glowPulse ? 1.1 : 1.0)
                        .opacity(glowPulse ? 0 : 0.3)
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
                            colors: theme.accentTheme.primaryColors + [theme.accentTheme.primaryColors[0]],
                            center: .center,
                            startAngle: .degrees(rotationAngle),
                            endAngle: .degrees(rotationAngle + 360)
                        ),
                        lineWidth: 3
                    )
                    .frame(width: 95, height: 95)

                // Main icon circle
                ZStack {
                    Circle()
                        .fill(theme.primaryGradient)
                        .frame(width: 80, height: 80)

                    Image(systemName: "paintbrush.fill")
                        .font(.system(size: 32, weight: .medium))
                        .foregroundColor(.white)
                }
                .shadow(color: theme.primaryColor.opacity(0.4), radius: 15, y: 8)
            }
            .scaleEffect(headerScale)
            .opacity(headerOpacity)

            VStack(spacing: 6) {
                Text("Customize Your Theme")
                    .font(.title2)
                    .fontWeight(.bold)

                Text("Personalize the look and feel of OhGrt")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .opacity(headerOpacity)
        }
    }

    // MARK: - Account Section

    private var accountSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            SectionHeader(title: "Account", icon: "person.circle.fill")
                .opacity(sectionsAppeared ? 1 : 0)
                .offset(x: sectionsAppeared ? 0 : -20)

            VStack(spacing: 12) {
                // Profile Button
                Button {
                    showingProfile = true
                } label: {
                    HStack {
                        ZStack {
                            RoundedRectangle(cornerRadius: 10)
                                .fill(theme.primaryGradient)
                                .frame(width: 40, height: 40)

                            Image(systemName: "person.fill")
                                .font(.system(size: 18))
                                .foregroundColor(.white)
                        }

                        VStack(alignment: .leading, spacing: 2) {
                            Text("Profile")
                                .font(.subheadline)
                                .fontWeight(.medium)
                                .foregroundColor(.primary)
                            Text("Manage your personal info")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        Spacer()

                        Image(systemName: "chevron.right")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.secondary)
                    }
                }

                Divider()

                // Personas Button
                Button {
                    showingPersonas = true
                } label: {
                    HStack {
                        ZStack {
                            RoundedRectangle(cornerRadius: 10)
                                .fill(
                                    LinearGradient(
                                        colors: [.purple, .pink],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 40, height: 40)

                            Image(systemName: "person.2.fill")
                                .font(.system(size: 16))
                                .foregroundColor(.white)
                        }

                        VStack(alignment: .leading, spacing: 2) {
                            Text("AI Personas")
                                .font(.subheadline)
                                .fontWeight(.medium)
                                .foregroundColor(.primary)
                            Text("Create shareable AI versions of you")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        Spacer()

                        Image(systemName: "chevron.right")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.large)
                .fill(Color(.secondarySystemBackground))
                .shadow(color: .black.opacity(0.05), radius: 10, y: 5)
        )
        .opacity(sectionsAppeared ? 1 : 0)
        .offset(y: sectionsAppeared ? 0 : 20)
    }

    // MARK: - Theme Selection Section

    private var themeSelectionSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            SectionHeader(title: "Accent Color", icon: "paintpalette.fill")
                .opacity(sectionsAppeared ? 1 : 0)
                .offset(x: sectionsAppeared ? 0 : -20)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 14) {
                ForEach(Array(AccentTheme.allCases.enumerated()), id: \.element.id) { index, accentTheme in
                    ThemeColorCard(
                        accentTheme: accentTheme,
                        isSelected: theme.accentTheme == accentTheme,
                        index: index,
                        isVisible: sectionsAppeared
                    ) {
                        withAnimation(ThemeManager.AnimationSettings.spring) {
                            theme.accentTheme = accentTheme
                        }
                        let feedback = UIImpactFeedbackGenerator(style: .light)
                        feedback.impactOccurred()
                    }
                }
            }
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.large)
                .fill(Color(.secondarySystemBackground))
                .shadow(color: .black.opacity(0.05), radius: 10, y: 5)
        )
        .opacity(sectionsAppeared ? 1 : 0)
        .offset(y: sectionsAppeared ? 0 : 20)
    }

    // MARK: - Appearance Mode Section

    private var appearanceModeSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            SectionHeader(title: "Appearance", icon: "circle.lefthalf.filled")
                .opacity(sectionsAppeared ? 1 : 0)
                .offset(x: sectionsAppeared ? 0 : -20)

            HStack(spacing: 12) {
                AppearanceModeButton(
                    mode: nil,
                    title: "System",
                    icon: "iphone",
                    isSelected: theme.colorScheme == nil
                ) {
                    withAnimation(ThemeManager.AnimationSettings.spring) {
                        theme.colorScheme = nil
                    }
                }

                AppearanceModeButton(
                    mode: .light,
                    title: "Light",
                    icon: "sun.max.fill",
                    isSelected: theme.colorScheme == .light
                ) {
                    withAnimation(ThemeManager.AnimationSettings.spring) {
                        theme.colorScheme = .light
                    }
                }

                AppearanceModeButton(
                    mode: .dark,
                    title: "Dark",
                    icon: "moon.fill",
                    isSelected: theme.colorScheme == .dark
                ) {
                    withAnimation(ThemeManager.AnimationSettings.spring) {
                        theme.colorScheme = .dark
                    }
                }
            }
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.large)
                .fill(Color(.secondarySystemBackground))
                .shadow(color: .black.opacity(0.05), radius: 10, y: 5)
        )
        .opacity(sectionsAppeared ? 1 : 0)
        .offset(y: sectionsAppeared ? 0 : 20)
        .animation(ThemeManager.AnimationSettings.spring.delay(0.1), value: sectionsAppeared)
    }

    // MARK: - App Info Section

    private var appInfoSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            SectionHeader(title: "About", icon: "info.circle.fill")

            VStack(spacing: 12) {
                InfoRow(title: "Version", value: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0")
                InfoRow(title: "Build", value: Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1")

                Divider()
                    .padding(.vertical, 4)

                // Reset Onboarding Button
                ResetOnboardingButton()
            }
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.large)
                .fill(Color(.secondarySystemBackground))
                .shadow(color: .black.opacity(0.05), radius: 10, y: 5)
        )
        .opacity(sectionsAppeared ? 1 : 0)
        .offset(y: sectionsAppeared ? 0 : 20)
        .animation(ThemeManager.AnimationSettings.spring.delay(0.2), value: sectionsAppeared)
    }

    // MARK: - Animations

    private func startAnimations() {
        // Header entrance
        withAnimation(.spring(response: 0.7, dampingFraction: 0.6).delay(0.1)) {
            headerScale = 1.0
            headerOpacity = 1.0
        }

        // Sections entrance
        withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(0.3)) {
            sectionsAppeared = true
        }

        // Start continuous animations
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            glowPulse = true

            withAnimation(.linear(duration: 8).repeatForever(autoreverses: false)) {
                rotationAngle = 360
            }
        }
    }
}

// MARK: - Section Header

private struct SectionHeader: View {
    let title: String
    let icon: String

    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(theme.primaryGradient)

            Text(title)
                .font(.headline)
                .fontWeight(.semibold)
        }
    }
}

// MARK: - Theme Color Card

private struct ThemeColorCard: View {
    let accentTheme: AccentTheme
    let isSelected: Bool
    let index: Int
    let isVisible: Bool
    let action: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button(action: action) {
            VStack(spacing: 10) {
                ZStack {
                    // Background gradient circle
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: accentTheme.primaryColors,
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 50, height: 50)
                        .shadow(color: accentTheme.primary.opacity(0.4), radius: isSelected ? 10 : 5, y: 4)

                    // Icon
                    Image(systemName: accentTheme.icon)
                        .font(.system(size: 20, weight: .medium))
                        .foregroundColor(.white)

                    // Selection ring
                    if isSelected {
                        Circle()
                            .stroke(accentTheme.primary, lineWidth: 3)
                            .frame(width: 62, height: 62)
                    }
                }

                Text(accentTheme.displayName)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(isSelected ? accentTheme.primary : .secondary)
            }
            .padding(.vertical, 12)
            .frame(maxWidth: .infinity)
            .background(
                RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.medium)
                    .fill(isSelected ? accentTheme.primary.opacity(0.1) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.medium)
                    .stroke(isSelected ? accentTheme.primary.opacity(0.3) : Color.clear, lineWidth: 1)
            )
        }
        .buttonStyle(ScaleButtonStyle())
        .opacity(isVisible ? 1 : 0)
        .offset(y: isVisible ? 0 : 20)
        .animation(
            ThemeManager.AnimationSettings.staggered(index: index, baseDelay: 0.05),
            value: isVisible
        )
    }
}

// MARK: - Appearance Mode Button

private struct AppearanceModeButton: View {
    let mode: ColorScheme?
    let title: String
    let icon: String
    let isSelected: Bool
    let action: () -> Void

    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        Button(action: {
            action()
            let feedback = UIImpactFeedbackGenerator(style: .light)
            feedback.impactOccurred()
        }) {
            VStack(spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(isSelected ? theme.primaryGradient : LinearGradient(colors: [Color(.tertiarySystemBackground)], startPoint: .top, endPoint: .bottom))
                        .frame(width: 48, height: 48)

                    Image(systemName: icon)
                        .font(.system(size: 20, weight: .medium))
                        .foregroundColor(isSelected ? .white : .secondary)
                }
                .shadow(color: isSelected ? theme.primaryColor.opacity(0.3) : .clear, radius: 8, y: 4)

                Text(title)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(isSelected ? theme.primaryColor : .secondary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.medium)
                    .fill(isSelected ? theme.primaryColor.opacity(0.08) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.medium)
                    .stroke(isSelected ? theme.primaryColor.opacity(0.2) : Color.clear, lineWidth: 1)
            )
        }
        .buttonStyle(ScaleButtonStyle())
    }
}

// MARK: - Info Row

private struct InfoRow: View {
    let title: String
    let value: String

    var body: some View {
        HStack {
            Text(title)
                .font(.subheadline)
                .foregroundColor(.secondary)

            Spacer()

            Text(value)
                .font(.subheadline)
                .fontWeight(.medium)
        }
    }
}

// MARK: - Scale Button Style

private struct ScaleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(ThemeManager.AnimationSettings.quickSpring, value: configuration.isPressed)
    }
}

// MARK: - Animated Settings Background

private struct AnimatedSettingsBackground: View {
    @ObservedObject private var theme = ThemeManager.shared
    @Environment(\.colorScheme) var colorScheme
    @State private var animate = false

    var body: some View {
        ZStack {
            // Base background - warmer for light mode
            if colorScheme == .light {
                Color(red: 0.98, green: 0.97, blue: 0.96)
                    .ignoresSafeArea()
            } else {
                Color(.systemBackground)
                    .ignoresSafeArea()
            }

            GeometryReader { geo in
                ZStack {
                    // Top gradient orb - softer for light mode
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [
                                    colorScheme == .light
                                        ? Color(red: 1.0, green: 0.9, blue: 0.85).opacity(0.5)
                                        : theme.primaryColor.opacity(0.12),
                                    .clear
                                ],
                                center: .center,
                                startRadius: 0,
                                endRadius: 180
                            )
                        )
                        .frame(width: 360, height: 360)
                        .offset(x: -100, y: animate ? -80 : -120)
                        .blur(radius: colorScheme == .light ? 70 : 50)

                    // Bottom gradient orb
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [
                                    colorScheme == .light
                                        ? theme.primaryColor.opacity(0.08)
                                        : theme.secondaryColor.opacity(0.1),
                                    .clear
                                ],
                                center: .center,
                                startRadius: 0,
                                endRadius: 150
                            )
                        )
                        .frame(width: 300, height: 300)
                        .offset(x: 140, y: geo.size.height - (animate ? 180 : 220))
                        .blur(radius: colorScheme == .light ? 60 : 40)

                    // Extra light mode orb for warmth
                    if colorScheme == .light {
                        Circle()
                            .fill(
                                RadialGradient(
                                    colors: [Color(red: 0.95, green: 0.9, blue: 1.0).opacity(0.4), .clear],
                                    center: .center,
                                    startRadius: 0,
                                    endRadius: 120
                                )
                            )
                            .frame(width: 280, height: 280)
                            .offset(x: 80, y: animate ? 150 : 200)
                            .blur(radius: 50)
                    }
                }
            }
            .ignoresSafeArea()
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 4).repeatForever(autoreverses: true)) {
                animate = true
            }
        }
    }
}

// MARK: - Reset Onboarding Button

private struct ResetOnboardingButton: View {
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = true
    @Environment(\.dismiss) private var dismiss
    @ObservedObject private var theme = ThemeManager.shared

    @State private var showingConfirmation = false

    var body: some View {
        Button(action: {
            showingConfirmation = true
        }) {
            HStack {
                Image(systemName: "arrow.counterclockwise.circle.fill")
                    .font(.system(size: 18))
                    .foregroundStyle(theme.primaryGradient)

                Text("View Onboarding Again")
                    .font(.subheadline)
                    .foregroundColor(.primary)

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.secondary)
            }
        }
        .confirmationDialog(
            "View Onboarding",
            isPresented: $showingConfirmation,
            titleVisibility: .visible
        ) {
            Button("Show Onboarding") {
                let feedback = UIImpactFeedbackGenerator(style: .medium)
                feedback.impactOccurred()
                dismiss()
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                    hasCompletedOnboarding = false
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will show the welcome screens again.")
        }
    }
}

// MARK: - Previews

#Preview("Settings View") {
    SettingsView()
}

#Preview("Theme Color Card") {
    HStack(spacing: 14) {
        ThemeColorCard(accentTheme: .purple, isSelected: true, index: 0, isVisible: true) {}
        ThemeColorCard(accentTheme: .blue, isSelected: false, index: 1, isVisible: true) {}
        ThemeColorCard(accentTheme: .teal, isSelected: false, index: 2, isVisible: true) {}
    }
    .padding()
}

#Preview("Appearance Mode") {
    HStack(spacing: 12) {
        AppearanceModeButton(mode: nil, title: "System", icon: "iphone", isSelected: true) {}
        AppearanceModeButton(mode: .light, title: "Light", icon: "sun.max.fill", isSelected: false) {}
        AppearanceModeButton(mode: .dark, title: "Dark", icon: "moon.fill", isSelected: false) {}
    }
    .padding()
}
