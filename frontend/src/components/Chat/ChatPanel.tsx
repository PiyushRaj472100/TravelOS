import { useEffect, useRef, type FC } from 'react';
import { Bot } from 'lucide-react';
import type { ChatMessage, AgentStatus } from '../../types';
import MessageBubble from './MessageBubble';
import AgentStatusFeed from './AgentStatusFeed';
import ChatInput from './ChatInput';
import './ChatPanel.css';

// ----------------------------------------------------------------
// Typing indicator
// ----------------------------------------------------------------
const TypingIndicator: FC = () => (
  <div className="typing-wrapper animate-fade-in">
    <div className="typing-avatar">
      <Bot size={14} />
    </div>
    <div className="typing-bubble">
      <span className="typing-dot" />
      <span className="typing-dot" />
      <span className="typing-dot" />
    </div>
  </div>
);

// ----------------------------------------------------------------
// Welcome screen (shown before any messages)
// ----------------------------------------------------------------
const WelcomeScreen: FC = () => (
  <div className="chat-welcome animate-fade-in">
    <div className="welcome-logo">
      <Bot size={32} />
    </div>
    <h2 className="welcome-title">How can I help you travel?</h2>
    <p className="welcome-subtitle">
      Tell me where you'd like to go, what you love doing, and I'll plan
      your perfect trip — flights, hotels, activities, itinerary and more.
    </p>
  </div>
);

// ----------------------------------------------------------------
// ChatPanel
// ----------------------------------------------------------------
interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
  latestStatuses: AgentStatus[];
  onSend: (text: string) => void;
  onRetry: () => void;
}

const ChatPanel: FC<ChatPanelProps> = ({
  messages,
  isLoading,
  latestStatuses,
  onSend,
  onRetry,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const isEmpty = messages.length === 0;

  // Scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-panel">
      {/* Messages */}
      <div className="chat-messages" role="log" aria-live="polite" aria-label="Conversation">
        {isEmpty && !isLoading && <WelcomeScreen />}

        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onRetry={msg.content.startsWith('⚠️') ? onRetry : undefined}
            onSend={onSend}
          />
        ))}

        {/* Agent status feed while loading */}
        {isLoading && (
          <AgentStatusFeed statuses={latestStatuses} isLoading={isLoading} />
        )}

        {/* Typing indicator */}
        {isLoading && <TypingIndicator />}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={onSend}
        isLoading={isLoading}
        showSuggestions={isEmpty && !isLoading}
      />
    </div>
  );
};

export default ChatPanel;
