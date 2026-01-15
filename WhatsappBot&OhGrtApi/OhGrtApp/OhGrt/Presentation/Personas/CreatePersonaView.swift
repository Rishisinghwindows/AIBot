import SwiftUI
import Combine

/// Multi-step wizard for creating a persona
struct CreatePersonaView: View {
    @StateObject private var viewModel = CreatePersonaViewModel()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Progress indicator
                ProgressView(value: Double(viewModel.currentStep), total: 4)
                    .tint(.purple)
                    .padding(.horizontal)
                    .padding(.top, 8)

                // Step content
                TabView(selection: $viewModel.currentStep) {
                    handleStep.tag(0)
                    basicInfoStep.tag(1)
                    personalityStep.tag(2)
                    professionalStep.tag(3)
                }
                .tabViewStyle(.page(indexDisplayMode: .never))
                .animation(.easeInOut, value: viewModel.currentStep)

                // Navigation buttons
                navigationButtons
                    .padding()
            }
            .navigationTitle(stepTitle)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .alert("Error", isPresented: .constant(viewModel.error != nil)) {
                Button("OK") { viewModel.error = nil }
            } message: {
                Text(viewModel.error ?? "")
            }
        }
    }

    private var stepTitle: String {
        switch viewModel.currentStep {
        case 0: return "Choose Handle"
        case 1: return "Basic Info"
        case 2: return "Personality"
        case 3: return "Professional"
        default: return "Create Persona"
        }
    }

    // MARK: - Step 0: Handle Selection

    private var handleStep: some View {
        ScrollView {
            VStack(spacing: 24) {
                Image(systemName: "at")
                    .font(.system(size: 50))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.purple, .pink],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )

                Text("Choose Your Handle")
                    .font(.title2)
                    .fontWeight(.bold)

                Text("This will be your unique username.\nPeople can find you at ohgrt.com/p/yourhandle")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)

                HStack {
                    Text("@")
                        .font(.title2)
                        .foregroundColor(.secondary)

                    TextField("handle", text: $viewModel.handle)
                        .font(.title2)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .onChange(of: viewModel.handle) { _, newValue in
                            viewModel.handle = newValue.lowercased().replacingOccurrences(of: " ", with: "")
                            viewModel.handleAvailable = nil
                        }
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)
                .padding(.horizontal)

                // Handle availability check
                if viewModel.isCheckingHandle {
                    HStack {
                        ProgressView()
                        Text("Checking availability...")
                            .foregroundColor(.secondary)
                    }
                } else if let available = viewModel.handleAvailable {
                    HStack {
                        Image(systemName: available ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(available ? .green : .red)
                        Text(available ? "Handle is available!" : "Handle is already taken")
                            .foregroundColor(available ? .green : .red)
                    }
                }

                Button("Check Availability") {
                    Task { await viewModel.checkHandle() }
                }
                .disabled(viewModel.handle.count < 3)
            }
            .padding(.top, 40)
        }
    }

    // MARK: - Step 1: Basic Info

    private var basicInfoStep: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Avatar placeholder
                Circle()
                    .fill(LinearGradient(
                        colors: [.purple, .pink],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ))
                    .frame(width: 100, height: 100)
                    .overlay(
                        Text(viewModel.displayName.isEmpty ? "?" : viewModel.displayName.prefix(1).uppercased())
                            .font(.largeTitle)
                            .foregroundColor(.white)
                    )

                VStack(alignment: .leading, spacing: 8) {
                    Text("Display Name")
                        .font(.headline)
                    TextField("Your Name", text: $viewModel.displayName)
                        .textFieldStyle(.roundedBorder)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Tagline")
                        .font(.headline)
                    TextField("A short description of yourself", text: $viewModel.tagline)
                        .textFieldStyle(.roundedBorder)
                    Text("This appears on your public profile")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal)

                Toggle("Make profile public", isOn: $viewModel.isPublic)
                    .padding(.horizontal)
            }
            .padding(.top, 40)
        }
    }

    // MARK: - Step 2: Personality

    private var personalityStep: some View {
        ScrollView {
            VStack(spacing: 24) {
                Text("Tell us about your personality")
                    .font(.headline)
                    .padding(.top, 16)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Communication Style")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    Picker("Style", selection: $viewModel.communicationStyle) {
                        Text("Formal").tag("formal")
                        Text("Casual").tag("casual")
                        Text("Professional").tag("professional")
                        Text("Friendly").tag("friendly")
                    }
                    .pickerStyle(.segmented)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Primary Expertise Area")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    TextField("e.g., Software Development, Marketing", text: $viewModel.expertiseArea)
                        .textFieldStyle(.roundedBorder)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Topics You're Knowledgeable About")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    TextField("Comma-separated topics", text: $viewModel.topics)
                        .textFieldStyle(.roundedBorder)
                    Text("e.g., iOS development, Swift, SwiftUI")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Response Length")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    Picker("Length", selection: $viewModel.responseLength) {
                        Text("Brief").tag("brief")
                        Text("Moderate").tag("moderate")
                        Text("Detailed").tag("detailed")
                    }
                    .pickerStyle(.segmented)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Use Humor?")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    Picker("Humor", selection: $viewModel.useHumor) {
                        Text("Never").tag("never")
                        Text("Sometimes").tag("sometimes")
                        Text("Often").tag("often")
                    }
                    .pickerStyle(.segmented)
                }
                .padding(.horizontal)
            }
        }
    }

    // MARK: - Step 3: Professional

    private var professionalStep: some View {
        ScrollView {
            VStack(spacing: 24) {
                Text("Professional Background")
                    .font(.headline)
                    .padding(.top, 16)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Job Title / Role")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    TextField("e.g., Senior Software Engineer", text: $viewModel.jobTitle)
                        .textFieldStyle(.roundedBorder)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Industry")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    TextField("e.g., Technology, Healthcare", text: $viewModel.industry)
                        .textFieldStyle(.roundedBorder)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Years of Experience")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    Stepper("\(viewModel.yearsExperience) years", value: $viewModel.yearsExperience, in: 0...50)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Key Skills")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    TextField("Comma-separated skills", text: $viewModel.skills)
                        .textFieldStyle(.roundedBorder)
                }
                .padding(.horizontal)

                VStack(alignment: .leading, spacing: 8) {
                    Text("Notable Achievements")
                        .font(.subheadline)
                        .fontWeight(.medium)
                    TextField("Brief achievements or credentials", text: $viewModel.achievements, axis: .vertical)
                        .textFieldStyle(.roundedBorder)
                        .lineLimit(3...5)
                }
                .padding(.horizontal)
            }
        }
    }

    // MARK: - Navigation Buttons

    private var navigationButtons: some View {
        HStack {
            if viewModel.currentStep > 0 {
                Button {
                    withAnimation {
                        viewModel.currentStep -= 1
                    }
                } label: {
                    HStack {
                        Image(systemName: "chevron.left")
                        Text("Back")
                    }
                    .foregroundColor(.primary)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(Color(.systemGray5))
                    .cornerRadius(12)
                }
            }

            Spacer()

            if viewModel.currentStep < 3 {
                Button {
                    withAnimation {
                        viewModel.currentStep += 1
                    }
                } label: {
                    HStack {
                        Text("Next")
                        Image(systemName: "chevron.right")
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(
                        LinearGradient(
                            colors: [.purple, .pink],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(12)
                }
                .disabled(!viewModel.canProceed)
            } else {
                Button {
                    Task {
                        if await viewModel.createPersona() {
                            dismiss()
                        }
                    }
                } label: {
                    HStack {
                        if viewModel.isCreating {
                            ProgressView()
                                .tint(.white)
                        } else {
                            Text("Create Persona")
                            Image(systemName: "checkmark")
                        }
                    }
                    .foregroundColor(.white)
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(
                        LinearGradient(
                            colors: [.purple, .pink],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(12)
                }
                .disabled(viewModel.isCreating || !viewModel.canCreate)
            }
        }
    }
}

/// ViewModel for CreatePersonaView
@MainActor
class CreatePersonaViewModel: ObservableObject {
    @Published var currentStep = 0

    // Step 0: Handle
    @Published var handle = ""
    @Published var handleAvailable: Bool?
    @Published var isCheckingHandle = false

    // Step 1: Basic Info
    @Published var displayName = ""
    @Published var tagline = ""
    @Published var isPublic = true

    // Step 2: Personality
    @Published var communicationStyle = "professional"
    @Published var expertiseArea = ""
    @Published var topics = ""
    @Published var responseLength = "moderate"
    @Published var useHumor = "sometimes"

    // Step 3: Professional
    @Published var jobTitle = ""
    @Published var industry = ""
    @Published var yearsExperience = 5
    @Published var skills = ""
    @Published var achievements = ""

    // State
    @Published var isCreating = false
    @Published var error: String?

    var canProceed: Bool {
        switch currentStep {
        case 0:
            return handle.count >= 3 && handleAvailable == true
        case 1:
            return !displayName.isEmpty
        default:
            return true
        }
    }

    var canCreate: Bool {
        return handle.count >= 3 && !displayName.isEmpty
    }

    func checkHandle() async {
        guard handle.count >= 3 else { return }

        isCheckingHandle = true
        do {
            let response = try await APIClient.shared.checkHandle(handle)
            handleAvailable = response.available
        } catch {
            self.error = "Failed to check handle"
        }
        isCheckingHandle = false
    }

    func createPersona() async -> Bool {
        isCreating = true

        let topicsArray = topics.split(separator: ",").map { String($0.trimmingCharacters(in: .whitespaces)) }
        let skillsArray = skills.split(separator: ",").map { String($0.trimmingCharacters(in: .whitespaces)) }

        let personality = PersonalityData(
            communicationStyle: communicationStyle,
            expertiseArea: expertiseArea.isEmpty ? nil : expertiseArea,
            topics: topicsArray.isEmpty ? nil : topicsArray,
            outsideExpertiseResponse: nil,
            responseLength: responseLength,
            useHumor: useHumor
        )

        let professional = ProfessionalData(
            jobTitle: jobTitle.isEmpty ? nil : jobTitle,
            industry: industry.isEmpty ? nil : industry,
            yearsExperience: yearsExperience,
            skills: skillsArray.isEmpty ? nil : skillsArray,
            achievements: achievements.isEmpty ? nil : achievements,
            problemsSolved: nil
        )

        let request = PersonaCreateRequest(
            handle: handle,
            displayName: displayName,
            tagline: tagline.isEmpty ? nil : tagline,
            avatarUrl: nil,
            personality: personality,
            professional: professional,
            isPublic: isPublic
        )

        do {
            _ = try await APIClient.shared.createPersona(request)
            isCreating = false
            return true
        } catch {
            self.error = "Failed to create persona"
            isCreating = false
            return false
        }
    }
}

#Preview {
    CreatePersonaView()
}
