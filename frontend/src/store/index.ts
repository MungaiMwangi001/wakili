/**
 * Zustand global store – manages auth state and language preference.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Lang } from "@/i18n/translations";
import { translations, type TranslationKey } from "@/i18n/translations";

interface User {
  id: number;
  email: string;
  full_name: string;
  preferred_language: Lang;
}

interface AppStore {
  // Auth
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;

  // Language
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: TranslationKey) => string;
}

export const useStore = create<AppStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      lang: "en",

      setAuth: (user, token) => set({ user, token, lang: user.preferred_language }),
      logout: () => set({ user: null, token: null }),

      setLang: (lang) => set({ lang }),

      t: (key) => {
        const lang = get().lang;
        return (translations[lang] as Record<string, string>)[key] ?? key;
      },
    }),
    { name: "wakili-store", partialize: (s) => ({ token: s.token, user: s.user, lang: s.lang }) }
  )
);
