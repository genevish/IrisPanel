/**
 * The Iris Panel — React entry point.
 */
import { React } from './lib.js';
import ReactDOM from 'react-dom/client';
import App from './components/App.js';

const { createElement } = React;

// Error boundary for debugging
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, info) {
        console.error('React Error:', error, info);
    }
    render() {
        if (this.state.hasError) {
            return createElement('div', { style: { padding: '20px', color: 'red' } },
                createElement('h1', null, 'Something went wrong'),
                createElement('pre', null, this.state.error?.toString())
            );
        }
        return this.props.children;
    }
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(createElement(ErrorBoundary, null, createElement(App)));
