import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getMessage } from '../../api/dadpass';
import { CopyButton } from '../../components/CopyButton/CopyButton';
import { Spinner } from '../../components/Spinner/Spinner';
import { ToastContainer, useToast } from '../../components/Toast/Toast';
import './ViewMessage.css';

const UNAVAILABLE_MESSAGE = 'Message is no longer available';

export function ViewMessage() {
    const { messageKey } = useParams<{ messageKey: string }>();
    const [message, setMessage] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isUnavailable, setIsUnavailable] = useState(false);
    const { toasts, showToast, dismissToast } = useToast();
    const hasFetched = useRef(false);

    useEffect(() => {
        if (!messageKey) {
            setIsUnavailable(true);
            setIsLoading(false);
            return;
        }

        // Prevent double-fetch in React StrictMode
        if (hasFetched.current) {
            return;
        }
        hasFetched.current = true;

        const fetchMessage = async () => {
            try {
                const response = await getMessage(messageKey);

                // Check if message is unavailable
                if (response.message === UNAVAILABLE_MESSAGE) {
                    setIsUnavailable(true);
                } else {
                    setMessage(response.message);
                }
            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Failed to retrieve message.';
                showToast('error', errorMessage);
                setIsUnavailable(true);
            } finally {
                setIsLoading(false);
            }
        };

        fetchMessage();
    }, [messageKey, showToast]);

    if (isLoading) {
        return (
            <div className="view-message">
                <Spinner delay={0} />
            </div>
        );
    }

    return (
        <div className="view-message">
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            <header className="view-message__header">
                <div className="view-message__logo">🔐</div>
                <h1 className="view-message__title">DadPass</h1>
            </header>

            <div className="view-message__card card">
                {isUnavailable ? (
                    <div className="view-message__unavailable">
                        <div className="view-message__unavailable-icon">🔒</div>
                        <h2 className="view-message__unavailable-title">Message Unavailable</h2>
                        <p className="view-message__unavailable-text">
                            This secret link has already been viewed or has expired.
                            <br />
                            Each link can only be accessed once.
                        </p>
                        <Link to="/" className="view-message__home-link">
                            ← Create a new secret
                        </Link>
                    </div>
                ) : (
                    <>
                        <div className="view-message__content">
                            <div className="view-message__label">Your Secret Message</div>
                            <p className="view-message__text">{message}</p>
                        </div>

                        <div className="view-message__actions">
                            <CopyButton text={message || ''} label="Copy Message" />
                        </div>

                        <p className="view-message__warning">
                            ⚠️ This message has been deleted and cannot be viewed again.
                        </p>

                        <Link
                            to="/"
                            className="view-message__home-link"
                            style={{ marginTop: 'var(--space-lg)', display: 'inline-flex' }}
                        >
                            ← Create a new secret
                        </Link>
                    </>
                )}
            </div>
        </div>
    );
}
