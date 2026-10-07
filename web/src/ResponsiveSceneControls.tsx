import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { SlidersHorizontal } from 'lucide-react';

/** Keep control children mounted when the mobile panel is collapsed. */
export default function ResponsiveSceneControls({ title, summary, children }: {
  title: string; summary: string; children: ReactNode;
}) {
  const [mobile, setMobile] = useState(() => window.matchMedia('(max-width: 760px)').matches);
  const [mobileOpen, setMobileOpen] = useState(false);
  useEffect(() => {
    const media = window.matchMedia('(max-width: 760px)');
    const onChange = (event: MediaQueryListEvent) => setMobile(event.matches);
    media.addEventListener('change', onChange);
    setMobile(media.matches);
    return () => media.removeEventListener('change', onChange);
  }, []);
  return <details className="scene-options" open={!mobile || mobileOpen}>
    <summary onClick={event => {
      event.preventDefault();
      if (mobile) setMobileOpen(previous => !previous);
    }}>
      <span className="scene-options-title"><SlidersHorizontal size={16} aria-hidden="true" />{title}</span>
      <span className="scene-options-state">{summary}</span>
    </summary>
    <div className="scene-options-content">{children}</div>
  </details>;
}
