import type { Locale } from './localization';
import type { DownloadErrorCode, DownloadProgress } from './download-resource';

export const downloadCopy = {
  zh: {
    starting: '准备下载…', processing: '正在校验文件…', cancelled: '下载已取消',
    saved: '文件已交给浏览器保存', cancel: '取消', retry: '重试', compressed: '下载压缩包',
    size: '文件大小', transfer: '压缩下载', downloading: '下载中',
    errors: {
      http: '服务器无法提供文件（HTTP {status}）。', network: '网络连接中断，请检查连接后重试。',
      timeout: '下载超时，请重试。', integrity: '文件大小或校验值不符，未保存。请刷新页面后重试。',
      format: '服务器返回的文件格式不正确，未保存。请重试。',
      manifest: '无法读取文件校验清单，下载未开始。请检查连接后重试。',
    },
  },
  ja: {
    starting: 'ダウンロードを準備中…', processing: 'ファイルを検証中…', cancelled: 'ダウンロードをキャンセルしました',
    saved: 'ブラウザへファイルを渡しました', cancel: 'キャンセル', retry: '再試行', compressed: '圧縮ファイルをダウンロード',
    size: 'ファイルサイズ', transfer: '圧縮ダウンロード', downloading: 'ダウンロード中',
    errors: {
      http: 'サーバーからファイルを取得できません（HTTP {status}）。', network: '接続が切れました。接続を確認して再試行してください。',
      timeout: 'ダウンロードがタイムアウトしました。再試行してください。',
      integrity: 'サイズまたは検証値が一致しないため保存しませんでした。ページを更新して再試行してください。',
      format: 'サーバーから正しい形式のファイルを取得できず、保存しませんでした。再試行してください。',
      manifest: 'ファイル検証一覧を読み込めず、ダウンロードを開始しませんでした。接続を確認して再試行してください。',
    },
  },
  en: {
    starting: 'Preparing download…', processing: 'Checking file…', cancelled: 'Download cancelled',
    saved: 'File sent to your browser for saving', cancel: 'Cancel', retry: 'Retry', compressed: 'Download compressed file',
    size: 'File size', transfer: 'Compressed download', downloading: 'Downloading',
    errors: {
      http: 'The server could not provide this file (HTTP {status}).', network: 'The connection was interrupted. Check your connection and retry.',
      timeout: 'The download timed out. Please retry.',
      integrity: 'The file size or checksum did not match, so it was not saved. Refresh the page and retry.',
      format: 'The server returned an incorrect file format, so it was not saved. Please retry.',
      manifest: 'The file verification manifest could not be loaded, so the download did not start. Check your connection and retry.',
    },
  },
} as const;

export function formatDownloadBytes(bytes: number, locale: Locale): string {
  const unit = bytes >= 1_000_000 ? 'MB' : bytes >= 1_000 ? 'KB' : 'B';
  const divisor = unit === 'MB' ? 1_000_000 : unit === 'KB' ? 1_000 : 1;
  return `${new Intl.NumberFormat(locale, { maximumFractionDigits: unit === 'B' ? 0 : 1 }).format(bytes / divisor)} ${unit}`;
}
export function downloadProgressText(progress: DownloadProgress, locale: Locale): string {
  const loaded = formatDownloadBytes(progress.loaded, locale);
  return `${downloadCopy[locale].downloading} ${loaded}${progress.total ? ` / ${formatDownloadBytes(progress.total, locale)}` : ''}`;
}
export function downloadErrorText(code: DownloadErrorCode, status: number | undefined, locale: Locale): string {
  return downloadCopy[locale].errors[code].replace('{status}', String(status ?? '—'));
}
