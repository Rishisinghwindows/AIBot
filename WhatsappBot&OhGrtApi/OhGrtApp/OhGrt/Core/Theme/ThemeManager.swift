import SwiftUI
import Combine

// MARK: - Theme Manager

/// Centralized theme manager for consistent styling across the app
@MainActor
final class ThemeManager: ObservableObject {
    static let shared = ThemeManager()

    @Published var colorScheme: ColorScheme? = .dark
    @Published var accentTheme: AccentTheme = .purple

    private init() {}

    // MARK: - Environment-Aware Colors

    /// Check if we're in light mode (for adaptive styling)
    var isLightMode: Bool {
        colorScheme == .light
    }

    // MARK: - Theme Colors

    var primaryGradient: LinearGradient {
        LinearGradient(
            colors: accentTheme.primaryColors,
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    var secondaryGradient: LinearGradient {
        LinearGradient(
            colors: accentTheme.secondaryColors,
            startPoint: .leading,
            endPoint: .trailing
        )
    }

    var backgroundGradient: LinearGradient {
        LinearGradient(
            colors: isLightMode
                ? [Color(.systemBackground), Color(.systemBackground).opacity(0.95)]
                : [
                    Color(red: 0.05, green: 0.03, blue: 0.08),
                    Color(red: 0.03, green: 0.02, blue: 0.06),
                    Color.black
                ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    /// App-wide background view for the active theme
    @ViewBuilder
    var appBackground: some View {
        if isLightMode {
            lightModeBackground
        } else {
            ZStack {
                backgroundGradient
                RadialGradient(
                    colors: [
                        accentTheme.primary.opacity(0.15),
                        Color.clear
                    ],
                    center: .topLeading,
                    startRadius: 10,
                    endRadius: 520
                )
            }
        }
    }

    /// Enhanced background for light mode with subtle warmth
    var lightModeBackground: some View {
        ZStack {
            // Base warm white
            Color(red: 0.99, green: 0.98, blue: 0.97)

            // Subtle gradient overlay
            LinearGradient(
                colors: [
                    accentTheme.primary.opacity(0.03),
                    accentTheme.secondary.opacity(0.02),
                    Color.clear
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        }
    }

    /// Light mode card background with subtle tint
    var lightCardBackground: Color {
        Color(red: 1.0, green: 0.995, blue: 0.99)
    }

    /// Light mode elevated surface
    var lightElevatedSurface: Color {
        Color.white
    }

    // MARK: - Semantic Colors

    var primaryColor: Color { accentTheme.primary }
    var secondaryColor: Color { accentTheme.secondary }

    // Card colors - adaptive for light/dark mode
    var cardBackground: Color {
        isLightMode ? lightCardBackground : Color(red: 0.12, green: 0.1, blue: 0.16)
    }
    var cardBorder: Color { accentTheme.primary.opacity(0.2) }

    // Text colors
    var primaryText: Color { isLightMode ? .black : Color(red: 0.93, green: 0.9, blue: 0.96) }
    var secondaryText: Color { isLightMode ? .secondary : Color(red: 0.7, green: 0.66, blue: 0.78) }
    var accentText: Color { accentTheme.primary }

    // Status colors
    var successColor: Color { .green }
    var warningColor: Color { .orange }
    var errorColor: Color { .red }
    var infoColor: Color { .blue }

    // MARK: - Light Mode Enhanced Colors

    /// Soft shadow color for light mode cards
    var lightShadowColor: Color {
        Color.black.opacity(0.08)
    }

    /// Subtle border for light mode elements
    var lightBorderColor: Color {
        Color.gray.opacity(0.12)
    }

    /// Light mode input field background
    var lightInputBackground: Color {
        Color(red: 0.97, green: 0.97, blue: 0.98)
    }

    /// Light mode message bubble (AI response)
    var lightAIBubbleBackground: Color {
        Color(red: 0.96, green: 0.96, blue: 0.98)
    }

    /// Light mode divider color
    var lightDividerColor: Color {
        Color.gray.opacity(0.15)
    }

    /// Light mode hover/pressed state
    var lightPressedColor: Color {
        Color.gray.opacity(0.08)
    }

    // MARK: - Category Colors

    func categoryColor(for category: String) -> Color {
        switch category.lowercased() {
        case "horoscope", "astrology", "kundli", "zodiac", "life_prediction", "ask_astrologer":
            return .purple
        case "weather":
            return .cyan
        case "news":
            return .red
        case "pnr", "train", "travel", "pnr_status", "train_status", "metro_info":
            return .blue
        case "tarot":
            return .indigo
        case "numerology":
            return .orange
        case "panchang":
            return .teal
        case "dosha_check":
            return .red
        case "kundli_matching":
            return .pink
        default:
            return accentTheme.primary
        }
    }

    func categoryIcon(for category: String) -> String {
        switch category.lowercased() {
        case "horoscope", "astrology", "zodiac":
            return "sparkles"
        case "kundli":
            return "star.circle.fill"
        case "kundli_matching":
            return "heart.circle.fill"
        case "dosha_check":
            return "exclamationmark.triangle.fill"
        case "life_prediction":
            return "crystal.ball.fill"
        case "ask_astrologer":
            return "person.wave.2.fill"
        case "weather":
            return "cloud.sun.fill"
        case "news":
            return "newspaper.fill"
        case "pnr", "pnr_status":
            return "ticket.fill"
        case "train", "train_status":
            return "train.side.front.car"
        case "metro_info":
            return "tram.fill"
        case "tarot":
            return "suit.diamond.fill"
        case "numerology":
            return "number.circle.fill"
        case "panchang":
            return "calendar.badge.clock"
        default:
            return "bubble.left.fill"
        }
    }

    // MARK: - Animation Settings

    struct AnimationSettings {
        static let springResponse: Double = 0.5
        static let springDamping: Double = 0.7
        static let quickSpringResponse: Double = 0.3
        static let quickSpringDamping: Double = 0.6

        static var spring: Animation {
            .spring(response: springResponse, dampingFraction: springDamping)
        }

        static var quickSpring: Animation {
            .spring(response: quickSpringResponse, dampingFraction: quickSpringDamping)
        }

        static var bouncy: Animation {
            .spring(response: 0.4, dampingFraction: 0.6)
        }

        static var smooth: Animation {
            .easeInOut(duration: 0.3)
        }

        static var slow: Animation {
            .easeInOut(duration: 0.6)
        }

        static func staggered(index: Int, baseDelay: Double = 0.05) -> Animation {
            .spring(response: springResponse, dampingFraction: springDamping)
            .delay(Double(index) * baseDelay)
        }

        static var continuousPulse: Animation {
            .easeInOut(duration: 1.5).repeatForever(autoreverses: true)
        }

        static var continuousRotation: Animation {
            .linear(duration: 10).repeatForever(autoreverses: false)
        }

        static var shimmer: Animation {
            .linear(duration: 2).repeatForever(autoreverses: false)
        }

        static var float: Animation {
            .easeInOut(duration: 3).repeatForever(autoreverses: true)
        }
    }

    // MARK: - Shadow Settings

    struct ShadowSettings {
        static let cardShadow = Shadow(color: .black.opacity(0.1), radius: 8, y: 4)
        static let buttonShadow = Shadow(color: .blue.opacity(0.3), radius: 12, y: 6)
        static let floatingShadow = Shadow(color: .black.opacity(0.15), radius: 16, y: 8)

        // Enhanced light mode shadows - more visible and refined
        static let lightCardShadow = Shadow(color: .black.opacity(0.06), radius: 12, y: 4)
        static let lightElevatedShadow = Shadow(color: .black.opacity(0.1), radius: 20, y: 8)
        static let lightSubtleShadow = Shadow(color: .black.opacity(0.04), radius: 6, y: 2)

        struct Shadow {
            let color: Color
            let radius: CGFloat
            let y: CGFloat
        }
    }

    // MARK: - Corner Radius

    struct CornerRadius {
        static let small: CGFloat = 8
        static let medium: CGFloat = 12
        static let large: CGFloat = 16
        static let extraLarge: CGFloat = 20
        static let card: CGFloat = 16
        static let button: CGFloat = 14
        static let bubble: CGFloat = 18
        static let pill: CGFloat = 50
    }

    // MARK: - Spacing

    struct Spacing {
        static let xxs: CGFloat = 4
        static let xs: CGFloat = 8
        static let sm: CGFloat = 12
        static let md: CGFloat = 16
        static let lg: CGFloat = 24
        static let xl: CGFloat = 32
        static let xxl: CGFloat = 48
    }
}

// MARK: - Accent Theme

enum AccentTheme: String, CaseIterable, Identifiable {
    case purple
    case blue
    case teal
    case orange
    case pink

    var id: String { rawValue }

    var primary: Color {
        switch self {
        case .purple: return Color(red: 0.5, green: 0.2, blue: 0.9)
        case .blue: return Color(red: 0.2, green: 0.5, blue: 1.0)
        case .teal: return Color(red: 0.2, green: 0.7, blue: 0.7)
        case .orange: return Color(red: 1.0, green: 0.5, blue: 0.2)
        case .pink: return Color(red: 0.95, green: 0.3, blue: 0.5)
        }
    }

    var secondary: Color {
        switch self {
        case .purple: return Color(red: 0.3, green: 0.4, blue: 0.95)
        case .blue: return Color(red: 0.4, green: 0.3, blue: 0.9)
        case .teal: return Color(red: 0.3, green: 0.5, blue: 0.8)
        case .orange: return Color(red: 0.9, green: 0.3, blue: 0.3)
        case .pink: return Color(red: 0.7, green: 0.3, blue: 0.9)
        }
    }

    var primaryColors: [Color] {
        [primary, secondary]
    }

    var secondaryColors: [Color] {
        [secondary, primary]
    }

    var displayName: String {
        rawValue.capitalized
    }

    var icon: String {
        switch self {
        case .purple: return "sparkles"
        case .blue: return "drop.fill"
        case .teal: return "leaf.fill"
        case .orange: return "flame.fill"
        case .pink: return "heart.fill"
        }
    }
}

// MARK: - Theme Environment Key

private struct ThemeManagerKey: EnvironmentKey {
    static let defaultValue = ThemeManager.shared
}

extension EnvironmentValues {
    var themeManager: ThemeManager {
        get { self[ThemeManagerKey.self] }
        set { self[ThemeManagerKey.self] = newValue }
    }
}

// MARK: - Themed View Modifiers

extension View {
    func themedCard() -> some View {
        self
            .padding(ThemeManager.Spacing.md)
            .background(ThemeManager.shared.cardBackground)
            .cornerRadius(ThemeManager.CornerRadius.card)
            .shadow(
                color: ThemeManager.ShadowSettings.cardShadow.color,
                radius: ThemeManager.ShadowSettings.cardShadow.radius,
                y: ThemeManager.ShadowSettings.cardShadow.y
            )
    }

    /// Enhanced card style optimized for light mode with better shadows and borders
    func lightModeCard() -> some View {
        self
            .padding(ThemeManager.Spacing.md)
            .background(Color.white)
            .cornerRadius(ThemeManager.CornerRadius.card)
            .overlay(
                RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.card)
                    .stroke(ThemeManager.shared.lightBorderColor, lineWidth: 1)
            )
            .shadow(
                color: ThemeManager.ShadowSettings.lightCardShadow.color,
                radius: ThemeManager.ShadowSettings.lightCardShadow.radius,
                y: ThemeManager.ShadowSettings.lightCardShadow.y
            )
    }

    /// Elevated card style for light mode with prominent shadow
    func lightModeElevatedCard() -> some View {
        self
            .padding(ThemeManager.Spacing.md)
            .background(Color.white)
            .cornerRadius(ThemeManager.CornerRadius.large)
            .shadow(
                color: ThemeManager.ShadowSettings.lightElevatedShadow.color,
                radius: ThemeManager.ShadowSettings.lightElevatedShadow.radius,
                y: ThemeManager.ShadowSettings.lightElevatedShadow.y
            )
    }

    func themedButton() -> some View {
        self
            .padding(.horizontal, ThemeManager.Spacing.lg)
            .padding(.vertical, ThemeManager.Spacing.sm)
            .background(ThemeManager.shared.primaryGradient)
            .foregroundColor(.white)
            .cornerRadius(ThemeManager.CornerRadius.button)
            .shadow(
                color: ThemeManager.ShadowSettings.buttonShadow.color,
                radius: ThemeManager.ShadowSettings.buttonShadow.radius,
                y: ThemeManager.ShadowSettings.buttonShadow.y
            )
    }

    func themedSecondaryButton() -> some View {
        self
            .padding(.horizontal, ThemeManager.Spacing.lg)
            .padding(.vertical, ThemeManager.Spacing.sm)
            .background(ThemeManager.shared.cardBackground)
            .foregroundColor(ThemeManager.shared.primaryColor)
            .cornerRadius(ThemeManager.CornerRadius.button)
            .overlay(
                RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.button)
                    .stroke(ThemeManager.shared.primaryColor.opacity(0.3), lineWidth: 1)
            )
    }

    /// Light mode button with subtle shadow and border
    func lightModeButton() -> some View {
        self
            .padding(.horizontal, ThemeManager.Spacing.lg)
            .padding(.vertical, ThemeManager.Spacing.sm)
            .background(Color.white)
            .foregroundColor(ThemeManager.shared.primaryColor)
            .cornerRadius(ThemeManager.CornerRadius.button)
            .overlay(
                RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.button)
                    .stroke(ThemeManager.shared.lightBorderColor, lineWidth: 1)
            )
            .shadow(
                color: ThemeManager.ShadowSettings.lightSubtleShadow.color,
                radius: ThemeManager.ShadowSettings.lightSubtleShadow.radius,
                y: ThemeManager.ShadowSettings.lightSubtleShadow.y
            )
    }

    func themedGradientBackground() -> some View {
        self.background(
            ThemeManager.shared.appBackground
        )
    }

    /// Enhanced light mode background with subtle warmth and accent tint
    func lightModeBackground() -> some View {
        self.background(
            ZStack {
                // Warm white base
                Color(red: 0.995, green: 0.99, blue: 0.985)
                    .ignoresSafeArea()

                // Very subtle accent gradient
                LinearGradient(
                    colors: [
                        ThemeManager.shared.primaryColor.opacity(0.02),
                        Color.clear,
                        ThemeManager.shared.secondaryColor.opacity(0.015)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
            }
        )
    }

    /// Light mode list/scroll background
    func lightModeListBackground() -> some View {
        self.background(
            Color(red: 0.96, green: 0.96, blue: 0.97)
                .ignoresSafeArea()
        )
    }

    func entranceAnimation(delay: Double = 0) -> some View {
        self.modifier(EntranceAnimationModifier(delay: delay))
    }

    func pulseAnimation() -> some View {
        self.modifier(PulseAnimationModifier())
    }

    func floatAnimation() -> some View {
        self.modifier(FloatAnimationModifier())
    }

    func shimmerEffect() -> some View {
        self.modifier(ShimmerModifier())
    }
}

// MARK: - Animation Modifiers

struct EntranceAnimationModifier: ViewModifier {
    let delay: Double

    @State private var appeared = false

    func body(content: Content) -> some View {
        content
            .opacity(appeared ? 1 : 0)
            .scaleEffect(appeared ? 1 : 0.8)
            .offset(y: appeared ? 0 : 20)
            .onAppear {
                withAnimation(ThemeManager.AnimationSettings.spring.delay(delay)) {
                    appeared = true
                }
            }
    }
}

struct PulseAnimationModifier: ViewModifier {
    @State private var isPulsing = false

    func body(content: Content) -> some View {
        content
            .scaleEffect(isPulsing ? 1.05 : 1.0)
            .onAppear {
                withAnimation(ThemeManager.AnimationSettings.continuousPulse) {
                    isPulsing = true
                }
            }
    }
}

struct FloatAnimationModifier: ViewModifier {
    @State private var offset: CGFloat = 0

    func body(content: Content) -> some View {
        content
            .offset(y: offset)
            .onAppear {
                withAnimation(ThemeManager.AnimationSettings.float) {
                    offset = -10
                }
            }
    }
}

struct ShimmerModifier: ViewModifier {
    @State private var shimmerOffset: CGFloat = -200

    func body(content: Content) -> some View {
        content
            .overlay(
                LinearGradient(
                    colors: [.clear, .white.opacity(0.4), .clear],
                    startPoint: .leading,
                    endPoint: .trailing
                )
                .offset(x: shimmerOffset)
                .mask(content)
            )
            .onAppear {
                withAnimation(ThemeManager.AnimationSettings.shimmer) {
                    shimmerOffset = 400
                }
            }
    }
}

// MARK: - Themed Components

struct ThemedGradientIcon: View {
    let systemName: String
    let size: CGFloat
    let colors: [Color]?

    @ObservedObject private var theme = ThemeManager.shared

    init(systemName: String, size: CGFloat = 24, colors: [Color]? = nil) {
        self.systemName = systemName
        self.size = size
        self.colors = colors
    }

    var body: some View {
        Image(systemName: systemName)
            .font(.system(size: size, weight: .medium))
            .foregroundStyle(
                LinearGradient(
                    colors: colors ?? theme.accentTheme.primaryColors,
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
    }
}

struct ThemedCircleIcon: View {
    let systemName: String
    let size: CGFloat
    let iconSize: CGFloat
    let colors: [Color]?

    @ObservedObject private var theme = ThemeManager.shared

    init(systemName: String, size: CGFloat = 50, iconSize: CGFloat = 24, colors: [Color]? = nil) {
        self.systemName = systemName
        self.size = size
        self.iconSize = iconSize
        self.colors = colors
    }

    var body: some View {
        ZStack {
            Circle()
                .fill(
                    LinearGradient(
                        colors: (colors ?? theme.accentTheme.primaryColors).map { $0.opacity(0.15) },
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: size, height: size)

            ThemedGradientIcon(systemName: systemName, size: iconSize, colors: colors)
        }
    }
}

struct ThemedPillBadge: View {
    let text: String
    let icon: String?
    let color: Color?

    @ObservedObject private var theme = ThemeManager.shared

    init(text: String, icon: String? = nil, color: Color? = nil) {
        self.text = text
        self.icon = icon
        self.color = color
    }

    var body: some View {
        HStack(spacing: 4) {
            if let icon = icon {
                Image(systemName: icon)
                    .font(.caption2)
            }
            Text(text)
                .font(.caption2)
                .fontWeight(.medium)
        }
        .foregroundColor(color ?? theme.primaryColor)
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(
            Capsule()
                .fill((color ?? theme.primaryColor).opacity(0.12))
        )
    }
}

struct ThemedDivider: View {
    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        Rectangle()
            .fill(theme.primaryGradient.opacity(0.3))
            .frame(height: 1)
    }
}

struct AnimatedGradientBackground: View {
    @State private var animateGradient = false
    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        LinearGradient(
            colors: [
                theme.primaryColor.opacity(0.1),
                theme.secondaryColor.opacity(0.05),
                Color.clear
            ],
            startPoint: animateGradient ? .topLeading : .bottomTrailing,
            endPoint: animateGradient ? .bottomTrailing : .topLeading
        )
        .ignoresSafeArea()
        .onAppear {
            withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true)) {
                animateGradient = true
            }
        }
    }
}

struct FloatingOrbs: View {
    @State private var offset1: CGFloat = 0
    @State private var offset2: CGFloat = 0
    @State private var offset3: CGFloat = 0

    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        GeometryReader { geo in
            ZStack {
                Circle()
                    .fill(
                        RadialGradient(
                            colors: [theme.primaryColor.opacity(0.3), .clear],
                            center: .center,
                            startRadius: 0,
                            endRadius: 150
                        )
                    )
                    .frame(width: 300, height: 300)
                    .offset(x: -100, y: offset1 - 100)
                    .blur(radius: 60)

                Circle()
                    .fill(
                        RadialGradient(
                            colors: [theme.secondaryColor.opacity(0.25), .clear],
                            center: .center,
                            startRadius: 0,
                            endRadius: 120
                        )
                    )
                    .frame(width: 250, height: 250)
                    .offset(x: 120, y: -offset2 + 200)
                    .blur(radius: 50)

                Circle()
                    .fill(
                        RadialGradient(
                            colors: [Color.pink.opacity(0.2), .clear],
                            center: .center,
                            startRadius: 0,
                            endRadius: 100
                        )
                    )
                    .frame(width: 200, height: 200)
                    .offset(x: 50, y: offset3 + 400)
                    .blur(radius: 40)
            }
            .frame(width: geo.size.width, height: geo.size.height)
        }
        .ignoresSafeArea()
        .onAppear {
            withAnimation(.easeInOut(duration: 4).repeatForever(autoreverses: true)) {
                offset1 = 30
            }
            withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true).delay(0.5)) {
                offset2 = 40
            }
            withAnimation(.easeInOut(duration: 3.5).repeatForever(autoreverses: true).delay(1)) {
                offset3 = 25
            }
        }
    }
}

/// Light mode optimized floating orbs with softer, warmer colors
struct LightModeFloatingOrbs: View {
    @State private var offset1: CGFloat = 0
    @State private var offset2: CGFloat = 0
    @State private var offset3: CGFloat = 0

    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        GeometryReader { geo in
            ZStack {
                // Warm peach orb
                Circle()
                    .fill(
                        RadialGradient(
                            colors: [Color(red: 1.0, green: 0.85, blue: 0.8).opacity(0.4), .clear],
                            center: .center,
                            startRadius: 0,
                            endRadius: 180
                        )
                    )
                    .frame(width: 350, height: 350)
                    .offset(x: -120, y: offset1 - 150)
                    .blur(radius: 80)

                // Light accent orb
                Circle()
                    .fill(
                        RadialGradient(
                            colors: [theme.primaryColor.opacity(0.15), .clear],
                            center: .center,
                            startRadius: 0,
                            endRadius: 140
                        )
                    )
                    .frame(width: 280, height: 280)
                    .offset(x: 140, y: -offset2 + 250)
                    .blur(radius: 60)

                // Soft lavender orb
                Circle()
                    .fill(
                        RadialGradient(
                            colors: [Color(red: 0.9, green: 0.88, blue: 1.0).opacity(0.35), .clear],
                            center: .center,
                            startRadius: 0,
                            endRadius: 120
                        )
                    )
                    .frame(width: 240, height: 240)
                    .offset(x: 60, y: offset3 + 450)
                    .blur(radius: 50)
            }
            .frame(width: geo.size.width, height: geo.size.height)
        }
        .ignoresSafeArea()
        .onAppear {
            withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true)) {
                offset1 = 25
            }
            withAnimation(.easeInOut(duration: 6).repeatForever(autoreverses: true).delay(0.5)) {
                offset2 = 35
            }
            withAnimation(.easeInOut(duration: 4).repeatForever(autoreverses: true).delay(1)) {
                offset3 = 20
            }
        }
    }
}

