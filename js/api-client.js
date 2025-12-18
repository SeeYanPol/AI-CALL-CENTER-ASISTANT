/**
 * CallSim API Client
 * Handles communication with the Flask backend
 */

class CallSimAPI {
    constructor(baseUrl = 'http://localhost:5000/api', apiKey = null) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.sessionId = null;
        this.sessionToken = null;
    }

    /**
     * Set API credentials
     */
    setCredentials(apiKey) {
        this.apiKey = apiKey;
    }

    /**
     * Get default headers for API requests
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        if (this.sessionToken) {
            headers['X-Session-Token'] = this.sessionToken;
        }
        
        return headers;
    }

    /**
     * Check API health
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', message: error.message };
        }
    }

    /**
     * Start a new call session
     */
    async startSession(callerInfo = {}) {
        try {
            const response = await fetch(`${this.baseUrl}/session/start`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ caller_info: callerInfo })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.sessionId = data.session_id;
            this.sessionToken = data.token;
            
            return data;
        } catch (error) {
            console.error('Failed to start session:', error);
            throw error;
        }
    }

    /**
     * End the current call session
     */
    async endSession() {
        if (!this.sessionId) {
            return { status: 'no_session' };
        }

        try {
            const response = await fetch(`${this.baseUrl}/session/${this.sessionId}/end`, {
                method: 'POST',
                headers: this.getHeaders()
            });

            const data = await response.json();
            
            // Clear session data
            this.sessionId = null;
            this.sessionToken = null;
            
            return data;
        } catch (error) {
            console.error('Failed to end session:', error);
            throw error;
        }
    }

    /**
     * Send a chat message and get AI response
     */
    async sendMessage(message) {
        try {
            const response = await fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Failed to send message:', error);
            throw error;
        }
    }

    /**
     * Convert text to speech and play audio
     */
    async textToSpeech(text, lang = 'en') {
        try {
            const response = await fetch(`${this.baseUrl}/tts`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ text, lang })
            });

            if (!response.ok) {
                throw new Error(`TTS failed! status: ${response.status}`);
            }

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            return audioUrl;
        } catch (error) {
            console.error('TTS failed:', error);
            throw error;
        }
    }

    /**
     * Play TTS audio
     */
    async speak(text, lang = 'en') {
        try {
            const audioUrl = await this.textToSpeech(text, lang);
            const audio = new Audio(audioUrl);
            
            return new Promise((resolve, reject) => {
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                    resolve();
                };
                audio.onerror = (e) => {
                    URL.revokeObjectURL(audioUrl);
                    reject(e);
                };
                audio.play();
            });
        } catch (error) {
            // Fallback to Web Speech API
            console.warn('Server TTS failed, using browser TTS:', error);
            return this.speakBrowser(text, lang);
        }
    }

    /**
     * Browser-based TTS fallback
     */
    speakBrowser(text, lang = 'en') {
        return new Promise((resolve, reject) => {
            if (!('speechSynthesis' in window)) {
                reject(new Error('Speech synthesis not supported'));
                return;
            }

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang;
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            
            utterance.onend = resolve;
            utterance.onerror = reject;
            
            window.speechSynthesis.speak(utterance);
        });
    }

    /**
     * Get available TTS voices
     */
    async getVoices() {
        try {
            const response = await fetch(`${this.baseUrl}/tts/voices`, {
                headers: this.getHeaders()
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to get voices:', error);
            return { voices: [] };
        }
    }
}

// Speech Recognition helper
class SpeechRecognitionHelper {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.onResult = null;
        this.onError = null;
        this.onEnd = null;

        this.init();
    }

    init() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Speech recognition not supported in this browser');
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');
            
            const isFinal = event.results[event.results.length - 1].isFinal;
            
            if (this.onResult) {
                this.onResult(transcript, isFinal);
            }
        };

        this.recognition.onerror = (event) => {
            this.isListening = false;
            if (this.onError) {
                this.onError(event.error);
            }
        };

        this.recognition.onend = () => {
            this.isListening = false;
            if (this.onEnd) {
                this.onEnd();
            }
        };
    }

    isSupported() {
        return this.recognition !== null;
    }

    start() {
        if (!this.recognition) {
            console.error('Speech recognition not supported');
            return false;
        }

        try {
            this.recognition.start();
            this.isListening = true;
            return true;
        } catch (error) {
            console.error('Failed to start recognition:', error);
            return false;
        }
    }

    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        }
    }

    setLanguage(lang) {
        if (this.recognition) {
            this.recognition.lang = lang;
        }
    }
}

// Export for use in other files
window.CallSimAPI = CallSimAPI;
window.SpeechRecognitionHelper = SpeechRecognitionHelper;
