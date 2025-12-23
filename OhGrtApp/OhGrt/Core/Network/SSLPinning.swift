import Foundation
import Security
import CommonCrypto

/// SSL Pinning delegate for URLSession
/// Validates server certificates against pinned certificates
final class SSLPinningDelegate: NSObject, URLSessionDelegate {

    /// The host to pin certificates for
    private let pinnedHost = "api.d23.ai"

    /// Pinned certificate data loaded from bundle
    private var pinnedCertificates: [Data] = []

    /// Certificate expiry date for monitoring (embedded cert expires March 4, 2026)
    private static let embeddedCertExpiryDate: Date = {
        var components = DateComponents()
        components.year = 2026
        components.month = 3
        components.day = 4
        return Calendar.current.date(from: components) ?? Date.distantFuture
    }()

    /// Days before expiry to start warning
    private static let expiryWarningDays = 30

    override init() {
        super.init()
        loadPinnedCertificates()
        checkCertificateExpiry()
    }

    /// Check if embedded certificate is close to expiry and log warning
    private func checkCertificateExpiry() {
        let now = Date()
        let daysUntilExpiry = Calendar.current.dateComponents([.day], from: now, to: Self.embeddedCertExpiryDate).day ?? 0

        if daysUntilExpiry <= 0 {
            print("[SSLPinning] ⚠️ CRITICAL: Embedded certificate has EXPIRED!")
            print("[SSLPinning] ⚠️ App may fail to connect to API. Update required immediately.")
            // In production, this should trigger an alert or force update
        } else if daysUntilExpiry <= Self.expiryWarningDays {
            print("[SSLPinning] ⚠️ WARNING: Embedded certificate expires in \(daysUntilExpiry) days")
            print("[SSLPinning] ⚠️ Schedule app update with new certificate before \(Self.embeddedCertExpiryDate)")
        } else if AppConfig.shared.allowDebugLogging {
            print("[SSLPinning] Certificate valid for \(daysUntilExpiry) more days")
        }
    }

    /// Check certificate status - can be called to verify cert health
    static func certificateStatus() -> CertificateStatus {
        let now = Date()
        let daysUntilExpiry = Calendar.current.dateComponents([.day], from: now, to: embeddedCertExpiryDate).day ?? 0

        if daysUntilExpiry <= 0 {
            return .expired
        } else if daysUntilExpiry <= expiryWarningDays {
            return .expiringSoon(daysRemaining: daysUntilExpiry)
        } else {
            return .valid(daysRemaining: daysUntilExpiry)
        }
    }

    /// Certificate validity status
    enum CertificateStatus {
        case valid(daysRemaining: Int)
        case expiringSoon(daysRemaining: Int)
        case expired

        var isValid: Bool {
            switch self {
            case .valid, .expiringSoon:
                return true
            case .expired:
                return false
            }
        }

        var description: String {
            switch self {
            case .valid(let days):
                return "Valid (\(days) days remaining)"
            case .expiringSoon(let days):
                return "Expiring soon (\(days) days remaining)"
            case .expired:
                return "Expired"
            }
        }
    }

    /// Load pinned certificates from the app bundle
    private func loadPinnedCertificates() {
        // Try to load .cer file
        if let certPath = Bundle.main.path(forResource: "api.d23.ai", ofType: "cer"),
           let certData = try? Data(contentsOf: URL(fileURLWithPath: certPath)) {
            pinnedCertificates.append(certData)
            print("[SSLPinning] Loaded certificate from bundle")
        }

        // Try to load .der file as fallback
        if let derPath = Bundle.main.path(forResource: "api.d23.ai", ofType: "der"),
           let derData = try? Data(contentsOf: URL(fileURLWithPath: derPath)) {
            pinnedCertificates.append(derData)
            print("[SSLPinning] Loaded DER certificate from bundle")
        }

        // Fallback: use embedded base64 cert if bundle lookup fails
        if pinnedCertificates.isEmpty, let embeddedData = Data(base64Encoded: Self.embeddedCertBase64) {
            pinnedCertificates.append(embeddedData)
            print("[SSLPinning] Loaded embedded certificate")
        }

        if pinnedCertificates.isEmpty {
            print("[SSLPinning] WARNING: No pinned certificates found in bundle")
        }
    }

    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        // Only handle server trust challenges
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust else {
            completionHandler(.performDefaultHandling, nil)
            return
        }

