export async function decodedStep(url: string, fetcher: typeof fetch = fetch): Promise<Blob> {
  const response = await fetcher(url, { signal: AbortSignal.timeout(60000) });
  if (!response.ok || !response.body) throw new Error(`STEP download failed: ${response.status}`);
  let blob = await response.blob();
  // Some hosts send .gz with Content-Encoding; fetch then already decodes it.
  const prefix = new Uint8Array(await blob.slice(0, 2).arrayBuffer());
  if (prefix[0] === 0x1f && prefix[1] === 0x8b) {
    blob = await new Response(blob.stream().pipeThrough(new DecompressionStream('gzip'))).blob();
  }
  if (!(await blob.slice(0, 15).text()).startsWith('ISO-10303-21;')) {
    throw new Error('Downloaded payload is not a STEP document');
  }
  return blob;
}
