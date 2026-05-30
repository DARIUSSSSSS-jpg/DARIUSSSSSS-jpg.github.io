# Motion Control Suite v1.0

Professional Camera Motion Capture System for Blender

## Overview

Motion Control Suite is a professional system for controlling 3D camera motion in Blender using mobile device sensors (gyroscope and accelerometer).

**Key Features:**
- Real-time camera rotation control via DeviceOrientationEvent
- Position tracking via DeviceMotionEvent (accelerometer)
- Dynamic animation duration (1-99,999 frames)
- Professional Frutiger Aéro UI design
- WebSocket/HTTP connectivity
- Automatic keyframe insertion
- Advanced smoothing algorithms

---

## System Requirements

### Mobile Device
- iOS 13+ or Android 6+
- Modern browser (Chrome, Safari, Firefox)
- DeviceOrientationEvent and DeviceMotionEvent support
- Wi-Fi connection on same network as Blender PC

### Blender
- Blender 2.9 or newer
- Python 3.7+
- Socket library (built-in)

### Network
- PC and mobile on same local network
- Port 5005 available (configurable)

---

## Quick Start

### 1. Blender Setup

1. Open Blender
2. Switch to **Scripting** workspace
3. Click **New** to create new script
4. Copy entire contents of `blender_controller_v3.py`
5. Paste into Blender text editor
6. Press **Alt + P** to execute

**Verify execution** - You should see in console:
```
PROFESSIONAL CAMERA CONTROLLER v3
============================================================
Listening on port 5005
Status: READY
============================================================
```

### 2. Mobile Device Setup

#### Get Your PC IP Address
**Windows:**
```
cmd > ipconfig
Look for "IPv4 Address" under your Wi-Fi adapter (e.g., 192.168.1.100)
```

**Mac/Linux:**
```
Terminal > ifconfig | grep inet
Look for local IP (e.g., 192.168.1.100)
```

#### Open Interface on Mobile
1. On mobile, open any browser
2. Navigate to: `http://[YOUR_PC_IP]/motion-control.html`
   - Example: `http://192.168.1.100/motion-control.html`
3. Motion Control Suite interface should load

#### Grant Permissions (iOS 13+)
1. Go to **Settings**
2. **Privacy** > **Motion & Orientation**
3. Grant permissions to your browser

### 3. Connect and Start

1. On mobile interface, click **Motion Control Suite** (header)
2. Fill configuration modal:
   - **Blender Server IP**: Your PC IP (e.g., 192.168.1.100)
   - **Server Port**: 5005 (default)
   - **Connection Protocol**: WebSocket
3. Click **Connect**
4. Status indicator should turn **GREEN** (CONNECTED)

---

## Usage

### Basic Controls

#### Start Motion
- Click **Start Motion** button
- Mobile sensors begin streaming to Blender
- Camera in Blender moves in real-time with your device

#### Animation Duration
- Input field for total frame count
- Range: 1-99,999 frames
- Example: 240 frames = 10 seconds at 24fps
- Timeline auto-adjusts

#### Recording Range
- Slider to set which frames to record
- Start and end frame display
- Recording affects keyframe insertion range

#### Record Motion
- Click to start/stop recording
- Red "RECORDING" indicator appears
- Keyframes auto-insert in Blender timeline
- Click again to stop

#### Zoom Control
- Slider controls camera FOV
- Range: 1-200
- Real-time preview in Blender

#### Axis Lock
- Lock X, Y, Z individually
- Restricts rotation on locked axes
- Useful for controlled recordings

---

## Data Format

### JSON Payload

Mobile sends data approximately every 50ms:

```json
{
  "timestamp": 1234567890,
  "alpha": 45.5,
  "beta": 30.2,
  "gamma": -15.8,
  "gx": 0.25,
  "gy": 0.12,
  "gz": 9.81,
  "zoom": 50,
  "fov": 50,
  "isRecording": true,
  "frame": 45
}
```

**Field Descriptions:**
- `alpha`: Rotation around Z axis (0-360°)
- `beta`: Tilt forward/backward (-180 to 180°) - INVERTED
- `gamma`: Tilt left/right (-90 to 90°) - INVERTED
- `gx`, `gy`, `gz`: Acceleration in m/s²
- `zoom`: Zoom value (1-200)
- `fov`: Camera field of view
- `isRecording`: Recording status
- `frame`: Current frame number

---

## Troubleshooting

### Interface Won't Load
- Verify `motion-control.html` is in root directory
- Try accessing from PC browser first: `http://localhost/motion-control.html`
- Use updated browser (Chrome/Safari)

### Can't Connect to Blender
- Check port 5005 is available
- Windows: `netstat -an | findstr :5005`
- Try disabling firewall temporarily
- Verify Blender script is running

### Camera Won't Move
- Confirm active camera exists in Blender scene
- Go to **Scene Properties** > select camera
- Check mobile permissions (Settings > Privacy)
- Try moving device and check overlay data

### Inverted Movement
- X,Y axes are already corrected in interface
- If still inverted, manually invert in Blender

### High Latency
- Reduce animation duration
- Close other applications
- Check Wi-Fi signal strength
- Increase Smoothing slider

---

## Advanced Configuration

### Custom Port

Edit `blender_controller_v3.py` line ~20:
```python
self.port = 5005  # Change here
```

Then enter same port in mobile configuration.

### Smoothing Adjustment

In Blender World Properties panel:
- **Rotation Smoothing**: 0-1 (higher = smoother)
- **Position Smoothing**: 0-1 (higher = smoother)

### Position Scale

Edit `blender_controller_v3.py` line ~30:
```python
self.position_scale = 0.1  # Increase for more movement
```

---

## Use Cases

### Found Footage Cinema
1. Create scene in Blender
2. Position camera at starting location
3. Click **Record Motion**
4. Move mobile like physical camera
5. Keyframes auto-inserted
6. Review in timeline

### Dynamic Camera Animation
1. Set duration (e.g., 500 frames)
2. Move device slowly and smoothly
3. Records organic motion capture
4. Playback in timeline for review

### Axis-Locked Shots
1. Lock X and Y axes
2. Record only Z rotation (pan)
3. Useful for specific camera angles

---

## Technical Specifications

- **Protocol**: WebSocket (HTTP fallback)
- **Send Frequency**: ~20 Hz (50ms intervals)
- **Latency**: ~100-200ms (network dependent)
- **Max Duration**: 99,999 frames
- **Rotation Resolution**: 0.01°
- **Accelerometer Resolution**: 0.01 m/s²
- **Supported Browsers**: Chrome, Safari, Firefox, Edge

---

## File Structure

```
DARIUSSSSSS-jpg.github.io/
├── motion-control.html          # Web interface
├── blender_controller_v3.py     # Blender script
└── README.md                    # This file
```

---

## Support & Issues

**Check these first:**
1. Blender console (Window > Toggle System Console)
2. Browser console (F12 > Console tab)
3. Note exact error messages
4. Verify network connectivity

---

## Version History

- **v1.0** (May 2026) - Initial release
  - DeviceOrientationEvent support
  - DeviceMotionEvent support
  - Dynamic frame duration
  - Professional UI design
  - Blender 2.9+ compatible

---

**Motion Control Suite v1.0**
Professional Camera Motion Capture System for Blender
Created with Copilot AI Assistance
