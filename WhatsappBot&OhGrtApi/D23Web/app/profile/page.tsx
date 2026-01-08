"use client";

import { useAuth } from "@/context/AuthContext";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Loader2,
  ArrowLeft,
  User,
  Mail,
  Calendar,
  MapPin,
  Clock,
  Save,
  Check,
  Camera,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import authFetch from "@/lib/auth_fetch";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface BirthDetails {
  id: string;
  user_id: string;
  full_name: string | null;
  birth_date: string | null;
  birth_time: string | null;
  birth_place: string | null;
  zodiac_sign: string | null;
  moon_sign: string | null;
  nakshatra: string | null;
  created_at: string;
  updated_at: string;
}

interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  photo_url: string | null;
  bio: string | null;
  preferences: {
    language?: string;
    theme?: string;
    ai_tone?: string;
  } | null;
  created_at: string;
}

export default function ProfilePage() {
  const { currentUser, loading, idToken, accessToken } = useAuth();
  const router = useRouter();
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api"; // Use Next.js proxy to avoid CORS

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [birthDetails, setBirthDetails] = useState<BirthDetails | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form state
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [language, setLanguage] = useState("en");
  const [aiTone, setAiTone] = useState("balanced");

  // Birth details form
  const [fullName, setFullName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [birthPlace, setBirthPlace] = useState("");

  useEffect(() => {
    if (!loading && !currentUser) {
      router.push("/");
    }
  }, [currentUser, loading, router]);

  useEffect(() => {
    if (idToken || accessToken) {
      fetchProfile();
      fetchBirthDetails();
    }
  }, [idToken, accessToken]);

  const fetchProfile = async () => {
    const token = accessToken || idToken;
    if (!token) return;

    try {
      const response = await authFetch(`${apiBase}/auth/me`, {}, token);
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setDisplayName(data.display_name || "");
        setBio(data.bio || "");
        setLanguage(data.preferences?.language || "en");
        setAiTone(data.preferences?.ai_tone || "balanced");
      }
    } catch (error) {
      console.error("Failed to fetch profile:", error);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const fetchBirthDetails = async () => {
    const token = accessToken || idToken;
    if (!token) return;

    try {
      const response = await authFetch(`${apiBase}/auth/birth-details`, {}, token);
      if (response.ok) {
        const data = await response.json();
        if (data) {
          setBirthDetails(data);
          setFullName(data.full_name || "");
          setBirthDate(data.birth_date || "");
          setBirthTime(data.birth_time || "");
          setBirthPlace(data.birth_place || "");
        }
      }
    } catch (error) {
      console.error("Failed to fetch birth details:", error);
    }
  };

  const handleSaveProfile = async () => {
    const token = accessToken || idToken;
    if (!token) return;

    setIsSaving(true);
    setSaveSuccess(false);

    try {
      // Update profile
      const profileResponse = await authFetch(
        `${apiBase}/auth/profile`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            display_name: displayName,
            bio: bio,
            preferences: {
              language,
              ai_tone: aiTone,
            },
          }),
        },
        token
      );

      // Update birth details
      const birthResponse = await authFetch(
        `${apiBase}/auth/birth-details`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: fullName || null,
            birth_date: birthDate || null,
            birth_time: birthTime || null,
            birth_place: birthPlace || null,
          }),
        },
        token
      );

      if (profileResponse.ok && birthResponse.ok) {
        setSaveSuccess(true);
        fetchProfile();
        fetchBirthDetails();
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (error) {
      console.error("Failed to save profile:", error);
    } finally {
      setIsSaving(false);
    }
  };

  if (loading || isLoadingProfile) {
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
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.back()}
            className="text-white/60 hover:text-white"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl font-semibold">Profile</h1>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Profile Header */}
        <div className="flex items-center gap-6">
          <div className="relative">
            <Avatar className="h-24 w-24">
              <AvatarImage src={profile?.photo_url || ""} />
              <AvatarFallback className="bg-gradient-to-br from-purple-500 to-pink-500 text-white text-2xl">
                {displayName?.[0]?.toUpperCase() || profile?.email?.[0]?.toUpperCase() || "U"}
              </AvatarFallback>
            </Avatar>
            <button className="absolute bottom-0 right-0 p-1.5 bg-white/10 rounded-full hover:bg-white/20 transition-colors">
              <Camera className="h-4 w-4 text-white/60" />
            </button>
          </div>
          <div>
            <h2 className="text-2xl font-semibold">{displayName || "Set your name"}</h2>
            <p className="text-white/40">{profile?.email}</p>
            <p className="text-white/30 text-sm mt-1">
              Member since {new Date(profile?.created_at || "").toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Basic Info Section */}
        <div className="bg-white/5 rounded-xl p-6 space-y-6">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <User className="h-5 w-5 text-purple-400" />
            Basic Information
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="displayName">Display Name</Label>
              <Input
                id="displayName"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your name"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                value={profile?.email || ""}
                disabled
                className="bg-white/5 border-white/10 text-white/50"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="bio">Bio</Label>
            <Textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell us about yourself..."
              className="bg-white/5 border-white/10 text-white min-h-[100px]"
            />
          </div>
        </div>

        {/* Preferences Section */}
        <div className="bg-white/5 rounded-xl p-6 space-y-6">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-400" />
            Preferences
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>Language</Label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-white/10">
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="hi">Hindi</SelectItem>
                  <SelectItem value="ta">Tamil</SelectItem>
                  <SelectItem value="te">Telugu</SelectItem>
                  <SelectItem value="mr">Marathi</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>AI Response Style</Label>
              <Select value={aiTone} onValueChange={setAiTone}>
                <SelectTrigger className="bg-white/5 border-white/10 text-white">
                  <SelectValue placeholder="Select style" />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-white/10">
                  <SelectItem value="concise">Concise</SelectItem>
                  <SelectItem value="balanced">Balanced</SelectItem>
                  <SelectItem value="detailed">Detailed</SelectItem>
                  <SelectItem value="friendly">Friendly</SelectItem>
                  <SelectItem value="professional">Professional</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Birth Details Section */}
        <div className="bg-white/5 rounded-xl p-6 space-y-6">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Clock className="h-5 w-5 text-orange-400" />
            Birth Details
            <span className="text-xs text-white/40 font-normal ml-2">(for astrology features)</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Full name as per birth certificate"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="birthPlace">Birth Place</Label>
              <Input
                id="birthPlace"
                value={birthPlace}
                onChange={(e) => setBirthPlace(e.target.value)}
                placeholder="City, Country"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="birthDate">Birth Date (DD-MM-YYYY)</Label>
              <Input
                id="birthDate"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                placeholder="15-08-1990"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="birthTime">Birth Time (HH:MM, 24hr)</Label>
              <Input
                id="birthTime"
                value={birthTime}
                onChange={(e) => setBirthTime(e.target.value)}
                placeholder="14:30"
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
          </div>

          {/* Calculated Details */}
          {birthDetails && (birthDetails.zodiac_sign || birthDetails.moon_sign) && (
            <div className="mt-4 p-4 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg">
              <h4 className="text-sm font-medium text-white/60 mb-3">Calculated Details</h4>
              <div className="grid grid-cols-3 gap-4">
                {birthDetails.zodiac_sign && (
                  <div>
                    <p className="text-xs text-white/40">Sun Sign</p>
                    <p className="text-white font-medium">{birthDetails.zodiac_sign}</p>
                  </div>
                )}
                {birthDetails.moon_sign && (
                  <div>
                    <p className="text-xs text-white/40">Moon Sign</p>
                    <p className="text-white font-medium">{birthDetails.moon_sign}</p>
                  </div>
                )}
                {birthDetails.nakshatra && (
                  <div>
                    <p className="text-xs text-white/40">Nakshatra</p>
                    <p className="text-white font-medium">{birthDetails.nakshatra}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Save Button */}
        <div className="flex justify-end gap-4">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            className="text-white/60 hover:text-white"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveProfile}
            disabled={isSaving}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : saveSuccess ? (
              <>
                <Check className="h-4 w-4 mr-2" />
                Saved!
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
