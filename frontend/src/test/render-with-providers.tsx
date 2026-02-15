import { render as rtlRender } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';

export function render(ui: React.ReactElement, options = {}) {
  return {
    ...rtlRender(ui, { ...options }),
    user: userEvent.setup(),
  };
}
