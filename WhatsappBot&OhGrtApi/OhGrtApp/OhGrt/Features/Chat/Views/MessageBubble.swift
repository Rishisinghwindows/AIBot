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
        HStack(alignment: .bottom, spacing: 8) {
            if !isUser {
                assistantAvatar
            } else {
                Spacer(minLength: 2)
            }

            VStack(alignment: isUser ? .trailing : .leading, spacing: 6) {
                // Message content bubble
                messageBubble

                // Metadata row
                metadataRow
            }

            if isUser {
                userAvatar
            } else {
                Spacer(minLength: 16)
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

    private var messageBubble: some View {
        let hasWeatherCard = !isUser && weatherCardData != nil
        let hasHoroscopeCard = !isUser && horoscopeCardData != nil
        let hasNewsCard = !isUser && newsCardData != nil
        let hasNumerologyCard = !isUser && numerologyCardData != nil
        let hasRichCard = hasWeatherCard || hasHoroscopeCard || hasNewsCard || hasNumerologyCard
        return VStack(alignment: .leading, spacing: 8) {
            if let card = weatherCardData {
                WeatherCard(data: card)
            }

            if let card = horoscopeCardData {
                HoroscopeCard(data: card)
            }

            if let card = newsCardData {
                NewsCard(items: card.items, category: card.category)
            }

            if let card = numerologyCardData {
                NumerologyCard(data: card)
            }

            if let mediaView = mediaAttachment {
                mediaView
            }

            if !hasRichCard && !message.content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                messageTextView
                    .font(.body)
                    .lineSpacing(3)
                    .textSelection(.enabled)
            }
        }
        .padding(.horizontal, hasRichCard ? 0 : 12)
        .padding(.vertical, hasRichCard ? 0 : 10)
        .background(bubbleBackground.opacity(hasRichCard ? 0 : 1))
        .clipShape(RoundedCornerBubble(isUser: isUser))
        .frame(maxWidth: maxBubbleWidth, alignment: isUser ? .trailing : .leading)
        .shadow(
            color: hasRichCard ? Color.clear : Color.black.opacity(0.06),
            radius: 6,
            y: 2
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

            if let mediaURL = message.displayMediaURL, let url = URL(string: mediaURL) {
                Button(action: {
                    UIApplication.shared.open(url)
                }) {
                    Label("Open Attachment", systemImage: "link")
                }
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
                    Color(red: 0.72, green: 0.35, blue: 0.94),
                    Color(red: 0.55, green: 0.18, blue: 0.85)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        } else {
            LinearGradient(
                colors: [
                    Color(red: 0.16, green: 0.12, blue: 0.2),
                    Color(red: 0.12, green: 0.1, blue: 0.16)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
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
        case "government", "govt": return "building.columns.fill"
        case "food": return "fork.knife.circle.fill"
        case "games": return "puzzlepiece.extension.fill"
        case "reminder": return "bell.fill"
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
        case "government", "govt": return .blue
        case "food": return .orange
        case "games": return .pink
        case "reminder": return .orange
        default: return .blue
        }
    }

    private var mediaAttachment: AnyView? {
        guard let mediaURL = message.displayMediaURL,
              let url = URL(string: mediaURL) else {
            return nil
        }

        if isImageURL(url) {
            return AnyView(
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .empty:
                        ZStack {
                            RoundedRectangle(cornerRadius: 12)
                                .fill(Color(.systemGray5))
                            ProgressView()
                        }
                    case .success(let image):
                        image
                            .resizable()
                            .scaledToFill()
                    case .failure:
                        attachmentLinkView(url: url, label: "Image attachment")
                    @unknown default:
                        attachmentLinkView(url: url, label: "Image attachment")
                    }
                }
                .frame(maxWidth: 220, maxHeight: 180)
                .clipped()
                .cornerRadius(12)
            )
        }

        return AnyView(attachmentLinkView(url: url, label: attachmentLabel(for: url)))
    }

    private var messageTextView: Text {
        Text(messageAttributedString(from: message.content))
    }

    private func messageAttributedString(from text: String) -> AttributedString {
        let baseColor: Color = isUser ? .white : Color(red: 0.9, green: 0.88, blue: 0.95)
        let linkColor: Color = isUser ? .white.opacity(0.95) : Color(red: 0.6, green: 0.78, blue: 1.0)
        var attributed = (try? AttributedString(markdown: text)) ?? AttributedString(text)
        attributed.foregroundColor = baseColor
        applyLinkAttributes(
            to: &attributed,
            in: text,
            linkColor: linkColor
        )
        return attributed
    }

    private func applyLinkAttributes(
        to attributed: inout AttributedString,
        in text: String,
        linkColor: Color
    ) {
        guard let detector = try? NSDataDetector(types: NSTextCheckingResult.CheckingType.link.rawValue) else {
            return
        }

        let matches = detector.matches(
            in: text,
            options: [],
            range: NSRange(text.startIndex..<text.endIndex, in: text)
        )
        guard !matches.isEmpty else { return }
        for match in matches {
            guard let url = match.url,
                  let range = Range(match.range, in: text),
                  let attributedRange = Range(range, in: attributed) else {
                continue
            }
            attributed[attributedRange].link = url
            attributed[attributedRange].foregroundColor = linkColor
            attributed[attributedRange].underlineStyle = .single
        }
    }

    private var maxBubbleWidth: CGFloat {
        UIScreen.main.bounds.width * 0.85
    }

    private var weatherCardData: WeatherCardData? {
        if let data = weatherCardDataFromStructuredJSON() {
            return data
        }

        guard !isUser else { return nil }
        let category = message.displayCategory?.lowercased() ?? ""
        let content = message.content
        if category == "weather"
            || content.lowercased().contains("weather")
            || content.lowercased().contains("temperature")
            || content.lowercased().contains("humidity") {
            return weatherCardDataFromText(content)
        }
        return nil
    }

    private var horoscopeCardData: HoroscopeCardData? {
        guard !isUser else { return nil }
        guard let object = structuredDataObject() else { return nil }
        let dataObject = (object["data"] as? [String: Any]) ?? object
        guard let sign = stringValue(dataObject["sign"] ?? dataObject["zodiac_sign"]) else {
            return nil
        }

        let horoscope = stringValue(
            dataObject["horoscope"]
                ?? dataObject["daily_horoscope"]
                ?? dataObject["description"]
        ) ?? ""
        let period = stringValue(dataObject["period"] ?? dataObject["date"]) ?? "Today"

        return HoroscopeCardData(
            sign: sign,
            period: period,
            horoscope: horoscope,
            luckyNumber: stringValue(dataObject["lucky_number"] ?? dataObject["luckyNumber"]),
            luckyColor: stringValue(dataObject["lucky_color"] ?? dataObject["luckyColor"]),
            mood: stringValue(dataObject["mood"]),
            compatibility: stringValue(dataObject["compatibility"]),
            focusArea: stringValue(dataObject["focus_area"] ?? dataObject["focusArea"]),
            advice: stringValue(dataObject["advice"])
        )
    }

    private var newsCardData: NewsCardData? {
        guard !isUser else { return nil }
        let category = (message.displayCategory ?? "").lowercased()
        if category != "news" && category != "get_news" && category != "headline" {
            return nil
        }

        guard let object = structuredDataObject() else { return nil }
        let dataObject = (object["data"] as? [String: Any]) ?? object

        let items = extractNewsItems(from: dataObject)
        guard !items.isEmpty else { return nil }

        let headlineCategory = stringValue(dataObject["category"] ?? dataObject["news_category"])
        return NewsCardData(items: items, category: headlineCategory)
    }

    private var numerologyCardData: NumerologyCardData? {
        guard !isUser else { return nil }
        let category = (message.displayCategory ?? "").lowercased()
        if category != "numerology" {
            return nil
        }
        guard let object = structuredDataObject() else { return nil }
        let dataObject = (object["data"] as? [String: Any]) ?? object

        let name = stringValue(dataObject["name"]) ?? "Numerology"
        let nameNumber = stringValue(dataObject["name_number"] ?? dataObject["nameNumber"])
        let lifePath = stringValue(dataObject["life_path_number"] ?? dataObject["lifePathNumber"])
        let expression = stringValue(dataObject["expression_number"] ?? dataObject["expressionNumber"])
        let soulUrge = stringValue(dataObject["soul_urge_number"] ?? dataObject["soulUrgeNumber"])
        let personality = stringValue(dataObject["personality_number"] ?? dataObject["personalityNumber"])

        let nameMeaning = dataObject["name_meaning"] as? [String: Any]
        let lifePathMeaning = dataObject["life_path_meaning"] as? [String: Any]

        let luckyNumbers = dataObject["lucky_numbers"] as? [Any] ?? []
        let luckyNumberText = luckyNumbers.compactMap { stringValue($0) }

        return NumerologyCardData(
            name: name,
            nameNumber: nameNumber,
            nameTrait: stringValue(nameMeaning?["trait"]),
            nameDescription: stringValue(nameMeaning?["description"]),
            lifePathNumber: lifePath,
            lifePathTrait: stringValue(lifePathMeaning?["trait"]),
            expressionNumber: expression,
            soulUrgeNumber: soulUrge,
            personalityNumber: personality,
            luckyNumbers: luckyNumberText
        )
    }

    private func extractNewsItems(from object: [String: Any]) -> [NewsItem] {
        let containers: [Any?] = [
            object["articles"],
            object["items"],
            object["news"],
            object["data"]
        ]

        for container in containers {
            if let items = container as? [[String: Any]] {
                return items.compactMap { mapNewsItem($0) }
            }
        }

        if let single = mapNewsItem(object) {
            return [single]
        }
        return []
    }

    private func mapNewsItem(_ object: [String: Any]) -> NewsItem? {
        let title = stringValue(object["title"] ?? object["headline"])
        if title == nil { return nil }
        return NewsItem(
            title: title ?? "",
            summary: stringValue(object["summary"] ?? object["description"]),
            source: stringValue(object["source"]),
            url: stringValue(object["url"]),
            publishedAt: stringValue(object["published_at"] ?? object["publishedAt"]),
            imageURL: stringValue(object["image_url"] ?? object["imageUrl"]),
            category: stringValue(object["category"])
        )
    }

    private func structuredDataObject() -> [String: Any]? {
        guard let json = message.displayStructuredDataJSON,
              let data = json.data(using: .utf8),
              let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return nil
        }
        return object
    }

    private func weatherCardDataFromStructuredJSON() -> WeatherCardData? {
        guard let object = structuredDataObject(),
              let temp = doubleValue(object["temperature"] ?? object["temperature_c"]) else {
            return nil
        }

        let city = object["city"] as? String ?? "Unknown"
        let humidity = doubleValue(object["humidity"]) ?? 0
        let condition = object["condition"] as? String ?? "—"

        var windSpeed: Double?
        var visibilityKm: Double?

        if let raw = object["raw"] as? [String: Any] {
            if let wind = raw["wind"] as? [String: Any] {
                windSpeed = doubleValue(wind["speed"])
            }
            if let visibility = raw["visibility"] as? Double {
                visibilityKm = visibility / 1000.0
            } else if let visibility = raw["visibility"] as? Int {
                visibilityKm = Double(visibility) / 1000.0
            }
        }

        return WeatherCardData(
            city: city,
            temperature: temp,
            condition: condition,
            humidity: humidity,
            windSpeed: windSpeed,
            visibilityKm: visibilityKm
        )
    }

    private func weatherCardDataFromText(_ text: String) -> WeatherCardData? {
        let city = firstMatch(
            pattern: "(?i)weather\\s+in\\s+([^|\\n]+)",
            text: text
        )
            ?? firstMatch(
                pattern: "(?i)weather\\s+(?:for|in)\\s+([^:\\n]+)",
                text: text
            )
            ?? "Unknown"

        let temp = firstDoubleMatch(
            pattern: "(?i)temperature[^0-9]*([0-9]+(?:\\.[0-9]+)?)\\s*°?c",
            text: text
        )
            ?? firstDoubleMatch(pattern: "([0-9]+(?:\\.[0-9]+)?)\\s*°c", text: text)
        guard let temperature = temp else { return nil }

        let humidity = firstDoubleMatch(
            pattern: "(?i)humidity[^0-9]*([0-9]+(?:\\.[0-9]+)?)",
            text: text
        ) ?? 0
        let condition = firstMatch(
            pattern: "\\|\\s*([^|]+)\\s*temperature",
            text: text
        )
            ?? firstMatch(pattern: "(?i)condition[:\\s]*([A-Za-z\\s]+)", text: text)
            ?? firstMatch(pattern: "(?i)\\n?([A-Za-z\\s]+)\\s*\\n?feels like", text: text)
            ?? "—"
        let wind = firstDoubleMatch(
            pattern: "(?i)wind[^0-9]*([0-9]+(?:\\.[0-9]+)?)\\s*m/s",
            text: text
        )
        let visibility = firstDoubleMatch(
            pattern: "(?i)visibility[^0-9]*([0-9]+(?:\\.[0-9]+)?)\\s*km",
            text: text
        )

        return WeatherCardData(
            city: city.replacingOccurrences(of: "  ", with: " ").trimmingCharacters(in: .whitespacesAndNewlines),
            temperature: temperature,
            condition: condition.trimmingCharacters(in: .whitespacesAndNewlines),
            humidity: humidity,
            windSpeed: wind,
            visibilityKm: visibility
        )
    }

    private func firstDoubleMatch(pattern: String, text: String) -> Double? {
        guard let match = firstMatch(pattern: pattern, text: text) else { return nil }
        return Double(match)
    }

    private func firstMatch(pattern: String, text: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: pattern, options: []) else { return nil }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        guard let match = regex.firstMatch(in: text, options: [], range: range),
              match.numberOfRanges > 1,
              let matchRange = Range(match.range(at: 1), in: text) else { return nil }
        return String(text[matchRange])
    }

    private func stringValue(_ value: Any?) -> String? {
        switch value {
        case let string as String:
            return string
        case let number as Double:
            return String(number)
        case let number as Int:
            return String(number)
        default:
            return nil
        }
    }

    private func doubleValue(_ value: Any?) -> Double? {
        switch value {
        case let number as Double:
            return number
        case let number as Int:
            return Double(number)
        case let number as Float:
            return Double(number)
        case let string as String:
            return Double(string)
        default:
            return nil
        }
    }

    private var assistantAvatar: some View {
        ZStack {
            Circle()
                .fill(Color(red: 0.14, green: 0.11, blue: 0.18))
                .frame(width: 30, height: 30)
            Image(systemName: "sparkles")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(Color(red: 0.78, green: 0.72, blue: 0.9))
        }
    }

    private var userAvatar: some View {
        ZStack {
            Circle()
                .fill(Color(red: 0.72, green: 0.35, blue: 0.94))
                .frame(width: 30, height: 30)
            Image(systemName: "person.fill")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(.white)
        }
    }

    private func attachmentLabel(for url: URL) -> String {
        if isAudioURL(url) {
            return "Audio attachment"
        }
        if isVideoURL(url) {
            return "Video attachment"
        }
        return "File attachment"
    }

    private func attachmentLinkView(url: URL, label: String) -> some View {
        Link(destination: url) {
            HStack(spacing: 8) {
                Image(systemName: attachmentIcon(for: url))
                    .font(.system(size: 14, weight: .semibold))
                Text(label)
                    .font(.caption)
                    .fontWeight(.semibold)
            }
            .foregroundColor(isUser ? .white : .primary)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(
                Capsule()
                    .fill(isUser ? Color.white.opacity(0.2) : Color.black.opacity(0.06))
            )
        }
    }

    private func attachmentIcon(for url: URL) -> String {
        if isAudioURL(url) {
            return "waveform"
        }
        if isVideoURL(url) {
            return "play.rectangle.fill"
        }
        return "paperclip"
    }

    private func isImageURL(_ url: URL) -> Bool {
        let ext = url.pathExtension.lowercased()
        return ["jpg", "jpeg", "png", "gif", "webp", "heic"].contains(ext)
    }

    private func isAudioURL(_ url: URL) -> Bool {
        let ext = url.pathExtension.lowercased()
        return ["mp3", "m4a", "aac", "wav", "ogg"].contains(ext)
    }

    private func isVideoURL(_ url: URL) -> Bool {
        let ext = url.pathExtension.lowercased()
        return ["mp4", "mov", "m4v"].contains(ext)
    }
}

