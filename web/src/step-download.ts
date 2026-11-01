import { decodeGzipBlob } from './download-transport.ts';

export async function decodeStepBlob(input: Blob): Promise<Blob> {
  const blob = await decodeGzipBlob(input);
  if (!(await blob.slice(0, 15).text()).startsWith('ISO-10303-21;')) {
    throw new Error('Downloaded payload is not a STEP document');
  }
  return blob;
}

export async function decodedStep(url: string, fetcher: typeof fetch = fetch): Promise<Blob> {
  const response = await fetcher(url, { signal: AbortSignal.timeout(60000) });
  if (!response.ok || !response.body) throw new Error(`STEP download failed: ${response.status}`);
  return decodeStepBlob(await response.blob());
}
