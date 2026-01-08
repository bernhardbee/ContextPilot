/**
 * Context Templates component for quick context creation
 */
import React from 'react';
import { ContextType, ContextUnitCreate } from './types';

interface ContextTemplatesProps {
  onUseTemplate: (template: ContextUnitCreate) => void;
}

const TEMPLATES: Array<{ name: string; icon: string; template: ContextUnitCreate }> = [
  {
    name: 'Code Preference',
    icon: '💻',
    template: {
      type: ContextType.PREFERENCE,
      content: 'I prefer writing clean, well-documented code with comprehensive unit tests.',
      confidence: 1.0,
      tags: ['coding', 'quality', 'testing'],
    },
  },
  {
    name: 'Communication Style',
    icon: '💬',
    template: {
      type: ContextType.PREFERENCE,
      content: 'I prefer direct, concise communication with actionable next steps.',
      confidence: 1.0,
      tags: ['communication', 'style'],
    },
  },
  {
    name: 'Learning Goal',
    icon: '🎯',
    template: {
      type: ContextType.GOAL,
      content: 'I want to master TypeScript and modern web development practices.',
      confidence: 1.0,
      tags: ['learning', 'typescript', 'web-dev'],
    },
  },
  {
    name: 'Tech Stack Decision',
    icon: '🛠️',
    template: {
      type: ContextType.DECISION,
      content: 'I decided to use React with TypeScript for frontend development.',
      confidence: 1.0,
      tags: ['tech-stack', 'react', 'typescript'],
    },
  },
  {
    name: 'Project Fact',
    icon: '📋',
    template: {
      type: ContextType.FACT,
      content: 'This project uses PostgreSQL for data persistence and FastAPI for the backend.',
      confidence: 1.0,
      tags: ['project', 'database', 'backend'],
    },
  },
  {
    name: 'Work Schedule',
    icon: '⏰',
    template: {
      type: ContextType.PREFERENCE,
      content: 'I work best in the morning and prefer focused, uninterrupted work blocks.',
      confidence: 1.0,
      tags: ['schedule', 'productivity'],
    },
  },
];

export function ContextTemplates({ onUseTemplate }: ContextTemplatesProps) {
  return (
    <div className="context-templates">
      <h3>📝 Quick Templates</h3>
      <div className="template-grid">
        {TEMPLATES.map((template, index) => (
          <button
            key={index}
            className="template-card"
            onClick={() => onUseTemplate(template.template)}
            title="Click to use this template"
          >
            <div className="template-icon">{template.icon}</div>
            <div className="template-name">{template.name}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
