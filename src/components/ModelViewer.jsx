import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, useProgress, Html } from '@react-three/drei'
import { useRef, useEffect, useState, Suspense } from 'react'
import { useFrame } from '@react-three/fiber'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader'
import * as THREE from 'three'

function Loader() {
    const { progress } = useProgress()
    return <Html center>{progress.toFixed(0)}% loaded</Html>
}

function OBJModel({ url, onLoaded }) {
    const [object, setObject] = useState(null)
    const meshRef = useRef()

    useEffect(() => {
        const loader = new OBJLoader()
        loader.load(
            url,
            (obj) => {
                // Center the object
                const box = new THREE.Box3().setFromObject(obj)
                const center = box.getCenter(new THREE.Vector3())
                obj.position.sub(center)

                // Scale to fit
                const size = box.getSize(new THREE.Vector3())
                const maxDim = Math.max(size.x, size.y, size.z)
                const scale = 4 / maxDim
                obj.scale.multiplyScalar(scale)

                setObject(obj)
                if (onLoaded) onLoaded(obj)
            },
            (xhr) => {
                console.log((xhr.loaded / xhr.total * 100) + '% loaded')
            },
            (error) => {
                console.error('Error loading OBJ:', error)
            }
        )
    }, [url, onLoaded])

    useFrame(() => {
        if (meshRef.current) {
            meshRef.current.rotation.y += 0.005
        }
    })

    if (!object) return null

    return <primitive ref={meshRef} object={object} />
}

function Simple3DModel({ model }) {
    const meshRef = useRef()

    useFrame((state) => {
        if (meshRef.current) {
            meshRef.current.rotation.y = state.clock.elapsedTime * 0.2
        }
    })

    if (!model || !model.dimensions) {
        return null
    }

    const { dimensions, subdivisions } = model

    return (
        <group>
            {/* Main model - simple material to prevent crashes */}
            <mesh
                ref={meshRef}
                position={[0, 0, 0]}
                castShadow
                receiveShadow
            >
                <boxGeometry
                    args={[
                        dimensions.x,
                        dimensions.y,
                        dimensions.z,
                        subdivisions.x,
                        subdivisions.y,
                        subdivisions.z
                    ]}
                />
                <meshStandardMaterial
                    color={model.quality === 'high' ? '#4a90e2' : '#7b68ee'}
                    metalness={0.2}
                    roughness={0.8}
                />
            </mesh>

            {/* Simple wireframe */}
            <mesh position={[0, 0, 0]}>
                <boxGeometry
                    args={[
                        dimensions.x,
                        dimensions.y,
                        dimensions.z,
                        subdivisions.x,
                        subdivisions.y,
                        subdivisions.z
                    ]}
                />
                <meshBasicMaterial
                    color="#ffffff"
                    wireframe
                    transparent
                    opacity={0.3}
                />
            </mesh>
        </group>
    )
}

