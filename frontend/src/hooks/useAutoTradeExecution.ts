import { useEffect, useRef } from 'react';

interface TokenData {
    symbol: string;
    signal: string;
    ltp: number;
    strategy: string;
}

interface StrategyConfig {
    mode: 'AUTO' | 'NOTIFY';
    quantity: number;
    strategyName: string;
}

interface UseAutoTradeProps {
    tokens: TokenData[];
    strategies: { [key: string]: StrategyConfig };
}

export const useAutoTradeExecution = ({ tokens, strategies }: UseAutoTradeProps) => {
    const processedSignals = useRef<Set<string>>(new Set());

    useEffect(() => {
        if (!tokens || tokens.length === 0) return;

        tokens.forEach(token => {
            // Only process if there's a BUY or SELL signal
            if (token.signal !== 'BUY' && token.signal !== 'SELL') return;

            // Create unique key for this signal
            const signalKey = `${token.symbol}-${token.signal}-${Date.now()}`;

            // Check if we already processed this signal recently
            if (processedSignals.current.has(signalKey)) return;

            // Find matching strategy
            const matchingStrategy = Object.entries(strategies).find(
                ([_, config]) => token.strategy && config.strategyName === token.strategy
            );

            if (!matchingStrategy) return;

            const [, config] = matchingStrategy;

            // Only execute if Auto-Buy mode is enabled
            if (config.mode === 'AUTO') {
                console.log(`🚀 Auto-Trade Trigger: ${token.strategy} detected ${token.signal} signal for ${token.symbol}`);

                // Mark as processed
                processedSignals.current.add(signalKey);

                // Execute trade
                executeTrade({
                    symbol: token.symbol,
                    quantity: config.quantity,
                    order_type: token.signal,
                    strategy: token.strategy,
                    price: token.ltp
                });

                // Clear old processed signals after 5 minutes to allow re-triggering
                setTimeout(() => {
                    processedSignals.current.delete(signalKey);
                }, 5 * 60 * 1000);
            }
        });
    }, [tokens, strategies]);
};

// Execute trade API call
async function executeTrade(order: {
    symbol: string;
    quantity: number;
    order_type: string;
    strategy: string;
    price: number;
}) {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/execute-trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(order)
        });

        const result = await response.json();

        if (result.success) {
            console.log(`✅ Trade Executed: ${result.message}`);
            console.log(`Order ID: ${result.order_id}`);

            // Show desktop notification
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('🚀 Trade Executed!', {
                    body: `${order.order_type} ${order.quantity} ${order.symbol}\nStrategy: ${order.strategy}\nOrder ID: ${result.order_id}`,
                    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="75" font-size="75">💰</text></svg>',
                    requireInteraction: true
                });
            }
        } else {
            console.error(`❌ Trade Failed: ${result.message}`);

            // Show error notification
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('❌ Trade Failed', {
                    body: result.message,
                    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="75" font-size="75">⚠️</text></svg>'
                });
            }
        }
    } catch (error) {
        console.error('Trade execution error:', error);
    }
}
