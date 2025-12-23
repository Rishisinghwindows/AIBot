'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Import all locale files
import en from '@/locales/en.json';
import hi from '@/locales/hi.json';
import ta from '@/locales/ta.json';
import te from '@/locales/te.json';
import ml from '@/locales/ml.json';
import kn from '@/locales/kn.json';
import pa from '@/locales/pa.json';
import mr from '@/locales/mr.json';
import bn from '@/locales/bn.json';
import or from '@/locales/or.json';
import bho from '@/locales/bho.json';

export type LanguageCode = 'en' | 'hi' | 'ta' | 'te' | 'ml' | 'kn' | 'pa' | 'mr' | 'bn' | 'or' | 'bho';

export interface Language {
  code: LanguageCode;
  name: string;
  nativeName: string;
}

export const languages: Language[] = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिंदी' },
  { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
  { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు' },
  { code: 'ml', name: 'Malayalam', nativeName: 'മലയാളം' },
  { code: 'kn', name: 'Kannada', nativeName: 'ಕನ್ನಡ' },
  { code: 'pa', name: 'Punjabi', nativeName: 'ਪੰਜਾਬੀ' },
  { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
  { code: 'or', name: 'Odia', nativeName: 'ଓଡ଼ିଆ' },
  { code: 'bho', name: 'Bhojpuri', nativeName: 'भोजपुरी' },
];

const locales: Record<LanguageCode, typeof en> = {
  en,
  hi,
  bn,
  ta,
  te,
  ml,
  kn,
  pa,
  mr,
  or,
  bho,
};

interface LanguageContextType {
  language: LanguageCode;
  setLanguage: (lang: LanguageCode) => void;
  t: typeof en;
  languages: Language[];
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

interface LanguageProviderProps {
  children: ReactNode;
  defaultLanguage?: LanguageCode;
}

export function LanguageProvider({ children, defaultLanguage = 'en' }: LanguageProviderProps) {
  const [language, setLanguageState] = useState<LanguageCode>(defaultLanguage);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Check localStorage for saved language preference
    const savedLang = localStorage.getItem('d23-language') as LanguageCode | null;
    if (savedLang && locales[savedLang]) {
      setLanguageState(savedLang);
    } else {
      // Try to detect browser language
      const browserLang = navigator.language.split('-')[0] as LanguageCode;
      if (locales[browserLang]) {
        setLanguageState(browserLang);
      }
    }
  }, []);

  const setLanguage = (lang: LanguageCode) => {
    setLanguageState(lang);
    localStorage.setItem('d23-language', lang);
  };

  const t = locales[language];

  // Prevent hydration mismatch by rendering with default language on server
  if (!mounted) {
    return (
      <LanguageContext.Provider value={{ language: defaultLanguage, setLanguage, t: locales[defaultLanguage], languages }}>
        {children}
      </LanguageContext.Provider>
    );
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, languages }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

// Helper hook for getting translations
export function useTranslations() {
  const { t } = useLanguage();
  return t;
}
