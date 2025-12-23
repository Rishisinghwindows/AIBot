import SwiftUI
import SwiftData

/// A single message bubble in the chat with animations
struct MessageBubble<M: DisplayableMessage>: View {
    let message: M
    var onRetry: (() -> Void)? = nil

    @State private var appeared = false
    @State private var isPressed = false

    private var isUser: Bool {
        message.isUser
    }

    var body: some View {
        HStack(alignment: .bottom, spacing: 10) {
            if isUser {
                Spacer(minLength: 50)
            } else {
                // AI Avatar for assistant messages
                aiAvatar
            }

            VStack(alignment: isUser ? .trailing : .leading, spacing: 6) {
                // Message content bubble
                messageBubble

                // Metadata row
                metadataRow
            }

            if !isUser {
                Spacer(minLength: 50)
            }
        }
        .scaleEffect(appeared ? 1.0 : 0.8)
        .opacity(appeared ? 1.0 : 0)
        .offset(x: appeared ? 0 : (isUser ? 30 : -30))
        .onAppear {
            withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
                appeared = true
            }
        }
    }

    // MARK: - Components

    private var aiAvatar: some View {
        ZStack {
            Circle()
                .fill(
                    LinearGradient(
                        colors: [.purple.opacity(0.15), .blue.opacity(0.15)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 30, height: 30)

            Image(systemName: "sparkles")
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(
                    LinearGradient(
                        colors: [.purple, .blue],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
        }
    }

    private var messageBubble: some View {
        Text(message.content)
            .font(.body)
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(bubbleBackground)
            .foregroundColor(isUser ? .white : .primary)
            .clipShape(BubbleShape(isUser: isUser))
            .shadow(
                color: isUser ? Color.blue.opacity(0.2) : Color.black.opacity(0.05),
                radius: 8,
                y: 4
            )
            .scaleEffect(isPressed ? 0.98 : 1.0)
            .contextMenu {
                Button(action: {
                    UIPasteboard.general.string = message.content
                    let feedback = UINotificationFeedbackGenerator()
                    feedback.notificationOccurred(.success)
                }) {
                    Label("Copy", systemImage: "doc.on.doc")
                }

                if !isUser {
                    Button(action: {
                        // Share action
                        let activityVC = UIActivityViewController(
                            activityItems: [message.content],
                            applicationActivities: nil
                        )
                        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                           let window = windowScene.windows.first,
                           let rootVC = window.rootViewController {
                            rootVC.present(activityVC, animated: true)
                        }
                    }) {
                        Label("Share", systemImage: "square.and.arrow.up")
                    }
                }
            }
            .simultaneousGesture(
                LongPressGesture(minimumDuration: 0.2)
                    .onChanged { _ in
                        withAnimation(.easeInOut(duration: 0.1)) {
                            isPressed = true
                        }
                    }
                    .onEnded { _ in
                        withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                            isPressed = false
                        }
                    }
            )
    }

    private var metadataRow: some View {
        HStack(spacing: 8) {
            // Category badge for assistant messages
            if !isUser, let category = message.displayCategory {
                categoryBadge(category)
            }

            // Timestamp
            Text(message.createdAt, style: .time)
                .font(.caption2)
                .foregroundColor(.secondary)

            // Status indicator for user messages
            if isUser {
                statusIndicator
            }

            // Sync status / retry for user messages
            if isUser && !message.displaySynced {
                retryButton
            }
        }
    }

    private func categoryBadge(_ category: String) -> some View {
        HStack(spacing: 4) {
            Image(systemName: categoryIcon(for: category))
                .font(.system(size: 9))
            Text(category.capitalized)
                .font(.caption2)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(categoryColor(for: category).opacity(0.12))
        )
        .foregroundColor(categoryColor(for: category))
    }

    private var statusIndicator: some View {
        Group {
            if message.displaySynced {
                Image(systemName: "checkmark")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
            }
        }
    }

    private var retryButton: some View {
        Button(action: {
            let feedback = UIImpactFeedbackGenerator(style: .medium)
            feedback.impactOccurred()
            onRetry?()
        }) {
            HStack(spacing: 4) {
                Image(systemName: "exclamationmark.circle.fill")
                    .font(.system(size: 12))
                Text("Retry")
                    .font(.caption2)
                    .fontWeight(.medium)
            }
            .foregroundColor(.orange)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(
                Capsule()
                    .fill(Color.orange.opacity(0.12))
            )
        }
    }

    @ViewBuilder
    private var bubbleBackground: some View {
        if isUser {
            LinearGradient(
                colors: [
                    Color(red: 0.3, green: 0.5, blue: 1.0),
                    Color(red: 0.4, green: 0.35, blue: 0.95)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        } else {
            Color(.systemGray6)
        }
    }

    // MARK: - Helpers

    private func categoryIcon(for category: String) -> String {
        switch category.lowercased() {
        case "horoscope", "astrology", "kundli", "zodiac": return "sparkles"
        case "weather": return "cloud.sun.fill"
        case "news": return "newspaper.fill"
        case "pnr", "train", "travel": return "train.side.front.car"
        case "tarot": return "suit.diamond.fill"
        case "numerology": return "number.circle.fill"
        case "panchang": return "calendar"
        default: return "bubble.left.fill"
        }
    }

    private func categoryColor(for category: String) -> Color {
        switch category.lowercased() {
        case "horoscope", "astrology", "kundli", "zodiac": return .purple
        case "weather": return .cyan
        case "news": return .red
        case "pnr", "train", "travel": return .blue
        case "tarot": return .indigo
        case "numerology": return .orange
        case "panchang": return .teal
        default: return .blue
        }
    }
}

// MARK: - Custom Bubble Shape

struct BubbleShape: Shape {
    let isUser: Bool
    let cornerRadius: CGFloat = 18
    let tailSize: CGFloat = 6

    func path(in rect: CGRect) -> Path {
        var path = Path()

        if isUser {
            // User bubble - tail on right
            path.move(to: CGPoint(x: rect.minX + cornerRadius, y: rect.minY))
            path.addLine(to: CGPoint(x: rect.maxX - cornerRadius, y: rect.minY))
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX, y: rect.minY + cornerRadius),
                control: CGPoint(x: rect.maxX, y: rect.minY)
            )
            path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY - cornerRadius))
            // Tail
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX + tailSize, y: rect.maxY),
                control: CGPoint(x: rect.maxX, y: rect.maxY)
            )
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX - cornerRadius, y: rect.maxY),
                control: CGPoint(x: rect.maxX, y: rect.maxY)
            )
            path.addLine(to: CGPoint(x: rect.minX + cornerRadius, y: rect.maxY))
            path.addQuadCurve(
                to: CGPoint(x: rect.minX, y: rect.maxY - cornerRadius),
                control: CGPoint(x: rect.minX, y: rect.maxY)
            )
            path.addLine(to: CGPoint(x: rect.minX, y: rect.minY + cornerRadius))
            path.addQuadCurve(
                to: CGPoint(x: rect.minX + cornerRadius, y: rect.minY),
                control: CGPoint(x: rect.minX, y: rect.minY)
            )
        } else {
            // Assistant bubble - tail on left
            path.move(to: CGPoint(x: rect.minX + cornerRadius, y: rect.minY))
            path.addLine(to: CGPoint(x: rect.maxX - cornerRadius, y: rect.minY))
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX, y: rect.minY + cornerRadius),
                control: CGPoint(x: rect.maxX, y: rect.minY)
            )
            path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY - cornerRadius))
            path.addQuadCurve(
                to: CGPoint(x: rect.maxX - cornerRadius, y: rect.maxY),
                control: CGPoint(x: rect.maxX, y: rect.maxY)
            )
            path.addLine(to: CGPoint(x: rect.minX + cornerRadius, y: rect.maxY))
            // Tail
            path.addQuadCurve(
                to: CGPoint(x: rect.minX - tailSize, y: rect.maxY),
                control: CGPoint(x: rect.minX, y: rect.maxY)
            )
            path.addQuadCurve(
                to: CGPoint(x: rect.minX, y: rect.maxY - cornerRadius),
                control: CGPoint(x: rect.minX, y: rect.maxY)
            )
            path.addLine(to: CGPoint(x: rect.minX, y: rect.minY + cornerRadius))
            path.addQuadCurve(
                to: CGPoint(x: rect.minX + cornerRadius, y: rect.minY),
                control: CGPoint(x: rect.minX, y: rect.minY)
            )
        }

        return path
    }
}

