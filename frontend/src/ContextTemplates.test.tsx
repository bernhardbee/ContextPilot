import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ContextTemplates } from './ContextTemplates';
import { render } from './test/render-with-providers';
import { ContextType } from './types';

describe('ContextTemplates', () => {
  it('renders quick templates heading', () => {
    render(<ContextTemplates onUseTemplate={vi.fn()} />);
    expect(screen.getByText('📝 Quick Templates')).toBeInTheDocument();
  });

  it('renders all template cards', () => {
    render(<ContextTemplates onUseTemplate={vi.fn()} />);
    expect(screen.getByRole('button', { name: /code preference/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /communication style/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /learning goal/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /tech stack decision/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /project fact/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /work schedule/i })).toBeInTheDocument();
  });

  it('shows click tooltip on templates', () => {
    render(<ContextTemplates onUseTemplate={vi.fn()} />);
    const button = screen.getByRole('button', { name: /code preference/i });
    expect(button).toHaveAttribute('title', 'Click to use this template');
  });

  it('calls onUseTemplate with code preference template', async () => {
    const onUseTemplate = vi.fn();
    const { user } = render(<ContextTemplates onUseTemplate={onUseTemplate} />);

    await user.click(screen.getByRole('button', { name: /code preference/i }));

    expect(onUseTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        type: ContextType.PREFERENCE,
        content: expect.stringContaining('well-documented code'),
      })
    );
  });

  it('calls onUseTemplate with learning goal template', async () => {
    const onUseTemplate = vi.fn();
    const { user } = render(<ContextTemplates onUseTemplate={onUseTemplate} />);

    await user.click(screen.getByRole('button', { name: /learning goal/i }));

    expect(onUseTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        type: ContextType.GOAL,
        tags: expect.arrayContaining(['learning', 'typescript']),
      })
    );
  });

  it('calls onUseTemplate with tech stack decision template', async () => {
    const onUseTemplate = vi.fn();
    const { user } = render(<ContextTemplates onUseTemplate={onUseTemplate} />);

    await user.click(screen.getByRole('button', { name: /tech stack decision/i }));

    expect(onUseTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        type: ContextType.DECISION,
        tags: expect.arrayContaining(['tech-stack', 'react']),
      })
    );
  });

  it('calls onUseTemplate with project fact template', async () => {
    const onUseTemplate = vi.fn();
    const { user } = render(<ContextTemplates onUseTemplate={onUseTemplate} />);

    await user.click(screen.getByRole('button', { name: /project fact/i }));

    expect(onUseTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        type: ContextType.FACT,
        content: expect.stringContaining('PostgreSQL'),
      })
    );
  });

  it('fires callback for each template click', async () => {
    const onUseTemplate = vi.fn();
    const { user } = render(<ContextTemplates onUseTemplate={onUseTemplate} />);

    const buttons = screen.getAllByRole('button', { name: /code preference|communication style|learning goal|tech stack decision|project fact|work schedule/i });

    for (const button of buttons) {
      await user.click(button);
    }

    expect(onUseTemplate).toHaveBeenCalledTimes(6);
  });
});
