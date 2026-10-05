interface CachedResource<T> {
  promise: Promise<T>;
  value?: T;
}

// Share in-flight work and retain successful values for immediate view initialization.
export function createAsyncResourceCache<T>(loader: (path: string) => Promise<T>) {
  const resources = new Map<string, CachedResource<T>>();

  function load(path: string): Promise<T> {
    const existing = resources.get(path);
    if (existing) return existing.promise;

    // Deferring the loader also turns synchronous failures into retryable rejections.
    const pending = Promise.resolve().then(() => loader(path));
    const resource: CachedResource<T> = { promise: pending };
    resources.set(path, resource);
    void pending.then(value => {
      if (resources.get(path)?.promise === pending) resource.value = value;
    }, () => {
      if (resources.get(path)?.promise === pending) resources.delete(path);
    });
    return pending;
  }

  return {
    load,
    getCached(path: string): T | undefined { return resources.get(path)?.value; },
  };
}
