import { useEffect, useRef } from 'react';

interface TokenData {
    symbol: string;
    signal: string;
    change: number;
    strategy: string;
    ltp: number;
}

interface NotificationServiceProps {
    tokens: TokenData[];
    tradingMode: string;
}

export const useNotificationService = ({ tokens, tradingMode }: NotificationServiceProps) => {
    const notifiedTokens = useRef<Set<string>>(new Set());

    useEffect(() => {
        // Request notification permission on first load
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }, []);

    useEffect(() => {
        if (!tokens || tokens.length === 0) return;
        if (Notification.permission !== 'granted') return;

        tokens.forEach(token => {
            // Only notify on BUY or SELL signals that we haven't notified about yet
            if ((token.signal === 'BUY' || token.signal === 'SELL') && !notifiedTokens.current.has(token.symbol)) {

                const changeDirection = token.change >= 0 ? '↑' : '↓';
                const changeColor = token.change >= 0 ? '🟢' : '🔴';

                // Different notifications based on trading mode
                if (tradingMode === 'AUTO_BUY' && token.signal === 'BUY') {
                    // Auto-buy notification (more urgent)
                    new Notification('🚀 Auto-Buy Executed!', {
                        body: `${changeColor} ${token.symbol}\n${changeDirection} ${Math.abs(token.change).toFixed(2)}% at ₹${token.ltp.toFixed(2)}\nStrategy: ${token.strategy}`,
                        icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="75" font-size="75">💰</text></svg>',
                        tag: token.symbol,
                        requireInteraction: true, // Stays until user dismisses
                    });
                } else if (tradingMode === 'NOTIFY_ONLY' || tradingMode === 'BOTH') {
                    // Notification-only mode
                    const title = token.signal === 'BUY' ? '📊 Buy Signal Detected' : '⚠️ Sell Signal Detected';

                    new Notification(title, {
                        body: `${changeColor} ${token.symbol}\n${changeDirection} ${Math.abs(token.change).toFixed(2)}% at ₹${token.ltp.toFixed(2)}\nStrategy: ${token.strategy}`,
                        icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="75" font-size="75">📈</text></svg>',
                        tag: token.symbol,
                    });
                }

                // Mark as notified to avoid spam
                notifiedTokens.current.add(token.symbol);

                // Clear notification tracking after 5 minutes
                setTimeout(() => {
                    notifiedTokens.current.delete(token.symbol);
                }, 5 * 60 * 1000);
            }
        });
    }, [tokens, tradingMode]);
};
