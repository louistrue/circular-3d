import { useCallback } from 'react'
import { Ruler } from 'lucide-react'

function DimensionsForm({ dimensions, onDimensionsChange, disabled }) {
    const handleInputChange = useCallback((field, value) => {
        // Only allow positive numbers and decimals
        if (value === '' || /^\d*\.?\d*$/.test(value)) {
            const newDimensions = {
                ...dimensions,
                [field]: value
            }
            onDimensionsChange(newDimensions)
        }
    }, [dimensions, onDimensionsChange])

    return (
        <div>
            <div className="section-title text-lg mb-4">
                <Ruler size={20} />
                Object Dimensions (cm)
            </div>

            <div className="dimensions-form">
                <div className="form-group">
                    <label htmlFor="length">Length</label>
                    <input
                        id="length"
                        type="text"
                        placeholder="0.0"
                        value={dimensions.length}
                        onChange={(e) => handleInputChange('length', e.target.value)}
                        disabled={disabled}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="width">Width</label>
                    <input
                        id="width"
                        type="text"
                        placeholder="0.0"
                        value={dimensions.width}
                        onChange={(e) => handleInputChange('width', e.target.value)}
                        disabled={disabled}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="height">Height</label>
                    <input
                        id="height"
                        type="text"
                        placeholder="0.0"
                        value={dimensions.height}
                        onChange={(e) => handleInputChange('height', e.target.value)}
                        disabled={disabled}
                    />
                </div>
            </div>

            {dimensions.length && dimensions.width && dimensions.height && (
                <div className="mt-3 p-3 bg-blue-50 rounded-lg text-sm">
                    <div className="flex items-center gap-2 text-blue-700">
                        <Ruler size={16} />
                        <span className="font-medium">Calculated Volume:</span>
                        <span>
                            {(parseFloat(dimensions.length) * parseFloat(dimensions.width) * parseFloat(dimensions.height)).toFixed(2)} cm³
                        </span>
                    </div>
                </div>
            )}
        </div>
    )
}

export default DimensionsForm 