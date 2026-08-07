import {
  getCardColors,
  getCardExpansion,
  getCardLevel,
  getCardTypes,
} from '../cardUtils';

export default function CardDetailItem({
  card,
  index,
  selectedCardName,
}) {
  const cardId =
    card.cardNumber ||
    card.id ||
    `card-${index}`;

  const colors = getCardColors(card);
  const level = getCardLevel(card);
  const types = getCardTypes(card);

  return (
    <div
      key={`${cardId}-${index}`}
      className="digi-card-item"
    >
      <div className="card-header">
        <span className="card-id">
          {cardId}
        </span>

        <span className="card-rarity">
          {card.rarity || 'N/A'}
        </span>
      </div>

      <h3 className="card-name">
        {card.name?.english || selectedCardName}
      </h3>

      <div className="card-details">
        <p>
          <strong>EXPANSION:</strong>{' '}
          {getCardExpansion(card)}
        </p>

        <p>
          <strong>COLOR:</strong>{' '}
          {colors.join(' / ')}
        </p>

        <p>
          <strong>CARD TYPE:</strong>{' '}
          {card.cardType || 'N/A'}
        </p>

        {types.length > 0 && (
          <p>
            <strong>TYPE:</strong>{' '}
            {types.join(' / ')}
          </p>
        )}

        {level !== null && (
          <p>
            <strong>LEVEL:</strong> Lv.{level}
          </p>
        )}

        {card.playCost !== undefined &&
          card.playCost !== null &&
          card.playCost !== '-' && (
            <p>
              <strong>PLAY COST:</strong>{' '}
              {card.playCost}
            </p>
          )}

        {card.dp && card.dp !== '-' && (
          <p>
            <strong>DP:</strong> {card.dp}
          </p>
        )}

        {card.form && card.form !== '-' && (
          <p>
            <strong>FORM:</strong> {card.form}
          </p>
        )}

        {card.attribute && card.attribute !== '-' && (
          <p>
            <strong>ATTRIBUTE:</strong>{' '}
            {card.attribute}
          </p>
        )}
      </div>

      {card.effect && card.effect !== '-' && (
        <div className="card-effect">
          <strong>EFFECT</strong>
          <p>{card.effect}</p>
        </div>
      )}

      {card.digivolveEffect &&
        card.digivolveEffect !== '-' && (
          <div className="card-effect">
            <strong>DIGIVOLUTION EFFECT</strong>
            <p>{card.digivolveEffect}</p>
          </div>
        )}

      {card.securityEffect &&
        card.securityEffect !== '-' && (
          <div className="card-effect">
            <strong>SECURITY EFFECT</strong>
            <p>{card.securityEffect}</p>
          </div>
        )}
    </div>
  );
}