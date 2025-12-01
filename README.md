# Antigravity Trader

Automated trading desktop application with mStock integration.

## Project Structure

```
Zerodha10Candle/
├── backend/                    # FastAPI backend
│   ├── main.py                # Main API server
│   ├── models.py              # Data models
│   ├── mstock_client.py       # mStock API integration
│   └── backend_runner.py      # Standalone backend entry point
├── frontend/                   # React + Electron frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   │   ├── WelcomeSetup.tsx      # First-run setup wizard
│   │   │   ├── GlobalSettings.tsx    # Trading mode settings
│   │   │   ├── TokenGrid.tsx         # Live data grid
│   │   │   ├── StrategyPanel.tsx     # Strategy configuration
│   │   │   └── StrategyCard.tsx      # Individual strategy cards
│   │   ├── utils/
│   │   │   └── lotSizeHelper.ts      # Index-specific lot sizes
│   │   ├── App.tsx            # Main app component
│   │   └── main.tsx           # Entry point
│   ├── electron/              # Electron main process
│   └── package.json           # Dependencies
├── .env                       # mStock credentials (gitignored)
├── .env.example               # Credential template
├── build-all.bat              # Complete build script
└── requirements.txt           # Python dependencies

## Features

- ✅ First-run setup wizard (Microsoft Store-like)
- ✅ Real-time stock data grid with sparkline charts
- ✅ 3 trading modes: Notify Only, Auto Buy, Both
- ✅ Index-specific lot sizes (NIFTY, BANKNIFTY, SENSEX, etc.)
- ✅ Strategy configuration panel
- ✅ Desktop notifications
- ✅ Electron desktop app

## Development

### Backend
```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run electron:dev
```

## Building for Distribution

Run the automated build script:
```bash
build-all.bat
```

This creates: `frontend/dist/Antigravity Trader Setup.exe`

## Client Installation

1. Download the installer
2. Run it
3. Enter mStock credentials on first launch
4. Start trading!

## Environment Variables

Create `.env` from `.env.example`:
```env
MSTOCK_API_KEY=your_api_key
MSTOCK_USER_ID=your_user_id
MSTOCK_PASSWORD=your_password
```

## Tech Stack

- **Backend**: Python, FastAPI, mStock SDK
- **Frontend**: React, TypeScript, TailwindCSS
- **Desktop**: Electron
- **Charts**: Recharts
- **Packaging**: PyInstaller + electron-builder
