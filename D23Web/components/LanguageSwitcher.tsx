'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLanguage, LanguageCode } from '@/lib/i18n/LanguageContext';
import { Globe, ChevronDown, Check } from 'lucide-react';

interface LanguageSwitcherProps {
  variant?: 'default' | 'minimal' | 'pill';
  showNativeName?: boolean;
  className?: string;
}

export function LanguageSwitcher({
  variant = 'default',
  showNativeName = true,
  className = ''
}: LanguageSwitcherProps) {
  const { language, setLanguage, languages } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLanguage = languages.find(l => l.code === language);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (code: LanguageCode) => {
    setLanguage(code);
    setIsOpen(false);
  };

  if (variant === 'minimal') {
    return (
      <div ref={dropdownRef} className={`relative ${className}`}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-1.5 px-2 py-1 text-sm text-zinc-400 hover:text-white transition-colors"
        >
          <Globe className="w-4 h-4" />
          <span>{currentLanguage?.nativeName || 'EN'}</span>
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-1 py-1 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl min-w-[140px] z-50"
            >
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleSelect(lang.code)}
                  className={`w-full px-3 py-2 text-left text-sm flex items-center justify-between hover:bg-zinc-800 transition-colors ${
                    language === lang.code ? 'text-green-400' : 'text-zinc-300'
                  }`}
                >
                  <span>{lang.nativeName}</span>
                  {language === lang.code && <Check className="w-3.5 h-3.5" />}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  if (variant === 'pill') {
    return (
      <div ref={dropdownRef} className={`relative ${className}`}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700 rounded-full text-sm text-zinc-300 hover:text-white transition-all"
        >
          <Globe className="w-4 h-4" />
          <span>{currentLanguage?.nativeName}</span>
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-2 py-2 bg-zinc-900/95 backdrop-blur-xl border border-zinc-800 rounded-xl shadow-2xl min-w-[180px] z-50"
            >
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleSelect(lang.code)}
                  className={`w-full px-4 py-2.5 text-left flex items-center justify-between hover:bg-zinc-800/50 transition-colors ${
                    language === lang.code ? 'text-green-400 bg-green-500/10' : 'text-zinc-300'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-medium">{lang.nativeName}</span>
                    {showNativeName && lang.code !== 'en' && (
                      <span className="text-xs text-zinc-500">{lang.name}</span>
                    )}
                  </div>
                  {language === lang.code && <Check className="w-4 h-4" />}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // Default variant
  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-zinc-300 hover:text-white transition-all"
      >
        <Globe className="w-4 h-4" />
        <span>{currentLanguage?.nativeName}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -8 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 py-2 bg-zinc-900/95 backdrop-blur-xl border border-zinc-800 rounded-xl shadow-2xl min-w-[200px] z-50 max-h-[320px] overflow-y-auto"
          >
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleSelect(lang.code)}
                className={`w-full px-4 py-3 text-left flex items-center justify-between hover:bg-zinc-800/50 transition-colors ${
                  language === lang.code ? 'text-green-400 bg-green-500/10' : 'text-zinc-300'
                }`}
              >
                <div className="flex flex-col">
                  <span className="font-medium">{lang.nativeName}</span>
                  {showNativeName && (
                    <span className="text-xs text-zinc-500">{lang.name}</span>
                  )}
                </div>
                {language === lang.code && <Check className="w-4 h-4" />}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Inline language bar for showing available languages
export function LanguageBar({ className = '' }: { className?: string }) {
  const { language, setLanguage, languages } = useLanguage();

  return (
    <div className={`flex flex-wrap items-center justify-center gap-2 ${className}`}>
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => setLanguage(lang.code)}
          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
            language === lang.code
              ? 'bg-green-500 text-black'
              : 'bg-zinc-800/50 text-zinc-400 hover:bg-zinc-800 hover:text-white'
          }`}
        >
          {lang.nativeName}
        </button>
      ))}
    </div>
  );
}
