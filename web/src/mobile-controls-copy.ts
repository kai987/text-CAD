import type { Locale } from './localization';

export const mobileControlsCopy = {
  zh: { sceneSettings: '场景设置' },
  ja: { sceneSettings: '表示設定' },
  en: { sceneSettings: 'Scene settings' },
} satisfies Record<Locale, { sceneSettings: string }>;