// MARK: - Custom Bubble Shape

struct RoundedCornerBubble: Shape {
    let isUser: Bool

    func path(in rect: CGRect) -> Path {
        let large: CGFloat = 18
        let small: CGFloat = 6
        let radii = isUser
            ? RectangleCornerRadii(
                topLeading: large,
                bottomLeading: large,
                bottomTrailing: large,
                topTrailing: small
            )
            : RectangleCornerRadii(
                topLeading: small,
                bottomLeading: large,
                bottomTrailing: large,
                topTrailing: large
            )
        return Path(roundedRect: rect, cornerRadii: radii)
    }
}

private struct WeatherCardData: Equatable {
    let city: String
    let temperature: Double
    let condition: String
    let humidity: Double
    let windSpeed: Double?
    let visibilityKm: Double?
}

private struct HoroscopeCardData: Equatable {
    let sign: String
    let period: String
    let horoscope: String
    let luckyNumber: String?
    let luckyColor: String?
    let mood: String?
    let compatibility: String?
    let focusArea: String?
    let advice: String?
}

private struct HoroscopeCard: View {
    let data: HoroscopeCardData

    var body: some View {
        VStack(spacing: 0) {
            header
            content
        }
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.1, green: 0.08, blue: 0.16),
                    Color.black
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.white.opacity(0.06), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.35), radius: 18, y: 10)
    }

    private var header: some View {
        HStack(spacing: 12) {
            Text(zodiacEmoji)
                .font(.system(size: 34))
            VStack(alignment: .leading, spacing: 2) {
                Text(data.sign.capitalized)
                    .font(.headline)
                    .foregroundColor(.white)
                Text(data.period.capitalized)
                    .font(.caption)
                    .foregroundColor(Color.white.opacity(0.6))
            }
            Spacer()
            Image(systemName: "sparkles")
                .foregroundColor(Color.yellow.opacity(0.9))
        }
        .padding(14)
        .background(
            LinearGradient(
                colors: headerGradientColors,
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }

    private var content: some View {
        VStack(alignment: .leading, spacing: 12) {
            if !data.horoscope.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 6) {
                        Image(systemName: "star.fill")
                            .font(.caption)
                            .foregroundColor(Color.yellow.opacity(0.9))
                        Text("Today's Reading")
                            .font(.caption)
                            .foregroundColor(Color.white.opacity(0.7))
                    }
                    Text(data.horoscope)
                        .font(.subheadline)
                        .foregroundColor(Color.white.opacity(0.75))
                }
                .padding(12)
                .background(Color.white.opacity(0.06))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }

            if data.luckyNumber != nil || data.luckyColor != nil {
                HStack(spacing: 10) {
                    if let number = data.luckyNumber {
                        VStack(spacing: 4) {
                            Text("Lucky Number")
                                .font(.caption2)
                                .foregroundColor(Color.white.opacity(0.5))
                            Text(number)
                                .font(.title3)
                                .foregroundColor(Color.purple.opacity(0.9))
                        }
                        .frame(maxWidth: .infinity)
                        .padding(10)
                        .background(Color.white.opacity(0.05))
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                    }

                    if let color = data.luckyColor {
                        VStack(spacing: 4) {
                            Text("Lucky Color")
                                .font(.caption2)
                                .foregroundColor(Color.white.opacity(0.5))
                            Text(color.capitalized)
                                .font(.caption)
                                .padding(.horizontal, 10)
                                .padding(.vertical, 4)
                                .background(Color.white.opacity(0.08))
                                .clipShape(Capsule())
                                .foregroundColor(.white)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(10)
                        .background(Color.white.opacity(0.05))
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }
            }

            if data.mood != nil || data.compatibility != nil || data.focusArea != nil {
                VStack(alignment: .leading, spacing: 6) {
                    if let mood = data.mood {
                        HoroscopeMetaRow(icon: "moon.stars.fill", label: "Mood", value: mood)
                    }
                    if let focus = data.focusArea {
                        HoroscopeMetaRow(icon: "star.circle.fill", label: "Focus", value: focus)
                    }
                    if let match = data.compatibility {
                        HoroscopeMetaRow(icon: "sun.max.fill", label: "Best match", value: match)
                    }
                }
                .padding(.top, 6)
            }

            if let advice = data.advice, !advice.isEmpty {
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "sparkles")
                        .font(.caption)
                        .foregroundColor(Color.purple.opacity(0.8))
                    Text(advice)
                        .font(.caption)
                        .foregroundColor(Color.white.opacity(0.75))
                }
                .padding(10)
                .background(Color.purple.opacity(0.12))
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }
        }
        .padding(14)
    }

    private var zodiacEmoji: String {
        let key = data.sign.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return HoroscopeCard.zodiacEmojis[key] ?? "⭐"
    }

    private var headerGradientColors: [Color] {
        let key = data.sign.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return HoroscopeCard.zodiacGradients[key] ?? [
            Color.purple.opacity(0.35),
            Color.purple.opacity(0.15)
        ]
    }

    private static let zodiacEmojis: [String: String] = [
        "aries": "♈", "taurus": "♉", "gemini": "♊", "cancer": "♋",
        "leo": "♌", "virgo": "♍", "libra": "♎", "scorpio": "♏",
        "sagittarius": "♐", "capricorn": "♑", "aquarius": "♒", "pisces": "♓"
    ]

    private static let zodiacGradients: [String: [Color]] = [
        "aries": [Color.red.opacity(0.35), Color.orange.opacity(0.2)],
        "taurus": [Color.green.opacity(0.35), Color.mint.opacity(0.2)],
        "gemini": [Color.yellow.opacity(0.35), Color.orange.opacity(0.2)],
        "cancer": [Color.blue.opacity(0.35), Color.cyan.opacity(0.2)],
        "leo": [Color.orange.opacity(0.35), Color.yellow.opacity(0.2)],
        "virgo": [Color.green.opacity(0.35), Color.teal.opacity(0.2)],
        "libra": [Color.pink.opacity(0.35), Color.purple.opacity(0.2)],
        "scorpio": [Color.purple.opacity(0.35), Color.indigo.opacity(0.2)],
        "sagittarius": [Color.indigo.opacity(0.35), Color.blue.opacity(0.2)],
        "capricorn": [Color.gray.opacity(0.35), Color.black.opacity(0.2)],
        "aquarius": [Color.cyan.opacity(0.35), Color.blue.opacity(0.2)],
        "pisces": [Color.purple.opacity(0.35), Color.pink.opacity(0.2)]
    ]
}

