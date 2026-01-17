import { useState, useCallback } from 'react';
import './CopyButton.css';

interface CopyButtonProps {
    /** The text to copy to clipboard */
    text: string;
    /** Optional label to show on button */
    label?: string;
    /** Optional class name */
    className?: string;
}

export function CopyButton({ text, label = 'Copy', className = '' }: CopyButtonProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy text:', err);
        }
    }, [text]);

    return (
        <button
            type="button"
            className={`copy-button ${copied ? 'copy-button--copied' : ''} ${className}`}
            onClick={handleCopy}
            aria-label={copied ? 'Copied!' : `Copy ${label}`}
        >
            <span className="copy-button__icon">{copied ? '✓' : '📋'}</span>
            <span>{copied ? 'Copied!' : label}</span>
        </button>
    );
}
