const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
    app.quit();
}

let backendProcess = null;

function startBackend() {
    const isDev = process.env.NODE_ENV === 'development';
    if (isDev) {
        console.log('In development mode, skipping backend spawn (assume running manually)');
        return;
    }

    // Path to backend executable
    // In production, it's in resources/backend/AntigravityBackend.exe
    const backendPath = path.join(process.resourcesPath, 'backend', 'AntigravityBackend.exe');
    console.log('Starting backend from:', backendPath);

    backendProcess = spawn(backendPath, [], {
        cwd: path.dirname(backendPath),
        stdio: 'ignore', // Detach stdio to prevent hanging
        windowsHide: true // Hide the console window
    });

    backendProcess.on('error', (err) => {
        console.error('Failed to start backend:', err);
    });

    backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });
}

function createWindow() {
    // Start backend
    startBackend();

    // Create the browser window.
    const mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        backgroundColor: '#020817', // Match the dark theme background
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: true,
            contextIsolation: false, // For simpler communication for now
        },
        autoHideMenuBar: true,
        icon: path.join(__dirname, '../public/icon.ico')
    });

    // Load the app.
    const isDev = process.env.NODE_ENV === 'development';
    console.log('App starting...');
    console.log('isDev:', isDev);
    console.log('NODE_ENV:', process.env.NODE_ENV);

    if (isDev) {
        console.log('Loading URL: http://127.0.0.1:5173');
        mainWindow.loadURL('http://127.0.0.1:5173');
        mainWindow.webContents.openDevTools();
    } else {
        const filePath = path.join(__dirname, '../dist/index.html');
        console.log('Loading file:', filePath);
        mainWindow.loadFile(filePath);
    }
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', function () {
    // Kill backend process
    if (backendProcess) {
        backendProcess.kill();
    }
    if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
    if (backendProcess) {
        backendProcess.kill();
    }
});