/// Adaptive background that switches between light and dark mode styles
struct AdaptiveBackground: View {
    @Environment(\.colorScheme) var colorScheme
    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        ZStack {
            if colorScheme == .light {
                // Light mode: warm white with subtle gradient
                Color(red: 0.995, green: 0.99, blue: 0.985)
                    .ignoresSafeArea()

                LightModeFloatingOrbs()
            } else {
                // Dark mode: standard dark background with orbs
                Color(.systemBackground)
                    .ignoresSafeArea()

                FloatingOrbs()
            }
        }
    }
}

// MARK: - Previews

#Preview("Theme Colors") {
    ScrollView {
        VStack(spacing: 20) {
            ForEach(AccentTheme.allCases) { theme in
                HStack {
                    Circle()
                        .fill(theme.primary)
                        .frame(width: 40, height: 40)
                    Circle()
                        .fill(theme.secondary)
                        .frame(width: 40, height: 40)
                    Text(theme.displayName)
                        .fontWeight(.medium)
                    Spacer()
                    Image(systemName: theme.icon)
                        .foregroundColor(theme.primary)
                }
                .padding()
                .background(Color(.secondarySystemBackground))
                .cornerRadius(12)
            }
        }
        .padding()
    }
}

#Preview("Themed Components") {
    VStack(spacing: 20) {
        ThemedCircleIcon(systemName: "sparkles", size: 80, iconSize: 36)

        ThemedPillBadge(text: "Premium", icon: "crown.fill")

        Text("Primary Button")
            .fontWeight(.semibold)
            .themedButton()

        Text("Secondary Button")
            .fontWeight(.medium)
            .themedSecondaryButton()

        VStack {
            Text("Card Content")
                .font(.headline)
            Text("This is a themed card with consistent styling")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .themedCard()
    }
    .padding()
}

