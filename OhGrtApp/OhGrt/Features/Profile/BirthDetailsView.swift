import SwiftUI
import Combine

/// View for managing user birth details for astrology features
struct BirthDetailsView: View {
    @StateObject private var viewModel = BirthDetailsViewModel()
    @ObservedObject private var theme = ThemeManager.shared
    @Environment(\.dismiss) private var dismiss

    // Animation states
    @State private var headerAppeared = false
    @State private var formAppeared = false
    @State private var zodiacGridAppeared = false
    @State private var rotationAngle: Double = 0

    var body: some View {
        NavigationStack {
            ZStack {
                // Animated background
                AnimatedAstrologyBackground()

                ScrollView {
                    VStack(spacing: 24) {
                        // Animated header
                        headerSection

                        // Birth details form
                        formSection

                        // Zodiac sign selection
                        zodiacSection

                        // Saved data preview
                        if viewModel.hasSavedDetails {
                            savedProfileSection
                        }

                        // Action buttons
                        actionButtons

                        Spacer(minLength: 40)
                    }
                    .padding()
                }
            }
            .navigationTitle("Birth Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundColor(theme.primaryColor)
                }
            }
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage)
            }
            .task {
                await viewModel.loadBirthDetails()
            }
            .onAppear {
                startAnimations()
            }
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        VStack(spacing: 16) {
            ZStack {
                // Outer rotating ring
                Circle()
                    .stroke(
                        AngularGradient(
                            colors: [.purple, .indigo, .blue, .purple],
                            center: .center,
                            startAngle: .degrees(rotationAngle),
                            endAngle: .degrees(rotationAngle + 360)
                        ),
                        lineWidth: 3
                    )
                    .frame(width: 95, height: 95)

                // Glow effect
                Circle()
                    .fill(
                        RadialGradient(
                            colors: [.purple.opacity(0.3), .clear],
                            center: .center,
                            startRadius: 20,
                            endRadius: 60
                        )
                    )
                    .frame(width: 120, height: 120)

                // Main circle
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.purple, .indigo],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 80, height: 80)
                    .shadow(color: .purple.opacity(0.4), radius: 15, y: 5)

                Image(systemName: "sparkles")
                    .font(.system(size: 36, weight: .medium))
                    .foregroundColor(.white)
                    .symbolEffect(.pulse, options: .repeating)
            }

            Text("Astrology Profile")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundStyle(
                    LinearGradient(
                        colors: [.primary, .primary.opacity(0.8)],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )

            Text("Enter your birth details for personalized\nhoroscopes and predictions")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            // Feature pills
            HStack(spacing: 10) {
                ThemedPillBadge(text: "Kundli", icon: "star.circle.fill", color: .purple)
                ThemedPillBadge(text: "Predictions", icon: "sparkles", color: .indigo)
                ThemedPillBadge(text: "Matching", icon: "heart.fill", color: .pink)
            }
        }
        .padding(.vertical, 16)
        .scaleEffect(headerAppeared ? 1.0 : 0.8)
        .opacity(headerAppeared ? 1.0 : 0)
    }

    // MARK: - Form Section

    private var formSection: some View {
        VStack(spacing: 16) {
            // Personal Information
            ThemedFormCard(title: "Personal Information", icon: "person.fill", color: .blue) {
                ThemedTextField(
                    placeholder: "Full Name",
                    text: $viewModel.fullName,
                    icon: "person.fill"
                )
            }

            // Birth Details
            ThemedFormCard(title: "Birth Details", icon: "calendar", color: .purple) {
                VStack(spacing: 16) {
                    DatePicker(
                        "Birth Date",
                        selection: $viewModel.birthDate,
                        displayedComponents: .date
                    )
                    .tint(theme.primaryColor)

                    Divider()

                    Toggle(isOn: $viewModel.includeBirthTime) {
                        HStack {
                            Image(systemName: "clock.fill")
                                .foregroundColor(.orange)
                            Text("Include Birth Time")
                        }
                    }
                    .tint(theme.primaryColor)

                    if viewModel.includeBirthTime {
                        DatePicker(
                            "Birth Time",
                            selection: $viewModel.birthTime,
                            displayedComponents: .hourAndMinute
                        )
                        .tint(theme.primaryColor)
                        .transition(.opacity.combined(with: .move(edge: .top)))
                    }

                    Divider()

                    ThemedTextField(
                        placeholder: "Birth Place (City)",
                        text: $viewModel.birthPlace,
                        icon: "mappin.circle.fill"
                    )
                }
            }
        }
        .offset(y: formAppeared ? 0 : 30)
        .opacity(formAppeared ? 1.0 : 0)
        .animation(.spring(response: 0.5, dampingFraction: 0.7), value: viewModel.includeBirthTime)
    }

    // MARK: - Zodiac Section

    private var zodiacSection: some View {
        ThemedFormCard(title: "Zodiac Sign", icon: "sparkles", color: .indigo) {
            VStack(spacing: 16) {
                // Zodiac grid
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 12), count: 4), spacing: 12) {
                    ForEach(Array(ZodiacSign.allCases.enumerated()), id: \.element) { index, sign in
                        ZodiacSignButton(
                            sign: sign,
                            isSelected: viewModel.selectedZodiacSign == sign.rawValue,
                            index: index,
                            isVisible: zodiacGridAppeared
                        ) {
                            withAnimation(ThemeManager.AnimationSettings.quickSpring) {
                                viewModel.selectedZodiacSign = sign.rawValue
                            }
                        }
                    }
                }

                if !viewModel.calculatedZodiacSign.isEmpty {
                    HStack {
                        Image(systemName: "wand.and.stars")
                            .foregroundColor(.purple)
                        Text("Detected:")
                            .foregroundColor(.secondary)
                        Text(viewModel.calculatedZodiacSign)
                            .fontWeight(.semibold)
                            .foregroundStyle(
                                LinearGradient(
                                    colors: [.purple, .indigo],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                        Spacer()
                    }
                    .font(.subheadline)
                    .padding(.top, 8)
                }
            }
        }
    }

    // MARK: - Saved Profile Section

    private var savedProfileSection: some View {
        ThemedFormCard(title: "Saved Profile", icon: "checkmark.seal.fill", color: .green) {
            VStack(spacing: 12) {
                if let zodiac = viewModel.savedZodiacSign {
                    SavedDetailRow(icon: "sparkles", label: "Sun Sign", value: zodiac, color: .purple)
                }
                if let moon = viewModel.savedMoonSign {
                    SavedDetailRow(icon: "moon.fill", label: "Moon Sign", value: moon, color: .indigo)
                }
                if let nakshatra = viewModel.savedNakshatra {
                    SavedDetailRow(icon: "star.fill", label: "Nakshatra", value: nakshatra, color: .orange)
                }
            }
        }
        .transition(.opacity.combined(with: .move(edge: .bottom)))
    }

    // MARK: - Action Buttons

    private var actionButtons: some View {
        VStack(spacing: 12) {
            // Save button
            Button {
                let feedback = UIImpactFeedbackGenerator(style: .medium)
                feedback.impactOccurred()
                Task {
                    await viewModel.saveBirthDetails()
                    if viewModel.saveSuccess {
                        dismiss()
                    }
                }
            } label: {
                HStack(spacing: 10) {
                    if viewModel.isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        Image(systemName: "checkmark.circle.fill")
                        Text("Save Birth Details")
                    }
                }
                .font(.headline)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .frame(height: 54)
                .background(
                    LinearGradient(
                        colors: [.purple, .indigo],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .cornerRadius(ThemeManager.CornerRadius.large)
                .shadow(color: .purple.opacity(0.4), radius: 12, y: 6)
            }
            .disabled(viewModel.isLoading)

            // Delete button
            if viewModel.hasSavedDetails {
                Button(role: .destructive) {
                    Task {
                        await viewModel.deleteBirthDetails()
                    }
                } label: {
                    HStack {
                        Image(systemName: "trash.fill")
                        Text("Delete Birth Details")
                    }
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.red)
                    .frame(maxWidth: .infinity)
                    .frame(height: 44)
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(ThemeManager.CornerRadius.medium)
                }
                .disabled(viewModel.isLoading)
            }
        }
        .padding(.top, 8)
    }

    // MARK: - Animations

    private func startAnimations() {
        withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(0.1)) {
            headerAppeared = true
        }

        withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(0.3)) {
            formAppeared = true
        }

        withAnimation(.easeOut(duration: 0.5).delay(0.5)) {
            zodiacGridAppeared = true
        }

        // Continuous rotation
        withAnimation(.linear(duration: 15).repeatForever(autoreverses: false)) {
            rotationAngle = 360
        }
    }
}

