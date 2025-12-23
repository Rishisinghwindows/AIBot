import SwiftUI
import Combine

/// User profile view with editing capabilities
struct ProfileView: View {
    @StateObject private var viewModel = ProfileViewModel()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                // Profile header
                Section {
                    HStack {
                        AsyncImage(url: URL(string: viewModel.photoUrl)) { image in
                            image
                                .resizable()
                                .scaledToFill()
                        } placeholder: {
                            Circle()
                                .fill(LinearGradient(
                                    colors: [.purple, .pink],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ))
                                .overlay(
                                    Text(viewModel.displayName.prefix(1).uppercased())
                                        .font(.title)
                                        .fontWeight(.bold)
                                        .foregroundColor(.white)
                                )
                        }
                        .frame(width: 80, height: 80)
                        .clipShape(Circle())

                        VStack(alignment: .leading, spacing: 4) {
                            Text(viewModel.displayName.isEmpty ? "Set your name" : viewModel.displayName)
                                .font(.title2)
                                .fontWeight(.semibold)
                            Text(viewModel.email)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        .padding(.leading, 8)
                    }
                    .padding(.vertical, 8)
                }

                // Basic Info
                Section("Basic Information") {
                    TextField("Display Name", text: $viewModel.displayName)
                    TextField("Bio", text: $viewModel.bio, axis: .vertical)
                        .lineLimit(3...5)
                }

                // Preferences
                Section("Preferences") {
                    Picker("Language", selection: $viewModel.language) {
                        Text("English").tag("en")
                        Text("Hindi").tag("hi")
                        Text("Tamil").tag("ta")
                        Text("Telugu").tag("te")
                        Text("Marathi").tag("mr")
                    }

                    Picker("AI Response Style", selection: $viewModel.aiTone) {
                        Text("Concise").tag("concise")
                        Text("Balanced").tag("balanced")
                        Text("Detailed").tag("detailed")
                        Text("Friendly").tag("friendly")
                        Text("Professional").tag("professional")
                    }
                }

                // Birth Details
                Section {
                    TextField("Full Name", text: $viewModel.fullName)
                    TextField("Birth Date (DD-MM-YYYY)", text: $viewModel.birthDate)
                    TextField("Birth Time (HH:MM)", text: $viewModel.birthTime)
                    TextField("Birth Place", text: $viewModel.birthPlace)

                    if let zodiac = viewModel.zodiacSign, !zodiac.isEmpty {
                        HStack {
                            Text("Sun Sign")
                            Spacer()
                            Text(zodiac)
                                .foregroundColor(.secondary)
                        }
                    }
                    if let moon = viewModel.moonSign, !moon.isEmpty {
                        HStack {
                            Text("Moon Sign")
                            Spacer()
                            Text(moon)
                                .foregroundColor(.secondary)
                        }
                    }
                    if let nakshatra = viewModel.nakshatra, !nakshatra.isEmpty {
                        HStack {
                            Text("Nakshatra")
                            Spacer()
                            Text(nakshatra)
                                .foregroundColor(.secondary)
                        }
                    }
                } header: {
                    Text("Birth Details")
                } footer: {
                    Text("Used for astrology features like horoscope and birth chart")
                }
            }
            .navigationTitle("Profile")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        Task {
                            await viewModel.save()
                            if viewModel.saveSuccess {
                                dismiss()
                            }
                        }
                    } label: {
                        if viewModel.isSaving {
                            ProgressView()
                        } else {
                            Text("Save")
                        }
                    }
                    .disabled(viewModel.isSaving)
                }
            }
            .alert("Error", isPresented: .constant(viewModel.error != nil)) {
                Button("OK") { viewModel.error = nil }
            } message: {
                Text(viewModel.error ?? "")
            }
            .task {
                await viewModel.loadProfile()
                await viewModel.loadBirthDetails()
            }
        }
    }
}

/// ViewModel for ProfileView
@MainActor
class ProfileViewModel: ObservableObject {
    @Published var email: String = ""
    @Published var displayName: String = ""
    @Published var photoUrl: String = ""
    @Published var bio: String = ""
    @Published var language: String = "en"
    @Published var aiTone: String = "balanced"

    @Published var fullName: String = ""
    @Published var birthDate: String = ""
    @Published var birthTime: String = ""
    @Published var birthPlace: String = ""
    @Published var zodiacSign: String?
    @Published var moonSign: String?
    @Published var nakshatra: String?

    @Published var isLoading = false
    @Published var isSaving = false
    @Published var saveSuccess = false
    @Published var error: String?

    func loadProfile() async {
        isLoading = true
        do {
            let profile = try await APIClient.shared.getProfile()
            email = profile.email
            displayName = profile.displayName ?? ""
            photoUrl = profile.photoUrl ?? ""
            bio = profile.bio ?? ""
            if let prefs = profile.preferences {
                language = prefs["language"] ?? "en"
                aiTone = prefs["ai_tone"] ?? "balanced"
            }
        } catch {
            self.error = "Failed to load profile"
        }
        isLoading = false
    }

    func loadBirthDetails() async {
        do {
            if let details = try await APIClient.shared.getBirthDetails() {
                fullName = details.fullName ?? ""
                birthDate = details.birthDate ?? ""
                birthTime = details.birthTime ?? ""
                birthPlace = details.birthPlace ?? ""
                zodiacSign = details.zodiacSign
                moonSign = details.moonSign
                nakshatra = details.nakshatra
            }
        } catch {
            // Birth details may not exist yet, that's ok
        }
    }

    func save() async {
        isSaving = true
        saveSuccess = false

        do {
            // Update profile
            let profileRequest = ProfileUpdateRequest(
                displayName: displayName.isEmpty ? nil : displayName,
                bio: bio.isEmpty ? nil : bio,
                photoUrl: nil,
                preferences: ["language": language, "ai_tone": aiTone]
            )
            _ = try await APIClient.shared.updateProfile(profileRequest)

            // Update birth details
            let birthRequest = BirthDetailsRequest(
                fullName: fullName.isEmpty ? nil : fullName,
                birthDate: birthDate.isEmpty ? nil : birthDate,
                birthTime: birthTime.isEmpty ? nil : birthTime,
                birthPlace: birthPlace.isEmpty ? nil : birthPlace,
                zodiacSign: nil
            )
            let birthResponse = try await APIClient.shared.saveBirthDetails(birthRequest)
            zodiacSign = birthResponse.zodiacSign
            moonSign = birthResponse.moonSign
            nakshatra = birthResponse.nakshatra

            saveSuccess = true
        } catch {
            self.error = "Failed to save profile"
        }

        isSaving = false
    }
}

#Preview {
    ProfileView()
}
