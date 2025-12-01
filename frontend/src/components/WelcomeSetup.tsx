import { useState } from 'react';
import { CheckCircle, Key, User, Lock } from 'lucide-react';

export const WelcomeSetup = ({ onComplete }: { onComplete: () => void }) => {
    const [step, setStep] = useState(1);
    const [credentials, setCredentials] = useState({
        apiKey: '',
        userId: '',
        password: '',
    });
    const [isConfiguring, setIsConfiguring] = useState(false);

    const saveCredentials = async () => {
        setIsConfiguring(true);
        try {
            // Save credentials to backend
            await fetch('http://127.0.0.1:8000/api/configure', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(credentials),
            });

            // Mark setup as complete in localStorage
            localStorage.setItem('setup_complete', 'true');

            setTimeout(() => {
                onComplete();
            }, 2000);
        } catch (err) {
            alert('Failed to save configuration. Please check if backend is running.');
            setIsConfiguring(false);
        }
    };

    return (
        <div className="h-screen w-screen bg-gradient-to-br from-blue-900 via-gray-900 to-purple-900 flex items-center justify-center">
            <div className="bg-gray-800 rounded-2xl shadow-2xl p-8 w-[500px]">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">
                        Welcome to Antigravity Trader
                    </h1>
                    <p className="text-gray-400">Let's get you set up in seconds</p>
                </div>

                {/* Progress Indicator */}
                <div className="flex items-center justify-center gap-2 mb-8">
                    <div className={`w-3 h-3 rounded-full ${step >= 1 ? 'bg-blue-500' : 'bg-gray-600'}`} />
                    <div className={`w-3 h-3 rounded-full ${step >= 2 ? 'bg-blue-500' : 'bg-gray-600'}`} />
                    <div className={`w-3 h-3 rounded-full ${step >= 3 ? 'bg-blue-500' : 'bg-gray-600'}`} />
                </div>

                {/* Step 1: Welcome */}
                {step === 1 && (
                    <div className="space-y-6">
                        <div className="text-center">
                            <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle size={40} className="text-white" />
                            </div>
                            <h2 className="text-xl font-bold text-white mb-2">
                                Automated Trading Made Simple
                            </h2>
                            <p className="text-gray-400">
                                Connect your mStock account and start trading with advanced strategies
                            </p>
                        </div>

                        <button
                            onClick={() => setStep(2)}
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition"
                        >
                            Get Started →
                        </button>
                    </div>
                )}

                {/* Step 2: Credentials */}
                {step === 2 && (
                    <div className="space-y-6">
                        <h2 className="text-xl font-bold text-white mb-4">
                            Enter Your mStock Credentials
                        </h2>

                        <div className="space-y-4">
                            <div>
                                <label className="text-gray-300 text-sm mb-2 block flex items-center gap-2">
                                    <Key size={16} /> API Key
                                </label>
                                <input
                                    type="text"
                                    value={credentials.apiKey}
                                    onChange={(e) => setCredentials({ ...credentials, apiKey: e.target.value })}
                                    className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Enter your mStock API Key"
                                />
                            </div>

                            <div>
                                <label className="text-gray-300 text-sm mb-2 block flex items-center gap-2">
                                    <User size={16} /> User ID
                                </label>
                                <input
                                    type="text"
                                    value={credentials.userId}
                                    onChange={(e) => setCredentials({ ...credentials, userId: e.target.value })}
                                    className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Enter your User ID"
                                />
                            </div>

                            <div>
                                <label className="text-gray-300 text-sm mb-2 block flex items-center gap-2">
                                    <Lock size={16} /> Password
                                </label>
                                <input
                                    type="password"
                                    value={credentials.password}
                                    onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                                    className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Enter your Password"
                                />
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setStep(1)}
                                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 rounded-lg transition"
                            >
                                ← Back
                            </button>
                            <button
                                onClick={() => setStep(3)}
                                disabled={!credentials.apiKey || !credentials.userId || !credentials.password}
                                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Continue →
                            </button>
                        </div>

                        <p className="text-xs text-gray-500 text-center">
                            🔒 Your credentials are stored securely and never shared
                        </p>
                    </div>
                )}

                {/* Step 3: Configuring */}
                {step === 3 && (
                    <div className="space-y-6 text-center">
                        {!isConfiguring ? (
                            <>
                                <div className="w-20 h-20 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <CheckCircle size={40} className="text-white" />
                                </div>
                                <h2 className="text-xl font-bold text-white mb-2">
                                    Ready to Configure
                                </h2>
                                <p className="text-gray-400">
                                    Click below to save your settings and start trading
                                </p>

                                <div className="flex gap-3">
                                    <button
                                        onClick={() => setStep(2)}
                                        className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 rounded-lg transition"
                                    >
                                        ← Back
                                    </button>
                                    <button
                                        onClick={saveCredentials}
                                        className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-lg transition"
                                    >
                                        Complete Setup ✓
                                    </button>
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="w-20 h-20 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                                <h2 className="text-xl font-bold text-white mb-2">
                                    Configuring Your Account...
                                </h2>
                                <p className="text-gray-400">
                                    Please wait while we set everything up
                                </p>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