// MARK: - Themed Form Card

struct ThemedFormCard<Content: View>: View {
    let title: String
    let icon: String
    let color: Color
    @ViewBuilder let content: Content

    @State private var appeared = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(
                            LinearGradient(
                                colors: [color.opacity(0.2), color.opacity(0.1)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 32, height: 32)

                    Image(systemName: icon)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [color, color.opacity(0.7)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }

                Text(title)
                    .font(.headline)
                    .fontWeight(.semibold)
            }

            content
        }
        .padding(ThemeManager.Spacing.md)
        .background(Color(.secondarySystemBackground))
        .cornerRadius(ThemeManager.CornerRadius.large)
        .shadow(color: .black.opacity(0.05), radius: 8, y: 4)
    }
}

// MARK: - Themed Text Field

struct ThemedTextField: View {
    let placeholder: String
    @Binding var text: String
    let icon: String

    @ObservedObject private var theme = ThemeManager.shared
    @FocusState private var isFocused: Bool

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(isFocused ? theme.primaryColor : .secondary)
                .frame(width: 24)

            TextField(placeholder, text: $text)
                .focused($isFocused)
        }
        .padding()
        .background(Color(.tertiarySystemBackground))
        .cornerRadius(ThemeManager.CornerRadius.medium)
        .overlay(
            RoundedRectangle(cornerRadius: ThemeManager.CornerRadius.medium)
                .stroke(isFocused ? theme.primaryColor.opacity(0.5) : Color.clear, lineWidth: 1.5)
        )
        .animation(.easeInOut(duration: 0.2), value: isFocused)
    }
}