function ModelViewer({ model, isProcessing, dimensions, photos, scanId, taskId }) {
    const [contextLost, setContextLost] = useState(false)
    const [retryCount, setRetryCount] = useState(0)
    const [realModelUrl, setRealModelUrl] = useState(null)
    const [modelStatus, setModelStatus] = useState('preview')
    const [processingStatus, setProcessingStatus] = useState('')
    const [taskProgress, setTaskProgress] = useState(null)

    const hasValidDimensions = dimensions.length && dimensions.width && dimensions.height
    const hasPhotos = photos && photos.length > 0

    // Poll task status for real-time updates
    useEffect(() => {
        if (taskId && isProcessing) {
            const checkTaskStatus = async () => {
                try {
                    const response = await fetch(`http://localhost:8000/task/${taskId}`)
                    const data = await response.json()
                    
                    if (data.status === 'SUCCESS') {
                        setProcessingStatus('Model ready!')
                        setModelStatus('loading')
                    } else if (data.status === 'FAILURE') {
                        setProcessingStatus('Processing failed')
                        setModelStatus('error')
                    } else if (data.status === 'PENDING') {
                        setProcessingStatus('Starting processing...')
                    } else if (data.info) {
                        // Extract status from task info
                        if (typeof data.info === 'string') {
                            setProcessingStatus(data.info)
                        } else if (data.info.current) {
                            setProcessingStatus(data.info.current)
                            if (data.info.total) {
                                setTaskProgress({
                                    current: data.info.current,
                                    total: data.info.total,
                                    percent: (data.info.current / data.info.total) * 100
                                })
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error checking task status:', error)
                }
            }

            checkTaskStatus()
            const interval = setInterval(checkTaskStatus, 2000)
            return () => clearInterval(interval)
        }
    }, [taskId, isProcessing])

    // Check for real model from backend
    useEffect(() => {
        if (scanId && !isProcessing) {
            const checkForModel = async () => {
                try {
                    const response = await fetch(`http://localhost:8000/model/${scanId}?format=obj`)
                    if (response.ok) {
                        const url = `http://localhost:8000/model/${scanId}?format=obj&t=${Date.now()}`
                        setRealModelUrl(url)
                        setModelStatus('ready')
                        setProcessingStatus('Loading real model...')
                    } else if (modelStatus !== 'preview') {
                        setModelStatus('processing')
                    }
                } catch (error) {
                    console.error('Error checking for model:', error)
                    if (modelStatus !== 'preview') {
                        setModelStatus('error')
                    }
                }
            }

            checkForModel()

            // Poll for model if still processing
            if (modelStatus === 'processing' || modelStatus === 'loading') {
                const interval = setInterval(checkForModel, 3000)
                return () => clearInterval(interval)
            }
        }
    }, [scanId, isProcessing, modelStatus])

    // Auto-retry on context loss
    useEffect(() => {
        if (contextLost && retryCount < 3) {
            const timer = setTimeout(() => {
                setContextLost(false)
                setRetryCount(prev => prev + 1)
                console.log(`Attempting WebGL recovery, attempt ${retryCount + 1}`)
            }, 1000)
            return () => clearTimeout(timer)
        }
    }, [contextLost, retryCount])

    if (contextLost && retryCount >= 3) {
        return (
            <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
                <div className="text-center">
                    <div className="text-red-600 mb-2">⚠️ WebGL Error</div>
                    <div className="text-sm text-gray-500 mb-4">
                        Please refresh the page to restore 3D rendering
                    </div>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                        Refresh Page
                    </button>
                </div>
            </div>
        )
    }

    if (!hasValidDimensions || !hasPhotos) {
        return (
            <div className="w-full h-96 bg-gray-50 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
                <div className="text-center text-gray-500">
                    <div className="text-6xl mb-4">📐</div>
                    <div className="text-lg mb-2">3D Model Preview</div>
                    <div className="text-sm">Upload photos and enter dimensions to generate model</div>
                </div>
            </div>
        )
    }

    return (
        <div className="w-full h-96 bg-gray-900 rounded-lg overflow-hidden relative">
            {/* Canvas with error boundary */}
            <Canvas
                camera={{ position: [8, 8, 8], fov: 50 }}
                onCreated={({ gl }) => {
                    gl.setSize(window.innerWidth, window.innerHeight, false)
                    console.log('Canvas created successfully')
                }}
                onError={(error) => {
                    console.error('Canvas error:', error)
                    setContextLost(true)
                }}
                fallback={
                    <div className="w-full h-full flex items-center justify-center bg-gray-800 text-white">
                        <div className="text-center">
                            <div className="text-red-400 mb-2">⚠️ WebGL Not Available</div>
                            <div className="text-sm">Your browser doesn't support 3D rendering</div>
                        </div>
                    </div>
                }
            >
                <Suspense fallback={<Loader />}>
                    {/* Lighting */}
                    <ambientLight intensity={0.6} />
                    <directionalLight position={[10, 10, 5]} intensity={0.5} castShadow />

                    {/* 3D Model - Real or Placeholder */}
                    {realModelUrl && modelStatus === 'ready' ? (
                        <OBJModel 
                            url={realModelUrl} 
                            onLoaded={() => setProcessingStatus('Real model loaded!')}
                        />
                    ) : (
                        model && <Simple3DModel model={model} />
                    )}

                    {/* Controls */}
                    <OrbitControls
                        enablePan={true}
                        enableZoom={true}
                        enableRotate={true}
                        autoRotate={false}
                    />
                </Suspense>
            </Canvas>

            {/* Overlay with model info */}
            <div className="absolute top-4 left-4 bg-black bg-opacity-50 text-white p-3 rounded-lg text-sm">
                <div className="font-semibold mb-1">🖱️ Drag to rotate • Scroll to zoom</div>
                <div className="text-gray-300">
                    📦 {dimensions.length}×{dimensions.width}×{dimensions.height} cm
                </div>
                {modelStatus === 'ready' && (
                    <div className="text-green-400 mt-1">✅ Real 3D model loaded</div>
                )}
                {modelStatus === 'preview' && (
                    <div className="text-yellow-400 mt-1">📦 Preview model (box)</div>
                )}
            </div>

            {/* Processing status overlay */}
            {isProcessing && (
                <div className="absolute top-4 right-4 bg-black bg-opacity-70 text-white p-3 rounded-lg text-sm max-w-xs">
                    <div className="font-semibold mb-2">🔄 COLMAP Processing</div>
                    <div className="text-gray-300">{processingStatus || 'Starting...'}</div>
                    {taskProgress && (
                        <div className="mt-2">
                            <div className="bg-gray-700 rounded-full h-2 overflow-hidden">
                                <div 
                                    className="bg-blue-500 h-full transition-all duration-300"
                                    style={{ width: `${taskProgress.percent}%` }}
                                />
                            </div>
                            <div className="text-xs mt-1">{taskProgress.percent.toFixed(0)}%</div>
                        </div>
                    )}
                </div>
            )}

            {/* Model stats */}
            {(model || realModelUrl) && (
                <div className="absolute bottom-4 right-4 bg-black bg-opacity-50 text-white p-3 rounded-lg text-sm">
                    <div className="font-semibold mb-1">3D Model Stats</div>
                    <div>Photos: {photos?.length || 0}</div>
                    <div>Quality: {model?.quality || 'processing'}</div>
                    <div>Status: {modelStatus}</div>
                    {scanId && modelStatus === 'ready' && (
                        <div className="mt-2">
                            <a
                                href={`http://localhost:8000/model/${scanId}?format=obj`}
                                download
                                className="text-blue-400 hover:text-blue-300 text-xs"
                            >
                                Download OBJ ↓
                            </a>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default ModelViewer