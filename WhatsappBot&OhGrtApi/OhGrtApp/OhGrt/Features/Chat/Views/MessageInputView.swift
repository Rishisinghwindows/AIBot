import SwiftUI
import UIKit

/// Input view for composing and sending messages
struct MessageInputView: View {
    @Binding var text: String
    let isLoading: Bool
    let onMic: () -> Void
    let onSend: () -> Void

    @FocusState private var isFocused: Bool
    @State private var sendButtonScale: CGFloat = 1.0
    @State private var micPulse: Bool = false
    @State private var showCharCount: Bool = false

    private let maxCharacters = 2000
    private let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
    private let selectionFeedback = UISelectionFeedbackGenerator()

    var body: some View {
        VStack(spacing: 0) {
            // Character count indicator (shows when near limit)
            if showCharCount && text.count > maxCharacters - 200 {
                characterCountBar
            }

            HStack(alignment: .bottom, spacing: 10) {
                // Mic Button with pulse animation
                micButton

                // Text Input Field
                textInputField

                // Send Button with gradient
                sendButton
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(inputBackground)
        }
        .onChange(of: text) { _, newValue in
            withAnimation(.easeInOut(duration: 0.2)) {
                showCharCount = newValue.count > maxCharacters - 200
            }
        }
    }

    // MARK: - Components

    private var micButton: some View {
        Button(action: {
            selectionFeedback.selectionChanged()
            onMic()
        }) {
            ZStack {
                Circle()
                    .fill(Color(.secondarySystemBackground))
                    .frame(width: 42, height: 42)

                Circle()
                    .stroke(Color.purple.opacity(0.3), lineWidth: 2)
                    .frame(width: 42, height: 42)
                    .scaleEffect(micPulse ? 1.3 : 1.0)
                    .opacity(micPulse ? 0 : 0.8)

                Image(systemName: "mic.fill")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.purple, .blue],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 1.5).repeatForever(autoreverses: false)) {
                micPulse = true
            }
        }
    }

    private var textInputField: some View {
        HStack(spacing: 8) {
            TextField("Ask anything...", text: $text, axis: .vertical)
                .textFieldStyle(.plain)
                .font(.body)
                .lineLimit(1...6)
                .focused($isFocused)
                .onSubmit {
                    if canSend {
                        triggerSend()
                    }
                }

            // Clear button when text is present
            if !text.isEmpty && !isLoading {
                Button {
                    withAnimation(.easeOut(duration: 0.15)) {
                        text = ""
                    }
                    selectionFeedback.selectionChanged()
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(.secondary.opacity(0.6))
                }
                .transition(.scale.combined(with: .opacity))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 22)
                .fill(Color(.systemGray6))
                .overlay(
                    RoundedRectangle(cornerRadius: 22)
                        .stroke(
                            isFocused ? Color.blue.opacity(0.4) : Color.clear,
                            lineWidth: 1.5
                        )
                )
        )
        .animation(.easeInOut(duration: 0.2), value: isFocused)
    }

    private var sendButton: some View {
        Button(action: triggerSend) {
            ZStack {
                Circle()
                    .fill(sendButtonGradient)
                    .frame(width: 42, height: 42)
                    .shadow(
                        color: canSend ? Color.blue.opacity(0.4) : Color.clear,
                        radius: 8,
                        y: 4
                    )

                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.9)
                } else {
                    Image(systemName: "arrow.up")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.white)
                }
            }
            .scaleEffect(sendButtonScale)
        }
        .disabled(!canSend)
        .animation(.spring(response: 0.3, dampingFraction: 0.6), value: sendButtonScale)
    }

    private var characterCountBar: some View {
        HStack {
            Spacer()
            Text("\(text.count)/\(maxCharacters)")
                .font(.caption2)
                .foregroundColor(text.count > maxCharacters ? .red : .secondary)
                .padding(.horizontal, 16)
                .padding(.vertical, 4)
        }
        .transition(.move(edge: .top).combined(with: .opacity))
    }

    private var inputBackground: some View {
        Rectangle()
            .fill(Color(.systemBackground))
            .shadow(color: .black.opacity(0.05), radius: 10, y: -5)
    }

    private var sendButtonGradient: LinearGradient {
        if canSend {
            return LinearGradient(
                colors: [
                    Color(red: 0.3, green: 0.5, blue: 1.0),
                    Color(red: 0.5, green: 0.3, blue: 0.95)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        } else {
            return LinearGradient(
                colors: [Color.gray.opacity(0.4), Color.gray.opacity(0.3)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        }
    }

    // MARK: - Helpers

    private var canSend: Bool {
        !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !isLoading &&
        text.count <= maxCharacters
    }

    private func triggerSend() {
        guard canSend else { return }

        // Haptic feedback
        impactFeedback.impactOccurred()

        // Button animation
        withAnimation(.spring(response: 0.2, dampingFraction: 0.5)) {
            sendButtonScale = 0.85
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.5)) {
                sendButtonScale = 1.0
            }
        }

        onSend()
    }
}

// MARK: - Typing Indicator

/// Animated typing indicator shown while waiting for AI response
struct TypingIndicator: View {
    @State private var dotAnimations: [Bool] = [false, false, false]
    @State private var shimmerOffset: CGFloat = -100
    @State private var appeared = false

    var body: some View {
        HStack(alignment: .bottom, spacing: 10) {
            // AI Avatar
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.purple.opacity(0.2), .blue.opacity(0.2)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 32, height: 32)

                Image(systemName: "sparkles")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.purple, .blue],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }
            .scaleEffect(appeared ? 1.0 : 0.5)
            .opacity(appeared ? 1.0 : 0)

            // Typing Bubble
            HStack(spacing: 5) {
                ForEach(0..<3, id: \.self) { index in
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [.secondary, .secondary.opacity(0.6)],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        .frame(width: 8, height: 8)
                        .offset(y: dotAnimations[index] ? -6 : 0)
                }
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(Color(.systemGray5))
                    .overlay(
                        // Shimmer effect
                        RoundedRectangle(cornerRadius: 20)
                            .fill(
                                LinearGradient(
                                    colors: [.clear, .white.opacity(0.3), .clear],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .offset(x: shimmerOffset)
                            .mask(RoundedRectangle(cornerRadius: 20))
                    )
            )
            .scaleEffect(appeared ? 1.0 : 0.8)
            .opacity(appeared ? 1.0 : 0)

            Spacer(minLength: 60)
        }
        .onAppear {
            // Entrance animation
            withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
                appeared = true
            }

            // Start dot animations with staggered delays
            for index in 0..<3 {
                DispatchQueue.main.asyncAfter(deadline: .now() + Double(index) * 0.15) {
                    withAnimation(
                        .easeInOut(duration: 0.4)
                        .repeatForever(autoreverses: true)
                    ) {
                        dotAnimations[index] = true
                    }
                }
            }

            // Shimmer animation
            withAnimation(.linear(duration: 1.5).repeatForever(autoreverses: false)) {
                shimmerOffset = 150
            }
        }
    }
}

