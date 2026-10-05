import { asset } from './data';
import { createAsyncResourceCache } from './async-resource-cache';

// The approved PDF conversion is static; prefetch and page rendering share parsed vectors.
const vectors = createAsyncResourceCache(async (path: string) => {
  const response = await fetch(asset(path));
  if (!response.ok) throw new Error('The vector plan could not be loaded.');
  const document = new DOMParser().parseFromString(await response.text(), 'image/svg+xml');
  if (document.querySelector('parsererror') || document.documentElement.localName !== 'svg' ||
      document.querySelector('script, foreignObject, image, text')) {
    throw new Error('Invalid vector plan.');
  }
  return document.documentElement.innerHTML;
});

export const loadPlanVectors = vectors.load;
export const getCachedPlanVectors = vectors.getCached;
