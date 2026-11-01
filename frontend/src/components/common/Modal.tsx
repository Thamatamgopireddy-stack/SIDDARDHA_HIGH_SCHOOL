import { X } from 'lucide-react'
import type { ReactNode } from 'react'

export function Modal({
  title,
  description,
  onClose,
  children,
  footer,
}: {
  title: string
  description?: string
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
}) {
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
      role="presentation"
    >
      <section aria-labelledby="modal-title" aria-modal="true" className="modal" role="dialog">
        <header className="modal-header">
          <div>
            <div className="modal-title" id="modal-title">{title}</div>
            {description && <div className="modal-description">{description}</div>}
          </div>
          <button aria-label="Close dialog" className="icon-button" onClick={onClose} type="button"><X size={17} /></button>
        </header>
        <div className="modal-content">{children}</div>
        {footer && <footer className="modal-footer">{footer}</footer>}
      </section>
    </div>
  )
}
