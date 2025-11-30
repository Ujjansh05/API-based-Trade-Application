const { app, BrowserWindow } = require('electron');
const path = require('path');

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
    app.quit();
}

function createWindow() {
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
    if (process.platform !== 'darwin') app.quit();
});
