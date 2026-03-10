import React from 'react';

import { emitSystemError } from '../lib/systemError';
import { ErrorPage } from '../pages/Error';

interface SystemErrorBoundaryProps {
    children: React.ReactNode;
}

interface SystemErrorBoundaryState {
    hasError: boolean;
}

export class SystemErrorBoundary extends React.Component<SystemErrorBoundaryProps, SystemErrorBoundaryState> {
    state: SystemErrorBoundaryState = {
        hasError: false
    };

    static getDerivedStateFromError(): SystemErrorBoundaryState {
        return { hasError: true };
    }

    componentDidCatch(error: Error): void {
        emitSystemError({
            source: 'runtime',
            title: 'Application Error',
            message: error.message || 'An unexpected runtime error occurred.'
        });
    }

    render(): React.ReactNode {
        if (this.state.hasError) {
            return <ErrorPage boundaryFallback={true} />;
        }

        return this.props.children;
    }
}
