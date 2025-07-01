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

function OBJModel({ url }) {
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
            },
            (xhr) => {
                console.log((xhr.loaded / xhr.total * 100) + '% loaded')
            },
            (error) => {
                console.error('Error loading OBJ:', error)
            }
        )
    }, [url])

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

    console.log('Rendering simple 3D model:', { dimensions, subdivisions })

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

function ModelViewer({ model, isProcessing, dimensions, photos, scanId }) {
    const [contextLost, setContextLost] = useState(false)
    const [retryCount, setRetryCount] = useState(0)
    const [realModelUrl, setRealModelUrl] = useState(null)
    const [modelStatus, setModelStatus] = useState('loading')

    const hasValidDimensions = dimensions.length && dimensions.width && dimensions.height
    const hasPhotos = photos && photos.length > 0

    // Check for real model from backend
    useEffect(() => {
        if (scanId && !isProcessing) {
            const checkForModel = async () => {
                try {
                    const response = await fetch(`http://localhost:8000/model/${scanId}?format=obj`)
                    if (response.ok) {
                        setRealModelUrl(`http://localhost:8000/model/${scanId}?format=obj`)
                        setModelStatus('ready')
                    } else {
                        setModelStatus('processing')
                    }
                } catch (error) {
                    console.error('Error checking for model:', error)
                    setModelStatus('error')
                }
            }

            checkForModel()

            // Poll for model if still processing
            const interval = setInterval(checkForModel, 5000)
            return () => clearInterval(interval)
        }
    }, [scanId, isProcessing])

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

    if (isProcessing) {
        return (
            <div className="w-full h-96 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <div className="text-gray-600">Processing with COLMAP...</div>
                    <div className="text-sm text-gray-500 mt-2">Creating real 3D model from {photos?.length || 0} photos</div>
                    <div className="text-xs text-gray-400 mt-1">This may take a few minutes</div>
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
                        <OBJModel url={realModelUrl} />
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
            </div>

            {/* Model stats */}
            {model && (
                <div className="absolute bottom-4 right-4 bg-black bg-opacity-50 text-white p-3 rounded-lg text-sm">
                    <div className="font-semibold mb-1">3D Model Stats</div>
                    <div>Photos: {photos?.length || 0}</div>
                    <div>Quality: {model.quality}</div>
                    <div>Status: {modelStatus}</div>
                    {scanId && (
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