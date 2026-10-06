import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import { initialStructuralDesign, structuralDesignUrl } from './structural-design';
import type { StructuralDesign } from './structural-design';

const Context = createContext<{ design: StructuralDesign; setDesign: (design: StructuralDesign) => void } | null>(null);
export function StructuralDesignProvider({ children }: { children: ReactNode }) {
  const [design, update] = useState(() => initialStructuralDesign(location.search));
  function setDesign(next: StructuralDesign) {
    update(next); history.replaceState(null, '', structuralDesignUrl(location.href, next));
  }
  return <Context.Provider value={{ design, setDesign }}>{children}</Context.Provider>;
}
export function useStructuralDesign() {
  const value = useContext(Context);
  if (!value) throw new Error('StructuralDesignProvider is required.');
  return value;
}
