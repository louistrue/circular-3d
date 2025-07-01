import { useCallback, useRef } from 'react'
import { Upload, X, Image } from 'lucide-react'
import { clsx } from 'clsx'

function PhotoUpload({ photos, onPhotosChange, disabled }) {
    const fileInputRef = useRef(null)

    const handleFileChange = useCallback((event) => {
        const files = Array.from(event.target.files)
        handleFiles(files)
    }, [])

    const handleFiles = useCallback((files) => {
        const imageFiles = files.filter(file => file.type.startsWith('image/'))

        if (imageFiles.length !== files.length) {
            alert('Please only upload image files')
        }

        if (imageFiles.length > 0) {
            const newPhotos = [...photos, ...imageFiles]
            onPhotosChange(newPhotos)
        }
    }, [photos, onPhotosChange])

    const handleDrop = useCallback((event) => {
        event.preventDefault()
        event.currentTarget.classList.remove('dragover')

        if (disabled) return

        const files = Array.from(event.dataTransfer.files)
        handleFiles(files)
    }, [handleFiles, disabled])

    const handleDragOver = useCallback((event) => {
        event.preventDefault()
        if (!disabled) {
            event.currentTarget.classList.add('dragover')
        }
    }, [disabled])

    const handleDragLeave = useCallback((event) => {
        event.preventDefault()
        event.currentTarget.classList.remove('dragover')
    }, [])

    const removePhoto = useCallback((index) => {
        const newPhotos = photos.filter((_, i) => i !== index)
        onPhotosChange(newPhotos)
    }, [photos, onPhotosChange])

    const openFileDialog = useCallback(() => {
        if (!disabled && fileInputRef.current) {
            fileInputRef.current.click()
        }
    }, [disabled])

    return (
        <div>
            <div
                className={clsx(
                    'file-upload',
                    disabled && 'opacity-50 cursor-not-allowed'
                )}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={openFileDialog}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleFileChange}
                    disabled={disabled}
                />

                <Upload className="upload-icon" />
                <div className="upload-text">
                    {photos.length === 0 ? 'Drop photos here or click to browse' : `${photos.length} photos selected`}
                </div>
                <div className="upload-subtext">
                    Supports: JPG, PNG, WEBP (multiple files)
                </div>
            </div>

            {photos.length > 0 && (
                <div className="photo-grid">
                    {photos.map((photo, index) => (
                        <div key={index} className="photo-item">
                            <img
                                src={URL.createObjectURL(photo)}
                                alt={`Photo ${index + 1}`}
                                loading="lazy"
                            />
                            <button
                                className="photo-remove"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    removePhoto(index)
                                }}
                                disabled={disabled}
                                title="Remove photo"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {photos.length > 0 && (
                <div className="text-sm text-gray-600 mt-3 flex items-center gap-2">
                    <Image size={16} />
                    {photos.length} photo{photos.length !== 1 ? 's' : ''} ready for processing
                </div>
            )}
        </div>
    )
}

export default PhotoUpload 