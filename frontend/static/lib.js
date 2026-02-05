/**
 * htm + React binding.
 * Usage: import { html, React } from './lib.js';
 */
import React from 'react';
import htm from 'htm';

const html = htm.bind(React.createElement);

export { html, React };
