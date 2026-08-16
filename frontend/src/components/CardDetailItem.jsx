import { useState } from 'react';
import {
  getCardColors,
  getCardExpansion,
  getCardLevel,
  getCardTypes,
} from '../cardUtils';

export default function CardDetailItem({ card, index, selectedCardName }) {
  // Find the primary image index to load first, fallback to 0 if none exist
  const defaultImageIndex = Math.max(0, card.images?.findIndex(img => img.is_primary) || 0);
  
  const [activeImageIndex, setActiveImageIndex] = useState(defaultImageIndex);
  const [isFlipped, setIsFlipped] = useState(false);

  const cardId = card.cardNumber || card.id || `card-${index}`;
  const colors = getCardColors(card);
  const level = getCardLevel(card);
  const types = getCardTypes(card);
  const activeImage = card.images?.[activeImageIndex];

  return (
    <div className="digi-card-flip-container">
      <div className={`digi-card-inner ${isFlipped ? 'is-flipped' : ''}`}>
        
        {/* --- FRONT: THE IMAGE & CONTROLS --- */}
        <div className="digi-card-front">
          {activeImage ? (
            <img 
              src={activeImage.image_url} 
              alt={card.name?.english || selectedCardName} 
              className="digi-full-art"
            />
          ) : (
            <div className="digi-no-art">NO ARTWORK FOUND</div>
          )}

          {/* Overlay Controls */}
          <div className="digi-art-controls">
            <div className="art-dots">
              {card.images?.map((img, i) => (
                <button
                  key={img.id || i}
                  className={`art-dot ${i === activeImageIndex ? 'active' : ''} ${img.is_primary ? 'primary-dot' : ''}`}
                  onClick={() => setActiveImageIndex(i)}
                  title={img.variant_type}
                />
              ))}
            </div>
            
            <button 
              className="digi-flip-btn" 
              onClick={() => setIsFlipped(true)}
              title="View Card Data"
            >
              ⟳ INFO
            </button>
          </div>
        </div>

        {/* --- BACK: YOUR EXISTING TEXT DATA --- */}
        <div className="digi-card-back digi-card-item">
          <button 
            className="digi-flip-back-btn" 
            onClick={() => setIsFlipped(false)}
          >
            ⟲ RETURN TO ART
          </button>

          <div className="card-header" style={{ marginTop: '10px' }}>
            <span className="card-id">{cardId}</span>
            <span className="card-rarity">{card.rarity || 'N/A'}</span>
          </div>

          <h3 className="card-name">{card.name?.english || selectedCardName}</h3>

          <div className="card-details">
            <p><strong>EXPANSION:</strong> {getCardExpansion(card)}</p>
            <p><strong>COLOR:</strong> {colors.join(' / ')}</p>
            <p><strong>CARD TYPE:</strong> {card.cardType || 'N/A'}</p>
            {types.length > 0 && <p><strong>TYPE:</strong> {types.join(' / ')}</p>}
            {level !== null && <p><strong>LEVEL:</strong> Lv.{level}</p>}
            {card.playCost !== undefined && card.playCost !== null && card.playCost !== '-' && (
              <p><strong>PLAY COST:</strong> {card.playCost}</p>
            )}
            {card.dp && card.dp !== '-' && <p><strong>DP:</strong> {card.dp}</p>}
            {card.form && card.form !== '-' && <p><strong>FORM:</strong> {card.form}</p>}
            {card.attribute && card.attribute !== '-' && <p><strong>ATTRIBUTE:</strong> {card.attribute}</p>}
          </div>

          {card.effect && card.effect !== '-' && (
            <div className="card-effect">
              <strong>EFFECT</strong>
              <p>{card.effect}</p>
            </div>
          )}

          {card.digivolveEffect && card.digivolveEffect !== '-' && (
            <div className="card-effect">
              <strong>DIGIVOLUTION EFFECT</strong>
              <p>{card.digivolveEffect}</p>
            </div>
          )}

          {card.securityEffect && card.securityEffect !== '-' && (
            <div className="card-effect">
              <strong>SECURITY EFFECT</strong>
              <p>{card.securityEffect}</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}