import Foundation
import Combine

/// Tracks daily usage for free tier limits
@MainActor
class UsageTracker: ObservableObject {
    /// Shared singleton instance
    static let shared = UsageTracker()

    /// Number of messages sent today
    @Published private(set) var dailyMessageCount: Int = 0

    /// Daily message limit for free users
    let freeMessageLimit = 10

    /// UserDefaults keys
    private enum Keys {
        static let dailyMessageCount = "usage_daily_message_count"
        static let lastUsageDate = "usage_last_date"
    }

    private init() {
        loadUsage()
    }

    /// Check if user can send a message (considering subscription status)
    func canSendMessage() -> Bool {
        // Premium users have unlimited messages
        if SubscriptionManager.shared.subscriptionStatus.isActive {
            return true
        }

        // Free users have daily limit
        return dailyMessageCount < freeMessageLimit
    }

    /// Record a message being sent
    func recordMessageSent() {
        // Don't count against premium users
        if SubscriptionManager.shared.subscriptionStatus.isActive {
            return
        }

        dailyMessageCount += 1
        saveUsage()
    }

    /// Get remaining messages for free users
    var remainingMessages: Int {
        if SubscriptionManager.shared.subscriptionStatus.isActive {
            return Int.max
        }
        return max(0, freeMessageLimit - dailyMessageCount)
    }

    /// Get usage description for UI
    var usageDescription: String {
        if SubscriptionManager.shared.subscriptionStatus.isActive {
            return "Unlimited messages"
        }
        return "\(remainingMessages)/\(freeMessageLimit) messages remaining today"
    }

    /// Check if user is at limit
    var isAtLimit: Bool {
        !canSendMessage()
    }

    // MARK: - Persistence

    private func loadUsage() {
        let defaults = UserDefaults.standard

        // Check if we need to reset for a new day
        if let lastDate = defaults.object(forKey: Keys.lastUsageDate) as? Date {
            if !Calendar.current.isDateInToday(lastDate) {
                // Reset for new day
                dailyMessageCount = 0
                defaults.set(Date(), forKey: Keys.lastUsageDate)
                defaults.set(0, forKey: Keys.dailyMessageCount)
                return
            }
        } else {
            // First run
            defaults.set(Date(), forKey: Keys.lastUsageDate)
        }

        dailyMessageCount = defaults.integer(forKey: Keys.dailyMessageCount)
    }

    private func saveUsage() {
        let defaults = UserDefaults.standard
        defaults.set(dailyMessageCount, forKey: Keys.dailyMessageCount)
        defaults.set(Date(), forKey: Keys.lastUsageDate)
    }

    /// Reset usage (for testing or when subscription is purchased)
    func resetUsage() {
        dailyMessageCount = 0
        let defaults = UserDefaults.standard
        defaults.set(0, forKey: Keys.dailyMessageCount)
        defaults.set(Date(), forKey: Keys.lastUsageDate)
    }
}
