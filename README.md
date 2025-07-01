# Circular 3D Scanner - Web Prototype

A modern web application for uploading photos with dimensions to generate 3D models via circular scanning techniques.

## 🚀 Features

- **📸 Multi-Photo Upload**: Drag-and-drop or click to upload multiple photos
- **📏 Dimension Input**: Enter object dimensions (length × width × height)
- **📦 ZIP Bundling**: Automatically bundles photos and metadata into ZIP files
- **🌐 API Integration**: Seamless communication with FastAPI backend
- **🎨 3D Visualization**: Real-time 3D model preview using Three.js
- **📱 Responsive Design**: Modern UI that works on desktop and mobile
- **⚡ Real-time Progress**: Live upload and processing status

## 🛠️ Technology Stack

### Frontend
- **React 18** - Modern React with hooks and functional components
- **Vite** - Fast build tool and dev server
- **Three.js** + **@react-three/fiber** - 3D rendering and visualization
- **@react-three/drei** - Useful helpers for Three.js
- **JSZip** - Client-side ZIP file creation
- **Axios** - HTTP client for API communication
- **Lucide React** - Beautiful icons
- **CSS3** - Modern styling with gradients and animations

### Backend Integration
- Compatible with **FastAPI** backend
- RESTful API communication
- File upload with progress tracking
- CORS enabled for cross-origin requests

## 📁 Project Structure

```
circular-3d/
├── public/                 # Static assets
├── src/
│   ├── components/         # React components
│   │   ├── PhotoUpload.jsx     # Photo upload with drag-and-drop
│   │   ├── DimensionsForm.jsx  # Dimensions input form
│   │   ├── ModelViewer.jsx     # 3D model visualization
│   │   └── ProcessingStatus.jsx # Upload progress and status
│   ├── utils/              # Utility functions
│   │   ├── zipUtils.js         # ZIP creation and file handling
│   │   └── api.js              # API communication layer
│   ├── App.jsx             # Main application component
│   ├── main.jsx            # React entry point
│   └── index.css           # Global styles
├── package.json            # Dependencies and scripts
├── vite.config.js          # Vite configuration
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 16+ and npm
- **FastAPI backend** running on `http://localhost:8000`

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open browser** to `http://localhost:5173`

### Backend Setup

Ensure your FastAPI backend has these endpoints:

```python
# main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/")
async def upload_scan(
    zipfile: UploadFile = File(...),
    metadata: str = Form(...)
):
    # Process upload and return scan UUID
    return {"uuid": "scan-123", "status": "processing"}

@app.get("/download/{scan_id}")
async def download_scan(scan_id: str):
    # Return processed scan results
    pass
```

## 🎯 How to Use

1. **Upload Photos**: 
   - Drag and drop multiple photos or click to browse
   - Supports JPG, PNG, WEBP formats
   - Photos are validated and previewed

2. **Enter Dimensions**:
   - Input length, width, and height in centimeters
   - Volume is automatically calculated
   - Only positive numbers allowed

3. **Process Scan**:
   - Click "Process Scan" to start
   - Photos are bundled into ZIP with metadata
   - Real-time progress tracking
   - 3D model generation simulation

4. **View Results**:
   - Interactive 3D model preview
   - Download processed results
   - Scan details and metadata

## 🎨 Key Components

### PhotoUpload Component
- Drag-and-drop file handling
- Multiple file selection
- Image preview grid
- File validation and error handling

### DimensionsForm Component  
- Numeric input validation
- Real-time volume calculation
- Responsive form layout

### ModelViewer Component
- Three.js 3D rendering
- Interactive orbit controls
- Wireframe preview mode
- Dynamic model generation

### ProcessingStatus Component
- Progress bar animation
- Step-by-step status updates
- Success/error messaging

## 🔧 Configuration

### API Endpoint
Update the API base URL in `src/utils/api.js`:

```javascript
const API_BASE_URL = 'http://your-backend-url:8000'
```

### Upload Settings
Modify upload timeout and settings in `src/utils/api.js`:

```javascript
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
})
```

## 📦 Build for Production

```bash
npm run build
```

This creates an optimized build in the `dist/` folder ready for deployment.

## 🚀 Deployment

### Static Hosting (Netlify, Vercel)
1. Build the project: `npm run build`
2. Upload `dist/` folder to your hosting provider
3. Configure environment variables for API URL

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

## 🛠️ Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production  
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### File Upload Flow

1. **Client Side**: Photos → ZIP creation → FormData preparation
2. **API Call**: Axios upload with progress tracking
3. **Backend**: ZIP processing → 3D model generation
4. **Response**: Scan UUID → Status updates → Download links

## 🎯 Features in Detail

### 3D Model Generation
- Uses Three.js for WebGL rendering
- Responsive 3D viewport with orbit controls
- Preview mode shows wireframe based on dimensions
- Actual model rendering from uploaded photos

### File Handling
- Client-side ZIP creation using JSZip
- Metadata embedding with scan parameters
- Progress tracking for large uploads
- Error handling and retry logic

### User Experience
- Modern glass-morphism UI design
- Smooth animations and transitions
- Mobile-responsive layout
- Real-time feedback and validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the AGPL-3 License.

## 🔗 References

- [React Three Fiber Documentation](https://docs.pmnd.rs/react-three-fiber)
- [JSZip Documentation](https://stuk.github.io/jszip/)  
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [Vite Configuration](https://vitejs.dev/config/)

---

**Built with ❤️ by LT+ for a modern aproach to circular construction** 