// MARK: - Enhanced Suggestion Chip

struct SuggestionChip: View {
    let text: String
    let icon: String?
    let color: Color
    let action: () -> Void

    init(
        text: String,
        icon: String? = nil,
        color: Color = .blue,
        action: @escaping () -> Void
    ) {
        self.text = text
        self.icon = icon
        self.color = color
        self.action = action
    }

    var body: some View {
        Button(action: {
            let feedback = UIImpactFeedbackGenerator(style: .light)
            feedback.impactOccurred()
            action()
        }) {
            HStack(spacing: 6) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.caption)
                        .foregroundColor(color)
                }
                Text(text)
                    .font(.footnote)
                    .fontWeight(.medium)
            }
            .foregroundColor(.primary)
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color(.secondarySystemBackground))
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(color.opacity(0.2), lineWidth: 1)
                    )
            )
        }
        .buttonStyle(PressableButtonStyle())
    }
}

/// Custom button style that allows ScrollView gestures to work
struct PressableButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

// MARK: - Scroll to Bottom Button

struct ScrollToBottomButton: View {
    let action: () -> Void
    let unreadCount: Int

    @State private var isVisible = false

    var body: some View {
        Button(action: {
            let feedback = UIImpactFeedbackGenerator(style: .light)
            feedback.impactOccurred()
            action()
        }) {
            ZStack {
                Circle()
                    .fill(Color(.systemBackground))
                    .frame(width: 44, height: 44)
                    .shadow(color: .black.opacity(0.15), radius: 8, y: 4)

                Circle()
                    .stroke(Color.blue.opacity(0.3), lineWidth: 1)
                    .frame(width: 44, height: 44)

                Image(systemName: "chevron.down")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.blue)

                // Unread badge
                if unreadCount > 0 {
                    Text("\(min(unreadCount, 99))")
                        .font(.caption2)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.red)
                        .clipShape(Capsule())
                        .offset(x: 16, y: -16)
                }
            }
        }
        .scaleEffect(isVisible ? 1.0 : 0.5)
        .opacity(isVisible ? 1.0 : 0)
        .onAppear {
            withAnimation(.spring(response: 0.4, dampingFraction: 0.6)) {
                isVisible = true
            }
        }
    }
}

