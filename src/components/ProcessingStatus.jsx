import { AlertCircle, CheckCircle, Clock, Camera, Zap, Cpu, Layers } from 'lucide-react'

function ProcessingStatus({ isProcessing, step, progress, status }) {
    const getStepIcon = (step) => {
        if (step.includes('Analyzing photos')) return <Camera size={18} />
        if (step.includes('ZIP') || step.includes('metadata')) return <Layers size={18} />
        if (step.includes('Uploading')) return <Zap size={18} />
        if (step.includes('Extracting') || step.includes('point cloud') || step.includes('mesh')) return <Cpu size={18} />
        return <Clock size={18} />
    }

    const getProgressColor = (progress) => {
        if (progress < 30) return '#3b82f6' // blue
        if (progress < 70) return '#8b5cf6' // purple  
        if (progress < 90) return '#06b6d4' // cyan
        return '#10b981' // green
    }

    if (isProcessing) {
        return (
            <div className="status loading">
                <div className="flex items-center gap-3 mb-3">
                    {getStepIcon(step)}
                    <span className="font-medium">{step}</span>
                </div>

                <div className="progress-bar">
                    <div
                        className="progress-fill"
                        style={{
                            width: `${progress}%`,
                            background: `linear-gradient(90deg, ${getProgressColor(progress)}, ${getProgressColor(progress)}dd)`
                        }}
                    ></div>
                </div>

                <div className="flex justify-between items-center mt-2 text-sm">
                    <span>{progress}% complete</span>
                    <span className="text-gray-500">
                        {progress < 25 ? 'Initializing...' :
                            progress < 50 ? 'Processing photos...' :
                                progress < 75 ? 'Building 3D model...' :
                                    progress < 95 ? 'Finalizing...' : 'Almost done!'}
                    </span>
                </div>

                {/* Processing stages indicator */}
                <div className="flex justify-between mt-3 text-xs">
                    <div className={`flex flex-col items-center ${progress >= 15 ? 'text-blue-600' : 'text-gray-400'}`}>
                        <Camera size={12} />
                        <span>Analyze</span>
                    </div>
                    <div className={`flex flex-col items-center ${progress >= 35 ? 'text-purple-600' : 'text-gray-400'}`}>
                        <Layers size={12} />
                        <span>Bundle</span>
                    </div>
                    <div className={`flex flex-col items-center ${progress >= 50 ? 'text-cyan-600' : 'text-gray-400'}`}>
                        <Zap size={12} />
                        <span>Upload</span>
                    </div>
                    <div className={`flex flex-col items-center ${progress >= 85 ? 'text-green-600' : 'text-gray-400'}`}>
                        <Cpu size={12} />
                        <span>Reconstruct</span>
                    </div>
                    <div className={`flex flex-col items-center ${progress >= 100 ? 'text-green-600' : 'text-gray-400'}`}>
                        <CheckCircle size={12} />
                        <span>Complete</span>
                    </div>
                </div>
            </div>
        )
    }

    if (status) {
        const Icon = status.type === 'success' ? CheckCircle : AlertCircle

        return (
            <div className={`status ${status.type}`}>
                <div className="flex items-center gap-3">
                    <Icon size={18} />
                    <span>{status.message}</span>
                </div>

                {status.type === 'success' && (
                    <div className="mt-3 text-sm opacity-80">
                        💡 Tip: Upload more photos for higher quality 3D models
                    </div>
                )}
            </div>
        )
    }

    return null
}

export default ProcessingStatus 