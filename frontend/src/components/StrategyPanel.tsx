import { useState } from 'react';
import { StrategyCard } from './StrategyCard';

const DEFAULT_CONFIG = {
    mode: 'NOTIFY' as const,
    quantity: 1,
    stopLoss: 0,
    target: 0,
    trailingStop: false,
};

export const StrategyPanel = () => {
    const [strategies, setStrategies] = useState([
        { id: 'turning', title: 'Turning Candle Buy', description: 'Buy when Red → Green candle pattern detected.', active: false, config: { ...DEFAULT_CONFIG } },
        { id: 'jump', title: 'Live Price Jump', description: 'Buy when price jumps > 0.5% in 10 mins.', active: false, config: { ...DEFAULT_CONFIG } },
        { id: 'day_double', title: 'Day Low Double', description: 'Buy when price reaches Day Low + Low.', active: false, config: { ...DEFAULT_CONFIG } },
        { id: 'day_rise', title: 'Day Candle 5% Rise', description: 'Notify when Day Candle rises > 5%.', active: false, config: { ...DEFAULT_CONFIG } },
    ]);

    const toggleStrategy = (id: string, active: boolean) => {
        setStrategies(s => s.map(strat => strat.id === id ? { ...strat, active } : strat));
    };

    const updateConfig = (id: string, config: any) => {
        setStrategies(s => s.map(strat => strat.id === id ? { ...strat, config } : strat));
    };

    return (
        <div className="space-y-3">
            {strategies.map(strat => (
                <StrategyCard
                    key={strat.id}
                    title={strat.title}
                    description={strat.description}
                    isActive={strat.active}
                    onToggle={(active) => toggleStrategy(strat.id, active)}
                    config={strat.config}
                    onConfigChange={(cfg) => updateConfig(strat.id, cfg)}
                />
            ))}
        </div>
    );
};
