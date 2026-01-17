/* ===========================================
   DadPass API Client
   =========================================== */

const API_BASE_URL = 'https://twyukas531.execute-api.us-east-2.amazonaws.com';

export interface CreateMessageRequest {
    message: string;
    ttlOption: string;
}

export interface CreateMessageResponse {
    messageKey: string;
}

export interface GetMessageResponse {
    message: string;
}

export class ApiError extends Error {
    constructor(message: string, public statusCode?: number) {
        super(message);
        this.name = 'ApiError';
    }
}

/**
 * Create a new secret message
 */
export async function createMessage(message: string, ttlOption: string): Promise<CreateMessageResponse> {
    const response = await fetch(`${API_BASE_URL}/dad-pass`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message,
            ttlOption,
        } satisfies CreateMessageRequest),
    });

    if (!response.ok) {
        throw new ApiError('Failed to create message. Please try again.', response.status);
    }

    const data = await response.json();
    return data as CreateMessageResponse;
}

/**
 * Retrieve a secret message by its key
 * Note: The message is deleted after retrieval (one-time access)
 */
export async function getMessage(messageKey: string): Promise<GetMessageResponse> {
    const response = await fetch(`${API_BASE_URL}/dad-pass/${messageKey}`, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
        },
    });

    if (!response.ok) {
        throw new ApiError('Failed to retrieve message. Please try again.', response.status);
    }

    const data = await response.json();
    return data as GetMessageResponse;
}