#Preview("Floating Orbs") {
    ZStack {
        Color(.systemBackground)
        FloatingOrbs()
    }
}

#Preview("Light Mode Floating Orbs") {
    ZStack {
        Color(red: 0.995, green: 0.99, blue: 0.985)
        LightModeFloatingOrbs()
    }
    .preferredColorScheme(.light)
}

#Preview("Adaptive Background") {
    AdaptiveBackground()
}

#Preview("Light Mode Cards") {
    VStack(spacing: 20) {
        Text("Light Mode Card")
            .font(.headline)
            .frame(maxWidth: .infinity)
            .lightModeCard()

        Text("Elevated Card")
            .font(.headline)
            .frame(maxWidth: .infinity)
            .lightModeElevatedCard()

        Text("Light Mode Button")
            .fontWeight(.medium)
            .lightModeButton()
    }
    .padding()
    .lightModeBackground()
    .preferredColorScheme(.light)
}

#Preview("Light Mode Full Screen") {
    ZStack {
        AdaptiveBackground()

        VStack(spacing: 24) {
            // Header
            VStack(spacing: 8) {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [Color.purple.opacity(0.2), Color.blue.opacity(0.15)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 80, height: 80)

                    Image(systemName: "sparkles")
                        .font(.system(size: 36))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [.purple, .blue],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }

                Text("Light Mode Preview")
                    .font(.title2)
                    .fontWeight(.bold)

                Text("Enhanced styling for light theme")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            // Cards
            VStack(spacing: 12) {
                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 8) {
                        Image(systemName: "sun.max.fill")
                            .font(.title2)
                            .foregroundColor(.orange)
                        Text("Weather")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        Text("Sunny, 28°C")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .lightModeCard()

                    VStack(alignment: .leading, spacing: 8) {
                        Image(systemName: "train.side.front.car")
                            .font(.title2)
                            .foregroundColor(.blue)
                        Text("PNR Status")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        Text("Confirmed")
                            .font(.caption)
                            .foregroundColor(.green)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .lightModeCard()
                }
            }
            .padding(.horizontal)

            Spacer()
        }
        .padding(.top, 60)
    }
    .preferredColorScheme(.light)
}