// MARK: - Preview

#Preview("User Message") {
    let container = try! ModelContainer(for: Message.self, Conversation.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
    return VStack(spacing: 16) {
        MessageBubble(
            message: Message(
                conversationId: UUID(),
                role: "user",
                content: "What's the weather like today?",
                isSynced: true
            )
        )
        MessageBubble(
            message: Message(
                conversationId: UUID(),
                role: "user",
                content: "Can you also check my horoscope for today? I'm a Leo.",
                isSynced: true
            )
        )
    }
    .padding()
    .modelContainer(container)
}

#Preview("Assistant Message") {
    let container = try! ModelContainer(for: Message.self, Conversation.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
    return VStack(spacing: 16) {
        MessageBubble(
            message: Message(
                conversationId: UUID(),
                role: "assistant",
                content: "The weather today is sunny with a high of 75°F. Perfect for outdoor activities!",
                category: "weather",
                isSynced: true
            )
        )
        MessageBubble(
            message: Message(
                conversationId: UUID(),
                role: "assistant",
                content: "Leo horoscope for today: The stars are aligned in your favor! Great day for creative pursuits and meeting new people.",
                category: "horoscope",
                isSynced: true
            )
        )
    }
    .padding()
    .modelContainer(container)
}

#Preview("Failed Message") {
    let container = try! ModelContainer(for: Message.self, Conversation.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
    return MessageBubble(
        message: Message(
            conversationId: UUID(),
            role: "user",
            content: "This message failed to send",
            isSynced: false
        ),
        onRetry: {}
    )
    .padding()
    .modelContainer(container)
}

