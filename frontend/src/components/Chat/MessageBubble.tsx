import type { FC } from 'react';
import { Bot, User, RefreshCw, BookOpen, Sparkles } from 'lucide-react';
import type { ChatMessage } from '../../types';
import './MessageBubble.css';

// ----------------------------------------------------------------
// Markdown renderer — handles bold, italic, code, lists, headings,
// images (rendered as rich cards), and links.
// ----------------------------------------------------------------
function renderMarkdown(text: string): string {
  return (
    text
      // headings
      .replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>')
      .replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>')
      // inline bold
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // inline italic
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // inline code
      .replace(/`(.*?)`/g, '<code>$1</code>')
      // markdown images → rich card
      .replace(
        /!\[([^\]]*)\]\((https?:\/\/[^\)]+)\)/g,
        '<div class="place-img-card"><img src="$2" alt="$1" loading="lazy" onerror="this.style.display=\'none\'" /></div>',
      )
      // markdown links
      .replace(
        /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>',
      )
      // bullet lists
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      // line breaks (after all block-level replacements)
      .replace(/\n/g, '<br />')
  );
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ----------------------------------------------------------------
// Sources sub-component
// ----------------------------------------------------------------
interface SourcesProps {
  sources: ChatMessage['sources'];
}
const Sources: FC<SourcesProps> = ({ sources }) => {
  if (!sources?.length) return null;
  return (
    <details className="msg-sources">
      <summary className="msg-sources-toggle">
        <BookOpen size={11} />
        Sources ({sources.length})
      </summary>
      <ul className="msg-sources-list">
        {sources.map((s, i) => (
          <li key={i} className="msg-source-item">
            {s.source_url ? (
              <a href={s.source_url} target="_blank" rel="noopener noreferrer">
                {s.title ?? s.source ?? 'Source'}
              </a>
            ) : (
              <span>{s.title ?? s.source ?? 'Source'}</span>
            )}
            {s.category && <span className="msg-source-tag">{s.category}</span>}
          </li>
        ))}
      </ul>
    </details>
  );
};

// ----------------------------------------------------------------
// CTA Button — "Generate My Complete Itinerary"
// ----------------------------------------------------------------
interface CTAButtonProps {
  onSend?: (text: string) => void;
}
const CTAGenerateButton: FC<CTAButtonProps> = ({ onSend }) => (
  <div className="cta-generate-wrapper">
    <button
      id="cta-generate-itinerary-btn"
      className="cta-generate-btn"
      onClick={() => onSend?.('Build my full itinerary now')}
    >
      <Sparkles size={16} className="cta-sparkle-icon" />
      Generate My Complete Itinerary
    </button>
    <p className="cta-generate-hint">
      Day-by-day plan · Hotels · Activities · Full budget breakdown
    </p>
  </div>
);

// ----------------------------------------------------------------
// MessageBubble
// ----------------------------------------------------------------
interface MessageBubbleProps {
  message: ChatMessage;
  onRetry?: () => void;
  onSend?: (text: string) => void;
}

const MessageBubble: FC<MessageBubbleProps> = ({ message, onRetry, onSend }) => {
  const isUser = message.role === 'user';
  const isError = message.content.startsWith('⚠️');
  const showCTA = !isUser && message.cta_action === 'generate_itinerary';

  return (
    <div className={`msg-wrapper ${isUser ? 'msg-user' : 'msg-assistant'} animate-fade-in`}>
      {/* Avatar */}
      <div className={`msg-avatar ${isUser ? 'msg-avatar-user' : 'msg-avatar-ai'}`}>
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>

      {/* Bubble */}
      <div className={`msg-bubble ${isError ? 'msg-error' : ''}`}>
        {isUser ? (
          <p className="msg-text">{message.content}</p>
        ) : (
          <div
            className="msg-text msg-text-ai"
            // eslint-disable-next-line react/no-danger
            dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
          />
        )}

        {/* CTA button */}
        {showCTA && <CTAGenerateButton onSend={onSend} />}

        {/* Sources */}
        {!isUser && <Sources sources={message.sources} />}

        {/* Footer */}
        <div className="msg-footer">
          <span className="msg-time">{formatTime(message.timestamp)}</span>
          {isError && onRetry && (
            <button className="msg-retry" onClick={onRetry} title="Retry">
              <RefreshCw size={11} />
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
