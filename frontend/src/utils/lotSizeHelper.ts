// Utility to detect index type from symbol and return appropriate lot size
export function getLotSizeForSymbol(symbol: string, lotSizes: {
    nifty: number;
    banknifty: number;
    sensex: number;
    midcpnifty: number;
    finnifty: number;
    stock: number;
}): number {
    const upperSymbol = symbol.toUpperCase();

    // Check for index patterns
    if (upperSymbol.includes('NIFTY')) {
        if (upperSymbol.includes('BANK')) return lotSizes.banknifty;
        if (upperSymbol.includes('MIDCAP') || upperSymbol.includes('MIDCP')) return lotSizes.midcpnifty;
        if (upperSymbol.includes('FIN')) return lotSizes.finnifty;
        return lotSizes.nifty; // Default NIFTY
    }

    if (upperSymbol.includes('SENSEX')) return lotSizes.sensex;

    // Default to stock lot size for everything else
    return lotSizes.stock;
}

// Format lot size display
export function formatLotSize(symbol: string, quantity: number): string {
    return `${quantity} lot${quantity !== 1 ? 's' : ''}`;
}
