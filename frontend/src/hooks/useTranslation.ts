// src/hooks/useTranslation.ts
// Returns the translation object for the current language.

import { useStore } from "@/store";
import { translations } from "@/i18n/translations";

export function useTranslation() {
  const lang = useStore((s) => s.lang);
  const t = translations[lang];

  /**
   * Dot-notation accessor: t('nav.dashboard') → "Dashboard" | "Dashibodi"
   * Falls back to English if key missing in Swahili.
   */
  function translate(key: string): string {
    const keys = key.split(".");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let result: any = t;
    for (const k of keys) {
      result = result?.[k];
    }
    if (!result) {
      // Fallback to English
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let fallback: any = translations["en"];
      for (const k of keys) fallback = fallback?.[k];
      return fallback ?? key;
    }
    return result;
  }

  return { t: translate, lang };
}
