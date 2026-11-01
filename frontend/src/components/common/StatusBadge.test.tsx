import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it('formats underscore-separated API states for display', () => {
    render(<StatusBadge value="under_review" />)
    expect(screen.getByText('under review')).toBeInTheDocument()
  })
})
