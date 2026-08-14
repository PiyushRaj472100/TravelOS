import { useState, useRef, type FC, type KeyboardEvent } from 'react';
import { Send, Sparkles } from 'lucide-react';
import './ChatInput.css';

const SUGGESTIONS = [
  'Plan a 7-day trip to Japan for 2 people',
  'Find flights from Delhi to Tokyo',
  'Show me hotels in Kyoto',
  'What is the weather like in Tokyo?',
  'Build the full itinerary',
  'What is my estimated budget?',
];

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  showSuggestions: boolean;
}

const ChatInput: FC<ChatInputProps> = ({ onSend, isLoading, showSuggestions }) => {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const text = value.trim();
    if (!text || isLoading) return;
    onSend(text);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    // Auto-resize
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const handleSuggestion = (s: string) => {
    onSend(s);
  };

  return (
    <div className="chat-input-area">
      {/* Suggestions */}
      {showSuggestions && (
        <div className="chat-suggestions">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              className="suggestion-chip"
              onClick={() => handleSuggestion(s)}
              disabled={isLoading}
            >
              <Sparkles size={10} />
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="chat-input-row">
        <div className="chat-input-box">
          <textarea
            ref={textareaRef}
            id="chat-message-input"
            className="chat-textarea"
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask TravelOS anything about your trip…"
            rows={1}
            disabled={isLoading}
            aria-label="Chat message"
          />
          <button
            id="chat-send-btn"
            className={`chat-send-btn ${isLoading ? 'loading' : ''}`}
            onClick={handleSend}
            disabled={!value.trim() || isLoading}
            aria-label="Send message"
          >
            {isLoading ? (
              <div className="send-spinner" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </div>
        <p className="chat-input-hint">
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};

export default ChatInput;