// MARK: - Zodiac Sign Button

struct ZodiacSignButton: View {
    let sign: ZodiacSign
    let isSelected: Bool
    let index: Int
    let isVisible: Bool
    let action: () -> Void

    @State private var appeared = false

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Text(sign.symbol)
                    .font(.system(size: 28))

                Text(sign.rawValue)
                    .font(.caption2)
                    .fontWeight(.medium)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 70)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ?
                        LinearGradient(
                            colors: [.purple.opacity(0.2), .indigo.opacity(0.15)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ) :
                        LinearGradient(
                            colors: [Color(.tertiarySystemBackground), Color(.tertiarySystemBackground)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(
                        isSelected ?
                            LinearGradient(colors: [.purple, .indigo], startPoint: .topLeading, endPoint: .bottomTrailing) :
                            LinearGradient(colors: [Color.clear], startPoint: .topLeading, endPoint: .bottomTrailing),
                        lineWidth: 2
                    )
            )
            .scaleEffect(isSelected ? 1.05 : 1.0)
            .shadow(color: isSelected ? .purple.opacity(0.2) : .clear, radius: 8, y: 4)
        }
        .buttonStyle(.plain)
        .scaleEffect(appeared ? 1.0 : 0.5)
        .opacity(appeared ? 1.0 : 0)
        .onAppear {
            if isVisible {
                let delay = Double(index) * 0.03
                withAnimation(.spring(response: 0.4, dampingFraction: 0.6).delay(delay)) {
                    appeared = true
                }
            }
        }
        .onChange(of: isVisible) { _, newValue in
            if newValue && !appeared {
                let delay = Double(index) * 0.03
                withAnimation(.spring(response: 0.4, dampingFraction: 0.6).delay(delay)) {
                    appeared = true
                }
            }
        }
    }
}

// MARK: - Saved Detail Row

struct SavedDetailRow: View {
    let icon: String
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(color)
                .frame(width: 24)

            Text(label)
                .font(.subheadline)
                .foregroundColor(.secondary)

            Spacer()

            Text(value)
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundStyle(
                    LinearGradient(
                        colors: [color, color.opacity(0.7)],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
        }
    }
}

// MARK: - Animated Astrology Background

