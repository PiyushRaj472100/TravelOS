import type { FC } from 'react';
import { Star, Wifi, Coffee, RefreshCw, MapPin, Hotel } from 'lucide-react';
import type { HotelResult } from '../../types';
import './HotelCard.css';

function Stars({ count }: { count?: number }) {
  if (!count) return null;
  const n = Math.min(Math.max(Math.round(count), 1), 5);
  return (
    <div className="hotel-stars" aria-label={`${n} stars`}>
      {Array.from({ length: 5 }, (_, i) => (
        <Star
          key={i}
          size={11}
          className={i < n ? 'star-filled' : 'star-empty'}
        />
      ))}
    </div>
  );
}

interface HotelCardProps {
  hotel: HotelResult;
  index: number;
  onPromptSend?: (prompt: string) => void;
}

const HotelCard: FC<HotelCardProps> = ({ hotel, index, onPromptSend }) => {
  const savings = hotel.savings && hotel.savings > 0;
  const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(hotel.name + ' ' + (hotel.address || ''))}`;
  const bookingUrl = `https://www.booking.com/searchresults.html?ss=${encodeURIComponent(hotel.name)}`;

  return (
    <article
      className="hotel-card card animate-slide-up"
      style={{ animationDelay: `${index * 60}ms` }}
      aria-label={`Hotel: ${hotel.name}`}
    >
      {/* Image */}
      <div className="hotel-image">
        {hotel.image ? (
          <img src={hotel.image} alt={hotel.name} loading="lazy" />
        ) : (
          <div className="hotel-image-placeholder">
            <Hotel size={28} />
          </div>
        )}
        {savings && (
          <span className="hotel-savings-badge">
            Save {hotel.currency} {hotel.savings?.toLocaleString()}
          </span>
        )}
      </div>

      {/* Body */}
      <div className="hotel-body">
        <div className="hotel-header">
          <div>
            <h3 className="hotel-name">{hotel.name}</h3>
            <Stars count={hotel.stars} />
          </div>
          <div className="hotel-price-block">
            {hotel.price ? (
              <>
                <span className="hotel-price">
                  {hotel.currency ?? ''} {hotel.price.toLocaleString()}
                </span>
                <span className="hotel-price-label">/ night (approx)</span>
              </>
            ) : null}
          </div>
        </div>

        {/* Location */}
        {(hotel.address || hotel.distance) && (
          <div className="hotel-location">
            <MapPin size={11} />
            <span>
              {hotel.address}
              {hotel.distance ? ` · ${hotel.distance.toFixed(1)} km from center` : ''}
            </span>
          </div>
        )}

        {/* Amenities */}
        <div className="hotel-amenities">
          {hotel.breakfast_included && (
            <span className="amenity-tag">
              <Coffee size={10} /> Breakfast Included
            </span>
          )}
          {hotel.refundable && (
            <span className="amenity-tag amenity-green">
              <RefreshCw size={10} /> Free Cancellation
            </span>
          )}
          {hotel.facilities?.slice(0, 3).map(f => (
            <span key={f} className="amenity-tag">
              <Wifi size={10} /> {f}
            </span>
          ))}
        </div>

        {/* Actions */}
        <div className="hotel-actions" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '12px' }}>
          {onPromptSend && (
            <button
              type="button"
              className="hotel-select-btn"
              onClick={() => onPromptSend(`Select hotel ${hotel.name}`)}
              style={{
                backgroundColor: '#3b82f6',
                color: '#fff',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              🏨 Select Hotel (Update Budget)
            </button>
          )}
          <a
            href={bookingUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="hotel-view-btn"
            style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem' }}
          >
            🔗 Booking Details
          </a>
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="hotel-view-btn"
            style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem' }}
          >
            <MapPin size={12} /> Google Maps
          </a>
        </div>

      </div>
    </article>
  );
};

export default HotelCard;
