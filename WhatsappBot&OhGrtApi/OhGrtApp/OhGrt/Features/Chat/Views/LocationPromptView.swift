import SwiftUI
import CoreLocation
import Combine

/// View for prompting user to share their location
struct LocationPromptView: View {
    let onShareLocation: (CLLocationCoordinate2D, Double?) -> Void
    let onDismiss: () -> Void

    @StateObject private var locationManager = LocationManager()
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        HStack(spacing: 12) {
            // Location icon
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.purple, .pink],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 40, height: 40)

                Image(systemName: "location.fill")
                    .font(.system(size: 18))
                    .foregroundColor(.white)
            }

            // Text content
            VStack(alignment: .leading, spacing: 2) {
                Text("Share your location")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.white)

                Text(errorMessage ?? "Help me find nearby places for you")
                    .font(.caption)
                    .foregroundColor(errorMessage != nil ? .red : .gray)
                    .lineLimit(1)
            }

            Spacer()

            // Action buttons
            HStack(spacing: 8) {
                Button(action: onDismiss) {
                    Image(systemName: "xmark")
                        .font(.system(size: 14))
                        .foregroundColor(.gray)
                        .frame(width: 32, height: 32)
                        .background(Color.gray.opacity(0.2))
                        .clipShape(Circle())
                }

                Button(action: requestLocation) {
                    HStack(spacing: 4) {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "location.fill")
                                .font(.system(size: 12))
                        }
                        Text(isLoading ? "Getting..." : "Share")
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(
                        LinearGradient(
                            colors: [.purple, .pink],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(Capsule())
                }
                .disabled(isLoading)
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color.purple.opacity(0.1))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color.purple.opacity(0.2), lineWidth: 1)
                )
        )
    }

    private func requestLocation() {
        isLoading = true
        errorMessage = nil

        locationManager.requestLocation { result in
            isLoading = false

            switch result {
            case .success(let location):
                onShareLocation(location.coordinate, location.horizontalAccuracy)
            case .failure(let error):
                switch error {
                case .denied:
                    errorMessage = "Location access denied. Enable in Settings."
                case .unavailable:
                    errorMessage = "Location unavailable."
                case .timeout:
                    errorMessage = "Location request timed out."
                case .unknown:
                    errorMessage = "Failed to get location."
                }
            }
        }
    }
}

// MARK: - Location Manager

enum LocationError: Error {
    case denied
    case unavailable
    case timeout
    case unknown
}

class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var completion: ((Result<CLLocation, LocationError>) -> Void)?
    private var timeoutTimer: Timer?
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
    }

    func requestLocation(completion: @escaping (Result<CLLocation, LocationError>) -> Void) {
        self.completion = completion

        // Set timeout
        timeoutTimer = Timer.scheduledTimer(withTimeInterval: 15, repeats: false) { [weak self] _ in
            self?.completion?(.failure(.timeout))
            self?.completion = nil
        }

        switch manager.authorizationStatus {
        case .notDetermined:
            manager.requestWhenInUseAuthorization()
        case .authorizedWhenInUse, .authorizedAlways:
            manager.requestLocation()
        case .denied, .restricted:
            completion(.failure(.denied))
            self.completion = nil
        @unknown default:
            completion(.failure(.unknown))
            self.completion = nil
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        timeoutTimer?.invalidate()
        if let location = locations.first {
            completion?(.success(location))
        } else {
            completion?(.failure(.unavailable))
        }
        completion = nil
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        timeoutTimer?.invalidate()
        if let clError = error as? CLError {
            switch clError.code {
            case .denied:
                completion?(.failure(.denied))
            case .locationUnknown:
                completion?(.failure(.unavailable))
            default:
                completion?(.failure(.unknown))
            }
        } else {
            completion?(.failure(.unknown))
        }
        completion = nil
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus
        switch manager.authorizationStatus {
        case .authorizedWhenInUse, .authorizedAlways:
            manager.requestLocation()
        case .denied, .restricted:
            completion?(.failure(.denied))
            completion = nil
        default:
            break
        }
    }
}

#Preview {
    LocationPromptView(
        onShareLocation: { _, _ in },
        onDismiss: { }
    )
    .padding()
    .background(Color.black)
}
