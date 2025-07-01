import JSZip from 'jszip'

/**
 * Creates a ZIP file from an array of photos
 * @param {File[]} photos - Array of photo files
 * @returns {Promise<Blob>} - ZIP file as blob
 */
export async function createZipFile(photos) {
    if (!photos || photos.length === 0) {
        throw new Error('No photos provided for ZIP creation')
    }

    const zip = new JSZip()

    // Add each photo to the ZIP with indexed names
    photos.forEach((photo, index) => {
        const fileExtension = photo.name.split('.').pop() || 'jpg'
        const fileName = `${String(index + 1).padStart(3, '0')}_${photo.name}`
        zip.file(fileName, photo)
    })

    // Add metadata file
    const metadata = {
        totalPhotos: photos.length,
        createdAt: new Date().toISOString(),
        photos: photos.map((photo, index) => ({
            index: index + 1,
            originalName: photo.name,
            size: photo.size,
            type: photo.type,
            lastModified: photo.lastModified
        }))
    }

    zip.file('metadata.json', JSON.stringify(metadata, null, 2))

    try {
        // Generate ZIP as blob
        const zipBlob = await zip.generateAsync({
            type: "blob",
            compression: "DEFLATE",
            compressionOptions: {
                level: 6
            }
        })

        return zipBlob
    } catch (error) {
        throw new Error(`Failed to create ZIP file: ${error.message}`)
    }
}

/**
 * Formats file size in human readable format
 * @param {number} bytes - File size in bytes
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted file size
 */
export function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return "0 Bytes"

    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i]
}

/**
 * Downloads a blob as a file
 * @param {Blob} blob - The blob to download
 * @param {string} filename - The filename for download
 */
export function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
} 