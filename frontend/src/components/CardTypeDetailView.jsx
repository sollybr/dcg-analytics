import CardDetailItem from './CardDetailItem';

export default function CardTypeDetailView({
    selectedType,
    typeCards,
    cardsLoading,
    cardsError,
    totalCards,
    hasMoreType,
    observerTarget,
    onClose,
}) {
    return (
        <div className="digi-dashboard">
            <header className="digi-header">
                <h1>DIGIMON ANALYTICS OS</h1>

                <div className="digi-status">
                    <span className="indicator"></span>
                    <span>SYSTEM ONLINE</span>
                    <span style={{ opacity: 0.4 }}>|</span>
                    <span>
                        CARDS INDEXED: {totalCards || 0}
                    </span>
                </div>
            </header>

            <main className="digi-detail-view">
                <div className="digi-detail-header">
                    <button
                        className="digi-back-btn"
                        onClick={onClose}
                    >
                        &larr; BACK TO DASHBOARD
                    </button>

                    <h2>
                        CARDS OF TYPE:{' '}
                        <span style={{ color: '#00f3ff' }}>
                            {selectedType}
                        </span>
                    </h2>

                    {!cardsLoading && !cardsError && (
                        <p>
                            {typeCards.length} CARDS LOADED
                        </p>
                    )}
                </div>

                {cardsLoading && typeCards.length === 0 && (
                    <div className="digi-loader">
                        <div className="digi-spinner"></div>

                        <p className="digi-loading-text">
                            LOADING CARD DATA...
                        </p>
                    </div>
                )}

                {cardsError && (
                    <div className="digi-error-container">
                        <h2>CARD DATABASE OFFLINE</h2>
                        <p>{cardsError}</p>
                    </div>
                )}

                {!cardsLoading &&
                    !cardsError &&
                    typeCards.length === 0 && (
                        <div className="digi-error-container">
                            <h2>NO CARDS FOUND</h2>
                            <p>
                                No cards were returned for this type.
                            </p>
                        </div>
                    )}

                {!cardsLoading &&
                    !cardsError &&
                    typeCards.length > 0 && (
                        <div className="card-list-container">
                            {typeCards.map((card, index) => (
                                <CardDetailItem
                                    key={`${card.id}-${index}`}
                                    card={card}
                                    index={index}
                                    selectedCardName={card.name?.english}
                                />
                            ))}

                            {hasMoreType && (
                                <div
                                    ref={observerTarget}
                                    className="loading-indicator"
                                    style={{
                                        textAlign: 'center',
                                        padding: '20px',
                                        color: '#00f3ff',
                                    }}
                                >
                                    <p>SCANNING FOR MORE...</p>
                                </div>
                            )}

                            {!hasMoreType && (
                                <div
                                    className="end-of-results"
                                    style={{
                                        textAlign: 'center',
                                        padding: '20px',
                                        color: '#666',
                                    }}
                                >
                                    <p>END OF DATALOG.</p>
                                </div>
                            )}
                        </div>
                    )}
            </main>

            <footer className="digi-footer">
                {/* Footer is rendered by Dashboard. */}
            </footer>
        </div>
    );
}