// MARK: - Enhanced Error Banner

struct ChatErrorBanner: View {
    let message: String
    let onDismiss: () -> Void
    let onRetry: (() -> Void)?

    @State private var appeared = false

    var body: some View {
        HStack(spacing: 12) {
            // Error icon with pulse
            ZStack {
                Circle()
                    .fill(Color.orange.opacity(0.2))
                    .frame(width: 32, height: 32)

                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 14))
                    .foregroundColor(.orange)
            }

            // Error message
            Text(message)
                .font(.footnote)
                .foregroundColor(.primary)
                .lineLimit(2)

            Spacer()

            // Actions
            HStack(spacing: 8) {
                if let onRetry = onRetry {
                    Button(action: onRetry) {
                        Text("Retry")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.blue)
                    }
                }

                Button(action: onDismiss) {
                    Image(systemName: "xmark")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.orange.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.orange.opacity(0.3), lineWidth: 1)
                )
        )
        .padding(.horizontal, 16)
        .offset(y: appeared ? 0 : -20)
        .opacity(appeared ? 1 : 0)
        .onAppear {
            withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
                appeared = true
            }
        }
    }
}

// MARK: - Previews

#Preview("Input - Empty") {
    VStack {
        Spacer()
        MessageInputView(
            text: .constant(""),
            isLoading: false,
            onMic: {},
            onSend: {}
        )
    }
}

#Preview("Input - With Text") {
    VStack {
        Spacer()
        MessageInputView(
            text: .constant("Hello, can you help me with my horoscope for today?"),
            isLoading: false,
            onMic: {},
            onSend: {}
        )
    }
}

#Preview("Input - Long Text") {
    VStack {
        Spacer()
        MessageInputView(
            text: .constant(String(repeating: "This is a long message. ", count: 50)),
            isLoading: false,
            onMic: {},
            onSend: {}
        )
    }
}

#Preview("Input - Loading") {
    VStack {
        Spacer()
        MessageInputView(
            text: .constant(""),
            isLoading: true,
            onMic: {},
            onSend: {}
        )
    }
}

#Preview("Typing Indicator") {
    TypingIndicator()
        .padding()
}

#Preview("Suggestion Chips") {
    ScrollView(.horizontal, showsIndicators: false) {
        HStack(spacing: 8) {
            SuggestionChip(text: "Today's horoscope", icon: "sparkles", color: .purple) {}
            SuggestionChip(text: "Check PNR", icon: "ticket.fill", color: .blue) {}
            SuggestionChip(text: "Weather", icon: "cloud.sun.fill", color: .orange) {}
            SuggestionChip(text: "Latest news", icon: "newspaper.fill", color: .red) {}
        }
        .padding()
    }
}

#Preview("Scroll to Bottom Button") {
    ZStack {
        Color(.systemBackground)
        ScrollToBottomButton(action: {}, unreadCount: 3)
    }
}

#Preview("Error Banner") {
    VStack {
        ChatErrorBanner(
            message: "Failed to send message. Please check your connection.",
            onDismiss: {},
            onRetry: {}
        )
        Spacer()
    }
}
