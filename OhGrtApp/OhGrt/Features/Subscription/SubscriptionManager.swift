import Foundation
import StoreKit
import Combine

/// Manages in-app subscriptions using StoreKit 2
@MainActor
class SubscriptionManager: ObservableObject {
    /// Shared singleton instance
    static let shared = SubscriptionManager()

    /// Available subscription products
    @Published var products: [Product] = []

    /// Current subscription status
    @Published var subscriptionStatus: SubscriptionStatus = .notSubscribed

    /// Whether products are loading
    @Published var isLoading = false

    /// Error message if any
    @Published var errorMessage: String?

    /// Product identifiers for subscriptions
    private let productIdentifiers = [
        "com.ohgrt.subscription.monthly",
        "com.ohgrt.subscription.yearly"
    ]

    /// Transaction listener task
    private var updateListenerTask: Task<Void, Error>?

    private init() {
        updateListenerTask = listenForTransactions()
        Task {
            await loadProducts()
            await updateSubscriptionStatus()
        }
    }

    deinit {
        updateListenerTask?.cancel()
    }

    /// Subscription status enum
    enum SubscriptionStatus: Equatable {
        case notSubscribed
        case subscribed(productId: String, expiresDate: Date?)
        case expired

        var isActive: Bool {
            switch self {
            case .subscribed: return true
            default: return false
            }
        }

        var displayName: String {
            switch self {
            case .notSubscribed: return "Free"
            case .subscribed(let productId, _):
                if productId.contains("yearly") {
                    return "Premium (Yearly)"
                } else {
                    return "Premium (Monthly)"
                }
            case .expired: return "Expired"
            }
        }
    }

    /// Load available products from App Store
    func loadProducts() async {
        isLoading = true
        errorMessage = nil

        do {
            products = try await Product.products(for: productIdentifiers)
            products.sort { $0.price < $1.price }
        } catch {
            errorMessage = "Failed to load subscription options: \(error.localizedDescription)"
        }

        isLoading = false
    }

    /// Purchase a subscription
    func purchase(_ product: Product) async throws -> Bool {
        let result = try await product.purchase()

        switch result {
        case .success(let verification):
            let transaction = try checkVerified(verification)
            await updateSubscriptionStatus()
            await transaction.finish()
            return true

        case .userCancelled:
            return false

        case .pending:
            return false

        @unknown default:
            return false
        }
    }

    /// Restore previous purchases
    func restorePurchases() async {
        isLoading = true

        do {
            try await AppStore.sync()
            await updateSubscriptionStatus()
        } catch {
            errorMessage = "Failed to restore purchases: \(error.localizedDescription)"
        }

        isLoading = false
    }

    /// Update current subscription status
    func updateSubscriptionStatus() async {
        var foundSubscription: SubscriptionStatus = .notSubscribed

        for await result in Transaction.currentEntitlements {
            do {
                let transaction = try checkVerified(result)

                if transaction.productType == .autoRenewable {
                    if let expirationDate = transaction.expirationDate {
                        if expirationDate > Date() {
                            foundSubscription = .subscribed(
                                productId: transaction.productID,
                                expiresDate: expirationDate
                            )
                        } else {
                            foundSubscription = .expired
                        }
                    } else {
                        foundSubscription = .subscribed(
                            productId: transaction.productID,
                            expiresDate: nil
                        )
                    }
                }
            } catch {
                // Transaction verification failed
                continue
            }
        }

        subscriptionStatus = foundSubscription
    }

    /// Listen for transaction updates
    private func listenForTransactions() -> Task<Void, Error> {
        return Task.detached {
            for await result in Transaction.updates {
                do {
                    let transaction = try await self.checkVerified(result)
                    await self.updateSubscriptionStatus()
                    await transaction.finish()
                } catch {
                    // Transaction failed verification
                }
            }
        }
    }

    /// Verify a transaction
    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified:
            throw StoreError.failedVerification
        case .verified(let safe):
            return safe
        }
    }

    /// Store errors
    enum StoreError: Error {
        case failedVerification
    }
}

// MARK: - Product Extensions

extension Product {
    /// Subscription period description
    var periodDescription: String {
        guard let subscription = self.subscription else { return "" }

        switch subscription.subscriptionPeriod.unit {
        case .day:
            return subscription.subscriptionPeriod.value == 1 ? "Daily" : "\(subscription.subscriptionPeriod.value) Days"
        case .week:
            return subscription.subscriptionPeriod.value == 1 ? "Weekly" : "\(subscription.subscriptionPeriod.value) Weeks"
        case .month:
            return subscription.subscriptionPeriod.value == 1 ? "Monthly" : "\(subscription.subscriptionPeriod.value) Months"
        case .year:
            return subscription.subscriptionPeriod.value == 1 ? "Yearly" : "\(subscription.subscriptionPeriod.value) Years"
        @unknown default:
            return ""
        }
    }

    /// Monthly equivalent price for yearly subscriptions
    var monthlyEquivalentPrice: String? {
        guard let subscription = self.subscription,
              subscription.subscriptionPeriod.unit == .year else {
            return nil
        }
        let monthlyPrice = price / 12
        return monthlyPrice.formatted(.currency(code: priceFormatStyle.currencyCode ?? "USD"))
    }
}
