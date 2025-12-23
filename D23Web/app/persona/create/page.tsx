"use client";

import { useAuth } from "@/context/AuthContext";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Loader2,
  ArrowLeft,
  ArrowRight,
  Check,
  User,
  Briefcase,
  Sparkles,
  Upload,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import authFetch from "@/lib/auth_fetch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const STEPS = [
  { id: 1, title: "Handle & Basic Info", icon: User },
  { id: 2, title: "Personality", icon: Sparkles },
  { id: 3, title: "Professional", icon: Briefcase },
  { id: 4, title: "Documents", icon: Upload },
  { id: 5, title: "Preview", icon: Eye },
];

export default function CreatePersonaPage() {
  const { currentUser, loading, idToken, accessToken } = useAuth();
  const router = useRouter();
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [currentStep, setCurrentStep] = useState(1);
  const [isCreating, setIsCreating] = useState(false);
  const [handleAvailable, setHandleAvailable] = useState<boolean | null>(null);
  const [checkingHandle, setCheckingHandle] = useState(false);

  // Form data
  const [handle, setHandle] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [tagline, setTagline] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");

  // Personality
  const [communicationStyle, setCommunicationStyle] = useState("professional");
  const [expertiseArea, setExpertiseArea] = useState("");
  const [topics, setTopics] = useState("");
  const [responseLength, setResponseLength] = useState("moderate");
  const [useHumor, setUseHumor] = useState("sometimes");
  const [outsideExpertise, setOutsideExpertise] = useState("acknowledge and redirect");

  // Professional
  const [jobTitle, setJobTitle] = useState("");
  const [industry, setIndustry] = useState("");
  const [yearsExperience, setYearsExperience] = useState("");
  const [skills, setSkills] = useState("");
  const [achievements, setAchievements] = useState("");
  const [problemsSolved, setProblemsSolved] = useState("");

  useEffect(() => {
    if (!loading && !currentUser) {
      router.push("/");
    }
  }, [currentUser, loading, router]);

  const checkHandle = async (value: string) => {
    if (value.length < 3) {
      setHandleAvailable(null);
      return;
    }

    setCheckingHandle(true);
    try {
      const response = await fetch(`${apiBase}/personas/check-handle/${value}`);
      if (response.ok) {
        const data = await response.json();
        setHandleAvailable(data.available);
      }
    } catch (error) {
      console.error("Failed to check handle:", error);
    } finally {
      setCheckingHandle(false);
    }
  };

  const handleHandleChange = (value: string) => {
    const sanitized = value.toLowerCase().replace(/[^a-z0-9_]/g, "");
    setHandle(sanitized);
    if (sanitized.length >= 3) {
      checkHandle(sanitized);
    } else {
      setHandleAvailable(null);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return handle.length >= 3 && handleAvailable && displayName.length >= 1;
      case 2:
        return expertiseArea.length > 0;
      case 3:
        return true; // Optional
      case 4:
        return true; // Optional
      case 5:
        return true;
      default:
        return false;
    }
  };

  const handleCreate = async () => {
    const token = accessToken || idToken;
    if (!token) return;

    setIsCreating(true);

    try {
      const response = await authFetch(
        `${apiBase}/personas`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            handle,
            display_name: displayName,
            tagline: tagline || null,
            avatar_url: avatarUrl || null,
            personality: {
              communication_style: communicationStyle,
              expertise_area: expertiseArea,
              topics: topics.split(",").map(t => t.trim()).filter(Boolean),
              outside_expertise_response: outsideExpertise,
              response_length: responseLength,
              use_humor: useHumor,
            },
            professional: {
              job_title: jobTitle || null,
              industry: industry || null,
              years_experience: yearsExperience ? parseInt(yearsExperience) : null,
              skills: skills.split(",").map(s => s.trim()).filter(Boolean),
              achievements: achievements || null,
              problems_solved: problemsSolved || null,
            },
            is_public: true,
          }),
        },
        token
      );

      if (response.ok) {
        router.push("/persona");
      } else {
        const error = await response.json();
        console.error("Failed to create persona:", error);
      }
    } catch (error) {
      console.error("Failed to create persona:", error);
    } finally {
      setIsCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-white" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-[#0a0a0a]/95 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.back()}
            className="text-white/60 hover:text-white"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl font-semibold">Create AI Persona</h1>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => (
            <React.Fragment key={step.id}>
              <div
                className={`flex flex-col items-center ${
                  currentStep >= step.id ? "text-white" : "text-white/30"
                }`}
              >
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    currentStep > step.id
                      ? "bg-green-500"
                      : currentStep === step.id
                      ? "bg-gradient-to-r from-purple-500 to-pink-500"
                      : "bg-white/10"
                  }`}
                >
                  {currentStep > step.id ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <step.icon className="h-5 w-5" />
                  )}
                </div>
                <span className="text-xs mt-2 hidden sm:block">{step.title}</span>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-2 ${
                    currentStep > step.id ? "bg-green-500" : "bg-white/10"
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Step 1: Handle & Basic Info */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label>Handle</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40">@</span>
                <Input
                  value={handle}
                  onChange={(e) => handleHandleChange(e.target.value)}
                  placeholder="yourhandle"
                  className="bg-white/5 border-white/10 text-white pl-8"
                />
                {checkingHandle && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-white/40" />
                )}
                {!checkingHandle && handleAvailable === true && (
                  <Check className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-green-400" />
                )}
                {!checkingHandle && handleAvailable === false && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-red-400 text-sm">Taken</span>
                )}
              </div>
              <p className="text-xs text-white/40">This will be your public URL: ohgrt.com/p/{handle || "yourhandle"}</p>
            </div>

            <div className="space-y-2">
              <Label>Display Name</Label>
              <Input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Dr. Jane Smith"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>Tagline</Label>
              <Input
                value={tagline}
                onChange={(e) => setTagline(e.target.value)}
                placeholder="AI expert helping you build the future"
                className="bg-white/5 border-white/10 text-white"
                maxLength={200}
              />
              <p className="text-xs text-white/40">{tagline.length}/200 characters</p>
            </div>

            <div className="space-y-2">
              <Label>Avatar URL (optional)</Label>
              <Input
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://example.com/avatar.jpg"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
          </div>
        )}

        {/* Step 2: Personality */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label>Communication Style</Label>
              <Select value={communicationStyle} onValueChange={setCommunicationStyle}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-white/10">
                  <SelectItem value="formal">Formal</SelectItem>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="casual">Casual</SelectItem>
                  <SelectItem value="friendly">Friendly</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Primary Expertise Area *</Label>
              <Input
                value={expertiseArea}
                onChange={(e) => setExpertiseArea(e.target.value)}
                placeholder="Machine Learning, Marketing, Finance..."
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>Topics You Know About (comma-separated)</Label>
              <Textarea
                value={topics}
                onChange={(e) => setTopics(e.target.value)}
                placeholder="Python, TensorFlow, Neural Networks, Data Science"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>Response Length</Label>
              <Select value={responseLength} onValueChange={setResponseLength}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-white/10">
                  <SelectItem value="brief">Brief - Get to the point</SelectItem>
                  <SelectItem value="moderate">Moderate - Balanced detail</SelectItem>
                  <SelectItem value="detailed">Detailed - Thorough explanations</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Use Humor</Label>
              <Select value={useHumor} onValueChange={setUseHumor}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-white/10">
                  <SelectItem value="never">Never - Always serious</SelectItem>
                  <SelectItem value="sometimes">Sometimes - When appropriate</SelectItem>
                  <SelectItem value="often">Often - Light and fun</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>When Asked About Things Outside Your Expertise</Label>
              <Select value={outsideExpertise} onValueChange={setOutsideExpertise}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-white/10">
                  <SelectItem value="acknowledge and redirect">Acknowledge and redirect to my expertise</SelectItem>
                  <SelectItem value="try to help">Try to help with general knowledge</SelectItem>
                  <SelectItem value="politely decline">Politely decline</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        {/* Step 3: Professional */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label>Job Title / Role</Label>
              <Input
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="Senior Software Engineer, Marketing Director..."
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>Industry</Label>
              <Input
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="Technology, Healthcare, Finance..."
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>Years of Experience</Label>
              <Input
                type="number"
                value={yearsExperience}
                onChange={(e) => setYearsExperience(e.target.value)}
                placeholder="10"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>Key Skills (comma-separated)</Label>
              <Textarea
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                placeholder="Project Management, Team Leadership, Python, Data Analysis"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>Notable Achievements or Credentials</Label>
              <Textarea
                value={achievements}
                onChange={(e) => setAchievements(e.target.value)}
                placeholder="PhD from MIT, Published 50+ research papers..."
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>What Problems Do You Help Solve?</Label>
              <Textarea
                value={problemsSolved}
                onChange={(e) => setProblemsSolved(e.target.value)}
                placeholder="I help startups scale their engineering teams..."
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
          </div>
        )}

        {/* Step 4: Documents */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center">
              <Upload className="h-12 w-12 mx-auto text-white/40 mb-4" />
              <h3 className="text-lg font-medium mb-2">Upload Training Documents</h3>
              <p className="text-white/40 text-sm mb-4">
                Optional: Upload PDFs with your expertise to enhance your AI persona
              </p>
              <Button variant="outline" className="border-white/20 text-white hover:bg-white/10">
                Choose Files
              </Button>
              <p className="text-white/30 text-xs mt-2">PDF files only, max 10MB each</p>
            </div>
            <p className="text-center text-white/40 text-sm">
              You can skip this step and add documents later
            </p>
          </div>
        )}

        {/* Step 5: Preview */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div className="bg-white/5 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <Avatar className="h-16 w-16">
                  <AvatarImage src={avatarUrl} />
                  <AvatarFallback className="bg-gradient-to-br from-purple-500 to-pink-500 text-white text-xl">
                    {displayName[0]?.toUpperCase() || "?"}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="text-xl font-semibold">{displayName}</h2>
                  <p className="text-white/40">@{handle}</p>
                  {tagline && <p className="text-white/60 mt-2">{tagline}</p>}
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-white/40">Expertise</p>
                  <p className="text-white">{expertiseArea}</p>
                </div>
                {jobTitle && (
                  <div>
                    <p className="text-white/40">Role</p>
                    <p className="text-white">{jobTitle}</p>
                  </div>
                )}
                {industry && (
                  <div>
                    <p className="text-white/40">Industry</p>
                    <p className="text-white">{industry}</p>
                  </div>
                )}
                <div>
                  <p className="text-white/40">Style</p>
                  <p className="text-white capitalize">{communicationStyle}</p>
                </div>
              </div>

              {topics && (
                <div className="mt-4">
                  <p className="text-white/40 text-sm mb-2">Topics</p>
                  <div className="flex flex-wrap gap-2">
                    {topics.split(",").map((topic, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-white/10 rounded-full text-xs"
                      >
                        {topic.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <p className="text-center text-white/40 text-sm">
              Your persona will be publicly accessible at ohgrt.com/p/{handle}
            </p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <Button
            variant="ghost"
            onClick={() => setCurrentStep(prev => prev - 1)}
            disabled={currentStep === 1}
            className="text-white/60"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>

          {currentStep < 5 ? (
            <Button
              onClick={() => setCurrentStep(prev => prev + 1)}
              disabled={!canProceed()}
              className="bg-gradient-to-r from-purple-500 to-pink-500"
            >
              Next
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={handleCreate}
              disabled={isCreating}
              className="bg-gradient-to-r from-purple-500 to-pink-500"
            >
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Create Persona
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
