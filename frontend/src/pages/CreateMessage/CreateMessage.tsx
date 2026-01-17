import { useState, FormEvent } from 'react';
import { createMessage } from '../../api/dadpass';
import { CopyButton } from '../../components/CopyButton/CopyButton';
import { Spinner } from '../../components/Spinner/Spinner';
import { ToastContainer, useToast } from '../../components/Toast/Toast';
import './CreateMessage.css';

const MAX_CHARS = 256;
const SITE_URL = 'https://dadpass.com';

const TTL_OPTIONS = [
    { value: '15min', label: '15 Minutes' },
    { value: '1hour', label: '1 Hour' },
    { value: '1day', label: '1 Day' },
    { value: '5days', label: '5 Days' },
];

export function CreateMessage() {
    const [message, setMessage] = useState('');
    const [ttlOption, setTtlOption] = useState('1day');
    const [isLoading, setIsLoading] = useState(false);
    const [messageKey, setMessageKey] = useState<string | null>(null);
    const { toasts, showToast, dismissToast } = useToast();

    const charCount = message.length;
    const isOverLimit = charCount > MAX_CHARS;
    const isNearLimit = charCount > MAX_CHARS * 0.9;

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();

        if (!message.trim() || isOverLimit) {
            return;
        }

        setIsLoading(true);

        try {
            const response = await createMessage(message, ttlOption);
            setMessageKey(response.messageKey);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Something went wrong. Please try again.';
            showToast('error', errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const handleNewMessage = () => {
        setMessage('');
        setMessageKey(null);
        setTtlOption('1day');
    };

    const shareLink = messageKey ? `${SITE_URL}/${messageKey}` : '';

    return (
        <div className="create-message">
            {isLoading && <Spinner />}
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            <header className="create-message__header">
                <div className="create-message__logo">🔐</div>
                <h1 className="create-message__title">DadPass</h1>
                <p className="create-message__subtitle">Share secrets securely, one time only</p>
            </header>

            <div className="create-message__card card">
                {!messageKey ? (
                    <form onSubmit={handleSubmit}>
                        <div className="form-field">
                            <label htmlFor="message" className="form-label">
                                Your Secret Message
                            </label>
                            <div className="create-message__textarea-wrapper">
                                <textarea
                                    id="message"
                                    className="form-textarea create-message__textarea"
                                    placeholder="Enter a password, secret note, or any sensitive info..."
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                    maxLength={MAX_CHARS + 10} // Allow slight overtype to show error
                                    disabled={isLoading}
                                />
                                <span
                                    className={`create-message__char-count ${
                                        isOverLimit
                                            ? 'create-message__char-count--limit'
                                            : isNearLimit
                                            ? 'create-message__char-count--warning'
                                            : ''
                                    }`}
                                >
                                    {charCount}/{MAX_CHARS}
                                </span>
                            </div>
                        </div>

                        <div className="create-message__actions">
                            <div className="form-field" style={{ marginBottom: 0, flex: 1 }}>
                                <label htmlFor="ttl" className="form-label">
                                    Link Expires In
                                </label>
                                <select
                                    id="ttl"
                                    className="form-select"
                                    value={ttlOption}
                                    onChange={(e) => setTtlOption(e.target.value)}
                                    disabled={isLoading}
                                >
                                    {TTL_OPTIONS.map((option) => (
                                        <option key={option.value} value={option.value}>
                                            {option.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <button
                                type="submit"
                                className="btn btn-primary create-message__submit"
                                disabled={!message.trim() || isOverLimit || isLoading}
                            >
                                🔒 Create Secret Link
                            </button>
                        </div>
                    </form>
                ) : (
                    <div className="create-message__success">
                        <h2 className="create-message__success-title">✅ Link Created!</h2>
                        <p className="create-message__success-note">
                            This link can only be viewed <strong>once</strong>. After it's opened, the message is
                            deleted forever.
                        </p>
                        <div className="create-message__link-container">
                            <div className="create-message__link" role="textbox" aria-label="Share link">
                                {shareLink}
                            </div>
                            <CopyButton text={shareLink} label="Copy Link" />
                        </div>
                        <button
                            type="button"
                            className="btn btn-secondary create-message__new-button"
                            onClick={handleNewMessage}
                        >
                            Create Another
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
