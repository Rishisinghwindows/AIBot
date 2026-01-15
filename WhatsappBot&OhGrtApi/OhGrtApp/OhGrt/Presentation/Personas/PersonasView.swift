import SwiftUI
import Combine

/// View to display all user's personas
struct PersonasView: View {
    @StateObject private var viewModel = PersonasViewModel()
    @State private var showingCreatePersona = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if viewModel.personas.isEmpty {
                    emptyStateView
                } else {
                    personasList
                }
            }
            .navigationTitle("My Personas")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingCreatePersona = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingCreatePersona) {
                CreatePersonaView()
                    .onDisappear {
                        Task { await viewModel.loadPersonas() }
                    }
            }
            .alert("Error", isPresented: .constant(viewModel.error != nil)) {
                Button("OK") { viewModel.error = nil }
            } message: {
                Text(viewModel.error ?? "")
            }
            .task {
                await viewModel.loadPersonas()
            }
        }
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.2.circle")
                .font(.system(size: 60))
                .foregroundColor(.secondary)

            Text("No Personas Yet")
                .font(.title2)
                .fontWeight(.semibold)

            Text("Create an AI persona that represents you.\nShare the link and let others chat with your AI.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            Button {
                showingCreatePersona = true
            } label: {
                Text("Create Persona")
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 24)
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
            .padding(.top, 8)
        }
    }

    private var personasList: some View {
        List {
            ForEach(viewModel.personas) { persona in
                PersonaRow(persona: persona, viewModel: viewModel)
            }
            .onDelete { indexSet in
                Task {
                    for index in indexSet {
                        await viewModel.deletePersona(viewModel.personas[index])
                    }
                }
            }
        }
        .refreshable {
            await viewModel.loadPersonas()
        }
    }
}

/// Row for displaying a single persona
struct PersonaRow: View {
    let persona: PersonaResponse
    @ObservedObject var viewModel: PersonasViewModel
    @State private var showingShareSheet = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Avatar
                AsyncImage(url: URL(string: persona.avatarUrl ?? "")) { image in
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
                            Text(persona.displayName.prefix(1).uppercased())
                                .font(.headline)
                                .foregroundColor(.white)
                        )
                }
                .frame(width: 50, height: 50)
                .clipShape(Circle())

                VStack(alignment: .leading, spacing: 2) {
                    Text(persona.displayName)
                        .font(.headline)

                    Text("@\(persona.handle)")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                // Status badge
                if persona.isPublic {
                    Text("Public")
                        .font(.caption)
                        .foregroundColor(.green)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.green.opacity(0.1))
                        .cornerRadius(4)
                } else {
                    Text("Private")
                        .font(.caption)
                        .foregroundColor(.orange)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.orange.opacity(0.1))
                        .cornerRadius(4)
                }
            }

            if let tagline = persona.tagline, !tagline.isEmpty {
                Text(tagline)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            HStack {
                Label("\(persona.totalChats) chats", systemImage: "message")
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                // Share button
                Button {
                    sharePersona()
                } label: {
                    Label("Share", systemImage: "square.and.arrow.up")
                        .font(.caption)
                }
                .buttonStyle(.bordered)
            }
            .padding(.top, 4)
        }
        .padding(.vertical, 8)
    }

    private func sharePersona() {
        let baseURL = "https://ohgrt.com/p/\(persona.handle)"
        let activityVC = UIActivityViewController(
            activityItems: [baseURL],
            applicationActivities: nil
        )

        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let window = windowScene.windows.first,
           let rootVC = window.rootViewController {
            rootVC.present(activityVC, animated: true)
        }
    }
}

/// ViewModel for PersonasView
@MainActor
class PersonasViewModel: ObservableObject {
    @Published var personas: [PersonaResponse] = []
    @Published var isLoading = false
    @Published var error: String?

    func loadPersonas() async {
        isLoading = true
        do {
            personas = try await APIClient.shared.getPersonas()
        } catch {
            self.error = "Failed to load personas"
        }
        isLoading = false
    }

    func deletePersona(_ persona: PersonaResponse) async {
        do {
            try await APIClient.shared.deletePersona(id: persona.id)
            personas.removeAll { $0.id == persona.id }
        } catch {
            self.error = "Failed to delete persona"
        }
    }
}

#Preview {
    PersonasView()
}
