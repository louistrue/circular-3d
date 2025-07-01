import axios from 'axios'

// Configure axios defaults
const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 seconds timeout for uploads
})

/**
 * Uploads scan data (ZIP + metadata) to the FastAPI backend
 * @param {Blob} zipBlob - The ZIP file containing photos
 * @param {Object} metadata - Scan metadata (dimensions, etc.)
 * @returns {Promise<Object>} - Upload response with UUID
 */
export async function uploadScanData(zipBlob, metadata) {
    try {
        const formData = new FormData()

        // Add ZIP file
        formData.append('zipfile', new File([zipBlob], 'photos.zip', { type: 'application/zip' }))

        // Add metadata as JSON string
        formData.append('metadata', JSON.stringify(metadata))

        const response = await api.post('/upload/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                console.log(`Upload progress: ${percentCompleted}%`)
            }
        })

        return response.data
    } catch (error) {
        console.error('Upload error:', error)

        if (error.response) {
            // Server responded with error status
            throw new Error(`Upload failed: ${error.response.data?.detail || error.response.statusText}`)
        } else if (error.request) {
            // Request made but no response received
            throw new Error('Upload failed: No response from server. Please check if the backend is running.')
        } else {
            // Something else happened
            throw new Error(`Upload failed: ${error.message}`)
        }
    }
}

/**
 * Downloads processed scan results
 * @param {string} scanId - The scan UUID
 * @returns {Promise<Blob>} - Download blob
 */
export async function downloadScanResult(scanId) {
    try {
        const response = await api.get(`/download/${scanId}`, {
            responseType: 'blob'
        })

        return response.data
    } catch (error) {
        console.error('Download error:', error)
        throw new Error(`Download failed: ${error.message}`)
    }
}

/**
 * Gets scan status
 * @param {string} scanId - The scan UUID
 * @returns {Promise<Object>} - Scan status
 */
export async function getScanStatus(scanId) {
    try {
        const response = await api.get(`/status/${scanId}`)
        return response.data
    } catch (error) {
        console.error('Status check error:', error)
        throw new Error(`Status check failed: ${error.message}`)
    }
}

/**
 * Gets list of all scans
 * @returns {Promise<Array>} - List of scans
 */
export async function getScans() {
    try {
        const response = await api.get('/scans/')
        return response.data
    } catch (error) {
        console.error('Get scans error:', error)
        throw new Error(`Failed to get scans: ${error.message}`)
    }
}

/**
 * Health check for the API
 * @returns {Promise<Object>} - Health status
 */
export async function healthCheck() {
    try {
        const response = await api.get('/health')
        return response.data
    } catch (error) {
        console.error('Health check error:', error)
        throw new Error(`Health check failed: ${error.message}`)
    }
} 