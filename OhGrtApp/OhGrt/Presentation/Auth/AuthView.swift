import SwiftUI

/// Authentication view with Google Sign-In
struct AuthView: View {
    @ObservedObject var viewModel: AuthViewModel
    @ObservedObject private var theme = ThemeManager.shared

    @State private var logoScale: CGFloat = 0.8
    @State private var logoOpacity: Double = 0
    @State private var contentOpacity: Double = 0
    @State private var buttonScale: CGFloat = 0.9

    var body: some View {
        ZStack {
            // Background
            AuthBackground()

            VStack(spacing: 32) {
                Spacer()

                // Logo and branding
                VStack(spacing: 16) {
                    // Animated logo
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [theme.primaryColor, theme.secondaryColor],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 100, height: 100)
                            .shadow(color: theme.primaryColor.opacity(0.4), radius: 20, y: 10)

                        VStack(spacing: 0) {
                            Text("D23")
                                .font(.system(size: 28, weight: .black, design: .rounded))
                                .foregroundColor(.white)
                            Text("AI")
                                .font(.system(size: 12, weight: .bold, design: .rounded))
                                .foregroundColor(.white.opacity(0.9))
                        }
                    }
                    .scaleEffect(logoScale)
                    .opacity(logoOpacity)

                    VStack(spacing: 8) {
                        Text("Welcome to D23 AI")
                            .font(.title)
                            .fontWeight(.bold)

                        Text("Your intelligent assistant awaits")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
                .opacity(contentOpacity)

                Spacer()

                // Sign in buttons
                VStack(spacing: 16) {
                    // Google Sign-In button
                    Button(action: {
                        viewModel.signInWithGoogle()
                    }) {
                        HStack(spacing: 12) {
                            Image("google_logo")
                                .resizable()
                                .scaledToFit()
                                .frame(width: 20, height: 20)

                            Text("Continue with Google")
                                .font(.headline)
                                .fontWeight(.semibold)
                        }
                        .foregroundColor(.primary)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(Color(.systemBackground))
                        .cornerRadius(16)
                        .shadow(color: .black.opacity(0.1), radius: 10, y: 5)
                    }
                    .disabled(viewModel.isLoading)
                    .scaleEffect(buttonScale)

                    // Apple Sign-In button (placeholder)
                    Button(action: {
                        // TODO: Implement Apple Sign-In
                    }) {
                        HStack(spacing: 12) {
                            Image(systemName: "apple.logo")
                                .font(.system(size: 20, weight: .medium))

                            Text("Continue with Apple")
                                .font(.headline)
                                .fontWeight(.semibold)
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(Color.black)
                        .cornerRadius(16)
                    }
                    .disabled(viewModel.isLoading)
                    .scaleEffect(buttonScale)

                    // Loading indicator
                    if viewModel.isLoading {
                        ProgressView()
                            .scaleEffect(1.2)
                            .padding(.top, 8)
                    }
                }
                .padding(.horizontal, 32)
                .opacity(contentOpacity)

                // Terms and privacy
                VStack(spacing: 8) {
                    Text("By continuing, you agree to our")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    HStack(spacing: 4) {
                        Button("Terms of Service") {
                            // Open terms
                        }
                        .font(.caption)
                        .foregroundColor(theme.primaryColor)

                        Text("and")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Button("Privacy Policy") {
                            // Open privacy
                        }
                        .font(.caption)
                        .foregroundColor(theme.primaryColor)
                    }
                }
                .opacity(contentOpacity)
                .padding(.bottom, 32)
            }
        }
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK") {
                viewModel.clearError()
            }
        } message: {
            Text(viewModel.error ?? "An error occurred")
        }
        .onAppear {
            startAnimations()
        }
    }

    private func startAnimations() {
        withAnimation(.spring(response: 0.7, dampingFraction: 0.7).delay(0.1)) {
            logoScale = 1.0
            logoOpacity = 1.0
        }

        withAnimation(.easeOut(duration: 0.5).delay(0.3)) {
            contentOpacity = 1.0
        }

        withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(0.5)) {
            buttonScale = 1.0
        }
    }
}

/// Animated background for auth screen
private struct AuthBackground: View {
    @ObservedObject private var theme = ThemeManager.shared
    @State private var animateGradient = false

    var body: some View {
        ZStack {
            Color(.systemBackground)
                .ignoresSafeArea()

            GeometryReader { geo in
                ZStack {
                    // Top gradient orb
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [theme.primaryColor.opacity(0.2), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 200
                            )
                        )
                        .frame(width: 400, height: 400)
                        .offset(
                            x: animateGradient ? -80 : -120,
                            y: animateGradient ? -50 : -100
                        )
                        .blur(radius: 60)

                    // Bottom gradient orb
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [theme.secondaryColor.opacity(0.15), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 150
                            )
                        )
                        .frame(width: 300, height: 300)
                        .offset(
                            x: animateGradient ? 100 : 150,
                            y: geo.size.height - (animateGradient ? 100 : 150)
                        )
                        .blur(radius: 50)
                }
            }
            .ignoresSafeArea()
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 4).repeatForever(autoreverses: true)) {
                animateGradient = true
            }
        }
    }
}

#Preview {
    AuthView(viewModel: DependencyContainer.shared.makeAuthViewModel())
        .environmentObject(ThemeManager.shared)
}