private struct HoroscopeMetaRow: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(Color.white.opacity(0.5))
            Text("\(label):")
                .font(.caption)
                .foregroundColor(Color.white.opacity(0.5))
            Text(value.capitalized)
                .font(.caption)
                .foregroundColor(Color.white.opacity(0.8))
        }
    }
}

private struct NewsCardData: Equatable {
    let items: [NewsItem]
    let category: String?
}

private struct NewsItem: Equatable {
    let title: String
    let summary: String?
    let source: String?
    let url: String?
    let publishedAt: String?
    let imageURL: String?
    let category: String?
}

private struct NewsCard: View {
    let items: [NewsItem]
    let category: String?

    var body: some View {
        VStack(spacing: 0) {
            header
            VStack(spacing: 10) {
                ForEach(items.prefix(5), id: \.title) { item in
                    NewsItemRow(item: item)
                }
            }
            .padding(14)
        }
        .background(
            LinearGradient(
                colors: [
                    Color(red: 0.08, green: 0.07, blue: 0.12),
                    Color.black
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.white.opacity(0.06), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.35), radius: 18, y: 10)
    }

    private var header: some View {
        HStack(spacing: 10) {
            Image(systemName: "newspaper.fill")
                .foregroundColor(Color.cyan.opacity(0.85))
            Text(categoryTitle)
                .font(.headline)
                .foregroundColor(.white)
            Spacer()
            Text("\(items.count) articles")
                .font(.caption2)
                .foregroundColor(Color.white.opacity(0.6))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.white.opacity(0.08))
                .clipShape(Capsule())
        }
        .padding(14)
        .background(
            LinearGradient(
                colors: [
                    Color.cyan.opacity(0.2),
                    Color.blue.opacity(0.08)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }

    private var categoryTitle: String {
        if let category, !category.isEmpty {
            return "\(category.capitalized) News"
        }
        return "Latest News"
    }
}

private struct NewsItemRow: View {
    let item: NewsItem

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .top, spacing: 10) {
                VStack(alignment: .leading, spacing: 4) {
                    if let url = item.url, let link = URL(string: url) {
                        Link(destination: link) {
                            Text(item.title)
                                .font(.subheadline)
                                .foregroundColor(.white)
                                .multilineTextAlignment(.leading)
                        }
                    } else {
                        Text(item.title)
                            .font(.subheadline)
                            .foregroundColor(.white)
                            .multilineTextAlignment(.leading)
                    }

                    if let summary = item.summary, !summary.isEmpty {
                        Text(summary)
                            .font(.caption)
                            .foregroundColor(Color.white.opacity(0.6))
                            .lineLimit(2)
                    }
                }

                if let imageURL = item.imageURL, let url = URL(string: imageURL) {
                    AsyncImage(url: url) { phase in
                        switch phase {
                        case .empty:
                            RoundedRectangle(cornerRadius: 8)
                                .fill(Color.white.opacity(0.08))
                        case .success(let image):
                            image
                                .resizable()
                                .scaledToFill()
                        default:
                            RoundedRectangle(cornerRadius: 8)
                                .fill(Color.white.opacity(0.08))
                        }
                    }
                    .frame(width: 60, height: 60)
                    .clipped()
                    .cornerRadius(8)
                }
            }

            HStack(spacing: 10) {
                if let source = item.source, !source.isEmpty {
                    Label(source, systemImage: "tag")
                        .font(.caption2)
                        .foregroundColor(Color.white.opacity(0.5))
                }
                if let publishedAt = item.publishedAt, !publishedAt.isEmpty {
                    Label(publishedAt, systemImage: "clock")
                        .font(.caption2)
                        .foregroundColor(Color.white.opacity(0.5))
                }
            }
        }
        .padding(10)
        .background(Color.white.opacity(0.04))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

private struct NumerologyCardData: Equatable {
    let name: String
    let nameNumber: String?
    let nameTrait: String?
    let nameDescription: String?
    let lifePathNumber: String?
    let lifePathTrait: String?
    let expressionNumber: String?
    let soulUrgeNumber: String?
    let personalityNumber: String?
    let luckyNumbers: [String]
}

private struct NumerologyCard: View {
    let data: NumerologyCardData

    var body: some View {
        ZStack(alignment: .topTrailing) {
            RoundedRectangle(cornerRadius: 20)
                .fill(
                    LinearGradient(
                        colors: [
                            Color(red: 0.07, green: 0.05, blue: 0.15),
                            Color(red: 0.12, green: 0.07, blue: 0.2)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )

            Circle()
                .fill(Color.pink.opacity(0.15))
                .frame(width: 120, height: 120)
                .offset(x: 40, y: -40)

            VStack(alignment: .leading, spacing: 14) {
                header
                heroRow
                if let description = data.nameDescription, !description.isEmpty {
                    descriptionBlock(text: description)
                }
                detailChips
                if !data.luckyNumbers.isEmpty {
                    luckyRow
                }
            }
            .padding(16)
        }
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color.white.opacity(0.08), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.35), radius: 18, y: 10)
    }

    private var header: some View {
        HStack(spacing: 10) {
            Image(systemName: "circle.grid.2x2.fill")
                .foregroundColor(Color.pink.opacity(0.9))
            VStack(alignment: .leading, spacing: 2) {
                Text(data.name)
                    .font(.headline)
                    .foregroundColor(.white)
                Text(data.nameTrait?.capitalized ?? "Numerology Insight")
                    .font(.caption)
                    .foregroundColor(Color.white.opacity(0.6))
            }
            Spacer()
            Text("#\(data.lifePathNumber ?? "—")")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(Color.white.opacity(0.7))
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.white.opacity(0.08))
                .clipShape(Capsule())
        }
    }

    private var heroRow: some View {
        HStack(alignment: .top, spacing: 14) {
            NumerologyHeroNumber(
                title: "Life Path",
                value: data.lifePathNumber ?? "—",
                accent: Color.purple
            )

            VStack(alignment: .leading, spacing: 8) {
                NumerologyHeroNumber(
                    title: "Name Number",
                    value: data.nameNumber ?? "—",
                    accent: Color.orange
                )

                if let trait = data.lifePathTrait, !trait.isEmpty {
                    Text(trait.capitalized)
                        .font(.caption)
                        .foregroundColor(Color.white.opacity(0.7))
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var detailChips: some View {
        VStack(spacing: 8) {
            HStack(spacing: 8) {
                NumerologyChip(label: "Expression", value: data.expressionNumber)
                NumerologyChip(label: "Soul Urge", value: data.soulUrgeNumber)
            }
            HStack(spacing: 8) {
                NumerologyChip(label: "Personality", value: data.personalityNumber)
                NumerologyChip(label: "Trait", value: data.lifePathTrait)
            }
        }
    }

    private var luckyRow: some View {
        HStack(spacing: 10) {
            Image(systemName: "sparkle")
                .font(.caption)
                .foregroundColor(Color.pink.opacity(0.85))
            Text("Lucky")
                .font(.caption)
                .foregroundColor(Color.white.opacity(0.6))
            Text(data.luckyNumbers.joined(separator: " • "))
                .font(.caption)
                .foregroundColor(.white)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(Color.white.opacity(0.06))
        .clipShape(Capsule())
    }

    private func descriptionBlock(text: String) -> some View {
        Text(text)
            .font(.caption)
            .foregroundColor(Color.white.opacity(0.75))
            .padding(10)
            .background(Color.white.opacity(0.06))
            .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

private struct NumerologyHeroNumber: View {
    let title: String
    let value: String
    let accent: Color

    var body: some View {
        VStack(spacing: 6) {
            Text(title)
                .font(.caption2)
                .foregroundColor(Color.white.opacity(0.6))
            Text(value)
                .font(.title)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .frame(width: 64, height: 64)
                .background(
                    LinearGradient(
                        colors: [
                            accent.opacity(0.7),
                            accent.opacity(0.3)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .clipShape(Circle())
        }
        .padding(10)
        .background(Color.white.opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}

private struct NumerologyChip: View {
    let label: String
    let value: String?

    var body: some View {
        HStack(spacing: 6) {
            Text(label)
                .font(.caption2)
                .foregroundColor(Color.white.opacity(0.6))
            Spacer()
            Text(value ?? "—")
                .font(.caption)
                .foregroundColor(.white)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(Color.white.opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}
private struct WeatherCard: View {
    let data: WeatherCardData

    var body: some View {
        VStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 14) {
                HStack(spacing: 8) {
                    Image(systemName: "location.fill")
                        .font(.caption)
                        .foregroundColor(Color.white.opacity(0.55))
                    Text(data.city)
                        .font(.subheadline)
                        .foregroundColor(Color.white.opacity(0.65))
                }

                HStack(alignment: .center, spacing: 16) {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack(alignment: .firstTextBaseline, spacing: 6) {
                            Text("\(Int(round(data.temperature)))")
                                .font(.system(size: 44, weight: .bold))
                                .foregroundColor(.white)
                            Text("°C")
                                .font(.headline)
                                .foregroundColor(Color.white.opacity(0.7))
                        }
                        Text(data.condition.capitalized)
                            .font(.headline)
                            .foregroundColor(Color.white.opacity(0.8))
                        Text("Feels like \(Int(round(data.temperature)))°C")
                            .font(.footnote)
                            .foregroundColor(Color.white.opacity(0.5))
                    }

                    Spacer()

                    Image(systemName: "cloud.fill")
                        .font(.system(size: 46))
                        .foregroundColor(Color.white.opacity(0.6))
                }
            }
            .padding(16)
            .background(
                LinearGradient(
                    colors: [
                        Color(red: 0.17, green: 0.1, blue: 0.24),
                        Color(red: 0.08, green: 0.06, blue: 0.11)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )

            Divider()
                .background(Color.white.opacity(0.06))

            HStack {
                WeatherStat(
                    icon: "drop.fill",
                    iconColor: .cyan,
                    label: "Humidity",
                    value: "\(Int(round(data.humidity)))%"
                )

                Divider()
                    .background(Color.white.opacity(0.08))

                WeatherStat(
                    icon: "wind",
                    iconColor: .white.opacity(0.7),
                    label: "Wind",
                    value: windValue
                )

                Divider()
                    .background(Color.white.opacity(0.08))

                WeatherStat(
                    icon: "eye.fill",
                    iconColor: .orange,
                    label: "Visibility",
                    value: visibilityValue
                )
            }
            .padding(.vertical, 12)
            .background(Color(red: 0.07, green: 0.06, blue: 0.1))
        }
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(Color.white.opacity(0.06), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.35), radius: 18, y: 10)
    }

    private var windValue: String {
        guard let speed = data.windSpeed else { return "—" }
        return String(format: "%.1f m/s", speed)
    }

    private var visibilityValue: String {
        guard let km = data.visibilityKm else { return "—" }
        return String(format: "%.1f km", km)
    }
}

private struct WeatherStat: View {
    let icon: String
    let iconColor: Color
    let label: String
    let value: String

    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(iconColor)
            Text(label)
                .font(.caption2)
                .foregroundColor(Color.white.opacity(0.55))
            Text(value)
                .font(.subheadline)
                .foregroundColor(.white)
        }
        .frame(maxWidth: .infinity)
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