        // Only pin for our specific host
        guard challenge.protectionSpace.host == pinnedHost else {
            completionHandler(.performDefaultHandling, nil)
            return
        }

        guard let serverTrust = challenge.protectionSpace.serverTrust else {
            print("[SSLPinning] No server trust available")
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        // If no pinned certificates, check configuration
        if pinnedCertificates.isEmpty {
            // Only allow bypass if SSL pinning is not enforced (development only)
            if !AppConfig.shared.enforceSSLPinning {
                AppConfig.shared.debugLog("No pinned certificates - allowing connection (SSL pinning not enforced)")
                completionHandler(.useCredential, URLCredential(trust: serverTrust))
                return
            } else {
                print("[SSLPinning] No pinned certificates - rejecting connection (SSL pinning enforced)")
                completionHandler(.cancelAuthenticationChallenge, nil)
                return
            }
        }

        // Evaluate the server trust
        var error: CFError?
        let policy = SecPolicyCreateSSL(true, pinnedHost as CFString)
        SecTrustSetPolicies(serverTrust, policy)

        guard SecTrustEvaluateWithError(serverTrust, &error) else {
            print("[SSLPinning] Trust evaluation failed: \(error?.localizedDescription ?? "unknown")")
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        // Get server certificate
        guard let certificates = SecTrustCopyCertificateChain(serverTrust) as? [SecCertificate],
              let serverCertificate = certificates.first else {
            print("[SSLPinning] Could not get server certificate")
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        let serverCertData = SecCertificateCopyData(serverCertificate) as Data

        // Compare with pinned certificates
        for pinnedCertData in pinnedCertificates {
            if serverCertData == pinnedCertData {
                print("[SSLPinning] Certificate pinning successful")
                completionHandler(.useCredential, URLCredential(trust: serverTrust))
                return
            }
        }

        // Also check public key pinning as fallback
        if validatePublicKey(serverTrust: serverTrust) {
            print("[SSLPinning] Public key pinning successful")
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
            return
        }

        print("[SSLPinning] Certificate pinning FAILED - certificate mismatch")
        completionHandler(.cancelAuthenticationChallenge, nil)
    }

    /// Validate public key as a fallback pinning method
    /// Uses SHA-256 hash of the public key for comparison
    private func validatePublicKey(serverTrust: SecTrust) -> Bool {
        guard let certificates = SecTrustCopyCertificateChain(serverTrust) as? [SecCertificate],
              let serverCertificate = certificates.first,
              let serverPublicKey = SecCertificateCopyKey(serverCertificate) else {
            return false
        }

        // Get the public key data
        guard let serverPublicKeyData = SecKeyCopyExternalRepresentation(serverPublicKey, nil) as Data? else {
            return false
        }

        // Hash the server's public key
        let serverKeyHash = sha256Hash(data: serverPublicKeyData)

        // Compare with pinned public key hashes
        for pinnedHash in Self.pinnedPublicKeyHashes {
            if serverKeyHash == pinnedHash {
                return true
            }
        }

        return false
    }

    /// Compute SHA-256 hash of data
    private func sha256Hash(data: Data) -> String {
        var hash = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withUnsafeBytes {
            _ = CC_SHA256($0.baseAddress, CC_LONG(data.count), &hash)
        }
        return hash.map { String(format: "%02x", $0) }.joined()
    }

    /// Pre-computed SHA-256 hashes of pinned public keys
    /// To generate: extract public key from cert and hash it
    /// openssl x509 -in cert.pem -pubkey -noout | openssl pkey -pubin -outform DER | openssl dgst -sha256
    private static let pinnedPublicKeyHashes: [String] = [
        // Add your public key hash here when available
        // "abc123..."
    ]

    private static let embeddedCertBase64 = """
MIIFfjCCBGagAwIBAgISBSbq96gYWo0PxFx07WlhDTd/MA0GCSqGSIb3DQEBCwUAMDMxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MQwwCgYDVQQDEwNSMTIwHhcNMjUxMjA0MDQzMjU0WhcNMjYwMzA0MDQzMjUzWjATMREwDwYDVQQDDAgqLmQyMy5haTCCAaIwDQYJKoZIhvcNAQEBBQADggGPADCCAYoCggGBAI9xXiAYpwHZYwFbQELO3iE+ZnfN7iruvnRXwiaG2lsxuZ1LBh6YeDUvYaE7B2f8MlfFdIL/p3eRwCZsGGn4aSfSln1yZmEsFTw9v80HcWIHiDTdbhzF06UmKVD/EOW0q6v371X+Da8SRUl6cIwiVOAVKoJMScFrhKSFx4J/azK3zNb2oeJ0nnJD6KdY79YSKAgRGOsySHpW2mYcsBHErumA1lA/PBPOrsnknRR4zLk76Vb6ybUDHhqTrV2y2c6lXXG6irPUR6Ey04fmEeF9lY9rKjrsU5Xhmu7BdQrhQK+xfbzBGu9ap7BPlP64pEE8pwPBQ89UTxmZUCB0pRDcbL8ovH3zaDfzXOzpZCdsk6jC8+5MS67/Z/KJiQmfifEVKnbENmylGmD8Mv22Amt8fTtZrSPb7R2kfQce2fq7j/IyPN9xDS6htvxG0lf6i0vmjPp5WJZAQ6U72AwRpsuYHBop3+aIjM0wMqRilpnLdCg/yOfo9MqVMER6LiP5s199BQIDAQABo4ICKjCCAiYwDgYDVR0PAQH/BAQDAgWgMB0GA1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjAMBgNVHRMBAf8EAjAAMB0GA1UdDgQWBBQ9viN0bxNUojPzoJRBDM0sVnp8uDAfBgNVHSMEGDAWgBQAtSnyLY5vMeibTK14Pvrc6QzR0jAzBggrBgEFBQcBAQQnMCUwIwYIKwYBBQUHMAKGF2h0dHA6Ly9yMTIuaS5sZW5jci5vcmcvMBsGA1UdEQQUMBKCCCouZDIzLmFpggZkMjMuYWkwEwYDVR0gBAwwCjAIBgZngQwBAgEwLwYDVR0fBCgwJjAkoCKgIIYeaHR0cDovL3IxMi5jLmxlbmNyLm9yZy8xMjguY3JsMIIBDQYKKwYBBAHWeQIEAgSB/gSB+wD5AHYAyzj3FYl8hKFEX1vB3fvJbvKaWc1HCmkFhbDLFMMUWOcAAAGa59gCMwAABAMARzBFAiBrS4WjZgAWt+4SHueCEw1o+AKvHLa0V2W1ykKiB7bf1gIhANgQSmoxjK01EoDZleFmDHZ7sI/Uv83p1B4HXhh1U4G3AH8A4yON8o2iiOCq4Kzw+pDJhfC2v/XSpSewAfwcRFjEtugAAAGa59gF0wAIAAAFACfGn5IEAwBIMEYCIQDx02WfeFap8Nd64YsFhzuZmBB8UVhESMtjRoJ3LLX9zQIhANrf3Iom1s9awy2rTWFzOiEdenTOkLd+hVWd3NQPHGU7MA0GCSqGSIb3DQEBCwUAA4IBAQBYcmAPml96WlTkhn/Xl3+7MngX6+6zZyZ+H5kQxeY828ScYsZur6nrCO2V7S4d5gmiPAw0eA1LZ5J+/KEkc9C/uV4g4Ux2DKpn2zMfXNIe0bueZZhiE+MwC77bIlm9TY/nQYeaNk/hGGzcZ7FqR8g5NPZVb1NJbQRZzha4eePkN8EZ2EbqGXs9UbjlIv22Hzj3xPlK5MdHEd2w2/sNYC9QZK9w35TFtfTnCiJLQmmMPVk3lI19mO30GDIyafr1qtr04BNbeLD0RPKVYHFKCobQ1P0nU9rROZeQLaUpzPjVq665kuJhwgqPM8lnPxi3D4gn6n/fOvCiufwEI3WxqUCB
"""
}

/// Extension to create a pinned URLSession
extension URLSession {
    /// Create a URLSession with SSL pinning enabled
    static func pinnedSession(timeoutInterval: TimeInterval = 30) -> URLSession {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = timeoutInterval
        config.timeoutIntervalForResource = 60

        let delegate = SSLPinningDelegate()
        return URLSession(configuration: config, delegate: delegate, delegateQueue: nil)
    }
}
