import { useState } from 'react';
import type { ReactNode } from 'react';

export default function ControlSection({ title, children, initiallyOpen = false }: { title: string; children: ReactNode; initiallyOpen?: boolean }) {
  const [open, setOpen] = useState(initiallyOpen);
  return <details className="control-disclosure" open={open} onToggle={event => setOpen(event.currentTarget.open)}>
    <summary><h2>{title}</h2></summary>
    <div className="control-disclosure-content">{children}</div>
  </details>;
}
