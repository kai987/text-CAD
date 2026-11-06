import type { Locale } from './localization';

export class UnsupportedModelCompressionError extends Error {
  constructor() {
    super('This browser cannot decompress the model.');
    this.name = 'UnsupportedModelCompressionError';
  }
}

const unsupported = {
  ja: 'このブラウザーはモデルの展開に対応していません。ブラウザーを更新して、もう一度お試しください。',
  zh: '此浏览器不支持解压模型。请更新浏览器后重试。',
  en: 'This browser cannot decompress the model. Update your browser and try again.',
} as const;

export function loadFailureMessage(error: unknown, locale: Locale, fallback: string): string {
  return error instanceof UnsupportedModelCompressionError ? unsupported[locale] : fallback;
}