#Preview("Long Conversation") {
    let container = try! ModelContainer(for: Message.self, Conversation.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
    return ScrollView {
        VStack(spacing: 12) {
            MessageBubble(
                message: Message(
                    conversationId: UUID(),
                    role: "user",
                    content: "Check PNR 2345678901",
                    isSynced: true
                )
            )
            MessageBubble(
                message: Message(
                    conversationId: UUID(),
                    role: "assistant",
                    content: "Your PNR status shows confirmed tickets for Train 12301 Rajdhani Express. Departure: New Delhi at 16:55, Arrival: Howrah at 10:05 next day. Coach: A1, Berth: 23 Lower.",
                    category: "pnr",
                    isSynced: true
                )
            )
            MessageBubble(
                message: Message(
                    conversationId: UUID(),
                    role: "user",
                    content: "What's my tarot reading for this week?",
                    isSynced: true
                )
            )
            MessageBubble(
                message: Message(
                    conversationId: UUID(),
                    role: "assistant",
                    content: "Your tarot card for this week is The Star. This card represents hope, inspiration, and renewal. It suggests that you're entering a period of calm after recent challenges.",
                    category: "tarot",
                    isSynced: true
                )
            )
        }
        .padding()
    }
    .modelContainer(container)
}

#Preview("Category Badges") {
    VStack(spacing: 12) {
        ForEach(["horoscope", "weather", "news", "pnr", "tarot", "numerology", "panchang"], id: \.self) { category in
            let container = try! ModelContainer(for: Message.self, Conversation.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
            MessageBubble(
                message: Message(
                    conversationId: UUID(),
                    role: "assistant",
                    content: "Sample response for \(category)",
                    category: category,
                    isSynced: true
                )
            )
            .modelContainer(container)
        }
    }
    .padding()
}