private struct AnimatedAstrologyBackground: View {
    @State private var starOpacity: [Double] = Array(repeating: 0.3, count: 20)
    @State private var gradientOffset: CGFloat = 0

    var body: some View {
        ZStack {
            Color(.systemBackground)
                .ignoresSafeArea()

            // Gradient overlay
            LinearGradient(
                colors: [
                    .purple.opacity(0.05),
                    .clear,
                    .indigo.opacity(0.03)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            // Twinkling stars
            GeometryReader { geo in
                ForEach(0..<20, id: \.self) { i in
                    Circle()
                        .fill(Color.white)
                        .frame(width: CGFloat.random(in: 2...4))
                        .position(
                            x: CGFloat.random(in: 0...geo.size.width),
                            y: CGFloat.random(in: 0...geo.size.height)
                        )
                        .opacity(starOpacity[i])
                }
            }
            .ignoresSafeArea()
        }
        .onAppear {
            // Animate each star with random timing
            for i in 0..<20 {
                withAnimation(
                    .easeInOut(duration: Double.random(in: 1...2))
                    .repeatForever(autoreverses: true)
                    .delay(Double.random(in: 0...2))
                ) {
                    starOpacity[i] = Double.random(in: 0.5...1.0)
                }
            }
        }
    }
}

// MARK: - View Model

@MainActor
class BirthDetailsViewModel: ObservableObject {
    @Published var fullName = ""
    @Published var birthDate = Date()
    @Published var birthTime = Date()
    @Published var includeBirthTime = false
    @Published var birthPlace = ""
    @Published var selectedZodiacSign = ""

    @Published var isLoading = false
    @Published var showError = false
    @Published var errorMessage = ""
    @Published var saveSuccess = false
    @Published var hasSavedDetails = false

    @Published var savedZodiacSign: String?
    @Published var savedMoonSign: String?
    @Published var savedNakshatra: String?

    private let maxNameLength = 100
    private let maxPlaceLength = 200

    var calculatedZodiacSign: String {
        let calendar = Calendar.current
        let month = calendar.component(.month, from: birthDate)
        let day = calendar.component(.day, from: birthDate)
        return ZodiacSign.fromDate(month: month, day: day)?.rawValue ?? ""
    }

    func validateInputs() -> String? {
        if birthDate > Date() {
            return "Birth date cannot be in the future"
        }

        let calendar = Calendar.current
        if let minDate = calendar.date(byAdding: .year, value: -150, to: Date()),
           birthDate < minDate {
            return "Please enter a valid birth date"
        }

        let trimmedName = fullName.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedName.count > maxNameLength {
            return "Name must be less than \(maxNameLength) characters"
        }

        let trimmedPlace = birthPlace.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmedPlace.count > maxPlaceLength {
            return "Birth place must be less than \(maxPlaceLength) characters"
        }

        return nil
    }

    func loadBirthDetails() async {
        isLoading = true
        defer { isLoading = false }

        do {
            if let details = try await APIClient.shared.getBirthDetails() {
                hasSavedDetails = true
                fullName = details.fullName ?? ""
                birthPlace = details.birthPlace ?? ""
                selectedZodiacSign = details.zodiacSign ?? ""
                savedZodiacSign = details.zodiacSign
                savedMoonSign = details.moonSign
                savedNakshatra = details.nakshatra

                if let dateStr = details.birthDate {
                    let formatter = DateFormatter()
                    formatter.dateFormat = "dd-MM-yyyy"
                    if let date = formatter.date(from: dateStr) {
                        birthDate = date
                    }
                }

                if let timeStr = details.birthTime {
                    includeBirthTime = true
                    let formatter = DateFormatter()
                    formatter.dateFormat = "HH:mm"
                    if let time = formatter.date(from: timeStr) {
                        birthTime = time
                    }
                }
            }
        } catch {
            // No saved details
        }
    }

    func saveBirthDetails() async {
        if let validationError = validateInputs() {
            errorMessage = validationError
            showError = true
            return
        }

        isLoading = true
        saveSuccess = false
        defer { isLoading = false }

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "dd-MM-yyyy"
        let birthDateStr = dateFormatter.string(from: birthDate)

        var birthTimeStr: String? = nil
        if includeBirthTime {
            let timeFormatter = DateFormatter()
            timeFormatter.dateFormat = "HH:mm"
            birthTimeStr = timeFormatter.string(from: birthTime)
        }

        let request = BirthDetailsRequest(
            fullName: fullName.isEmpty ? nil : fullName,
            birthDate: birthDateStr,
            birthTime: birthTimeStr,
            birthPlace: birthPlace.isEmpty ? nil : birthPlace,
            zodiacSign: selectedZodiacSign.isEmpty ? nil : selectedZodiacSign
        )

        do {
            let response = try await APIClient.shared.saveBirthDetails(request)
            hasSavedDetails = true
            savedZodiacSign = response.zodiacSign
            savedMoonSign = response.moonSign
            savedNakshatra = response.nakshatra
            saveSuccess = true
        } catch {
            errorMessage = "Failed to save birth details: \(error.localizedDescription)"
            showError = true
        }
    }

    func deleteBirthDetails() async {
        isLoading = true
        defer { isLoading = false }

        do {
            try await APIClient.shared.deleteBirthDetails()
            hasSavedDetails = false
            savedZodiacSign = nil
            savedMoonSign = nil
            savedNakshatra = nil
            fullName = ""
            birthPlace = ""
            selectedZodiacSign = ""
            includeBirthTime = false
        } catch {
            errorMessage = "Failed to delete birth details: \(error.localizedDescription)"
            showError = true
        }
    }
}

// MARK: - Zodiac Sign Enum

enum ZodiacSign: String, CaseIterable {
    case aries = "Aries"
    case taurus = "Taurus"
    case gemini = "Gemini"
    case cancer = "Cancer"
    case leo = "Leo"
    case virgo = "Virgo"
    case libra = "Libra"
    case scorpio = "Scorpio"
    case sagittarius = "Sagittarius"
    case capricorn = "Capricorn"
    case aquarius = "Aquarius"
    case pisces = "Pisces"

    var symbol: String {
        switch self {
        case .aries: return "\u{2648}"
        case .taurus: return "\u{2649}"
        case .gemini: return "\u{264A}"
        case .cancer: return "\u{264B}"
        case .leo: return "\u{264C}"
        case .virgo: return "\u{264D}"
        case .libra: return "\u{264E}"
        case .scorpio: return "\u{264F}"
        case .sagittarius: return "\u{2650}"
        case .capricorn: return "\u{2651}"
        case .aquarius: return "\u{2652}"
        case .pisces: return "\u{2653}"
        }
    }

    static func fromDate(month: Int, day: Int) -> ZodiacSign? {
        switch (month, day) {
        case (3, 21...31), (4, 1...19): return .aries
        case (4, 20...30), (5, 1...20): return .taurus
        case (5, 21...31), (6, 1...20): return .gemini
        case (6, 21...30), (7, 1...22): return .cancer
        case (7, 23...31), (8, 1...22): return .leo
        case (8, 23...31), (9, 1...22): return .virgo
        case (9, 23...30), (10, 1...22): return .libra
        case (10, 23...31), (11, 1...21): return .scorpio
        case (11, 22...30), (12, 1...21): return .sagittarius
        case (12, 22...31), (1, 1...19): return .capricorn
        case (1, 20...31), (2, 1...18): return .aquarius
        case (2, 19...29), (3, 1...20): return .pisces
        default: return nil
        }
    }
}

// MARK: - Previews

#Preview("Birth Details Form") {
    BirthDetailsView()
}

#Preview("Themed Form Card") {
    VStack(spacing: 16) {
        ThemedFormCard(title: "Personal Info", icon: "person.fill", color: .blue) {
            Text("Card content here")
        }
        ThemedFormCard(title: "Birth Details", icon: "calendar", color: .purple) {
            VStack {
                Text("Date picker")
                Text("Time picker")
            }
        }
    }
    .padding()
}

#Preview("Zodiac Signs Grid") {
    LazyVGrid(columns: [GridItem(.adaptive(minimum: 80))], spacing: 12) {
        ForEach(Array(ZodiacSign.allCases.enumerated()), id: \.element) { index, sign in
            ZodiacSignButton(
                sign: sign,
                isSelected: sign == .leo,
                index: index,
                isVisible: true
            ) {}
        }
    }
    .padding()
}
