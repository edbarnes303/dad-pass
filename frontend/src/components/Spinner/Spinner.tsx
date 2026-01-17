import { useEffect, useState } from 'react';
import './Spinner.css';

interface SpinnerProps {
    /** Delay in ms before showing spinner (prevents flicker on fast responses) */
    delay?: number;
}

export function Spinner({ delay = 200 }: SpinnerProps) {
    const [show, setShow] = useState(delay === 0);

    useEffect(() => {
        if (delay === 0) return;

        const timer = setTimeout(() => {
            setShow(true);
        }, delay);

        return () => clearTimeout(timer);
    }, [delay]);

    if (!show) return null;

    return (
        <div className="spinner-overlay" role="status" aria-label="Loading">
            <div className="spinner" />
        </div>
    );
}
