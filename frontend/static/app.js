/**
 * The Iris Panel — React entry point.
 */
import { React } from './lib.js';
import ReactDOM from 'react-dom/client';
import App from './components/App.js';

const { createElement } = React;
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(createElement(App));
