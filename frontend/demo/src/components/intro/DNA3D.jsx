import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

/**
 * Generate 3D helix points
 */
function useHelix({
  turns = 2.0,
  length = 8.0,
  radius = 0.45,
  samples = 300,
  phase = 0,
}) {
  return useMemo(() => {
    const pts = [];
    for (let i = 0; i <= samples; i++) {
      const t = (i / samples) * Math.PI * 2 * turns + phase;
      const x = (i / samples - 0.5) * length;
      const y = Math.cos(t) * radius;
      const z = Math.sin(t) * radius;
      pts.push(new THREE.Vector3(x, y, z));
    }
    return pts;
  }, [turns, length, radius, samples, phase]);
}

/**
 * Smooth tube-based DNA strand for realistic 3D look
 */
function HelixStrandTube({ phase = 0, color = "#7cc7ff" }) {
  const pts = useHelix({ phase });

  const curve = new THREE.CatmullRomCurve3(pts);
  const tube = new THREE.TubeGeometry(curve, 400, 0.07, 20, false);

  return (
    <mesh geometry={tube}>
      <meshStandardMaterial
        color={color}
        metalness={0.75}
        roughness={0.18}
        emissive={color}
        emissiveIntensity={0.45}
        envMapIntensity={1.2}
      />
    </mesh>
  );
}

/**
 * Horizontal rungs between two strands
 */
function Rungs({ color = "#ffffff" }) {
  const a = useHelix({ phase: 0, samples: 26 });
  const b = useHelix({ phase: Math.PI, samples: 26 });

  return (
    <group>
      {a.map((pa, i) => {
        const pb = b[i];
        const mid = pa.clone().add(pb).multiplyScalar(0.5);
        const len = pa.distanceTo(pb);

        const geo = new THREE.CylinderGeometry(0.03, 0.03, len, 16);
        const mat = new THREE.MeshStandardMaterial({
          color,
          roughness: 0.25,
          metalness: 0.4,
          opacity: 0.9,
          transparent: true,
        });
        const m = new THREE.Mesh(geo, mat);
        m.position.copy(mid);
        m.lookAt(pb);
        m.rotateX(Math.PI / 2);
        return <primitive key={i} object={m} />;
      })}
    </group>
  );
}

/**
 * Entire rotating DNA group
 */
function MovingDNATube() {
  const g = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (!g.current) return;

    g.current.rotation.x = 0.25 + Math.sin(t * 0.4) * 0.06;
    g.current.rotation.y = Math.cos(t * 0.3) * 0.08;
    g.current.position.y = Math.sin(t * 0.6) * 0.15; // floating motion
  });

  return (
    <group ref={g} scale={2} position={[3, 0, 0]}>
      <HelixStrandTube phase={0} color="#7cc7ff" />
      <HelixStrandTube phase={Math.PI} color="#ff6ca8" />
      <Rungs />
    </group>
  );
}

/**
 * Full DNA component with lighting + environment + fog
 */
export default function DNA3D({
  width = "min(960px, 90vw)",
  height = "520px",
}) {
  return (
    <div style={{ width, height }}>
      <Canvas
        camera={{ position: [-4, 3, 4], fov: 45 }}
        gl={{ alpha: true }}
        style={{ background: "transparent" }}
      >
        {/* --- GLOBAL FOG FOR DEPTH (立体深度感核心) --- */}
        <fog attach="fog" args={["#000000", 5, 22]} />

        {/* --- LIGHTING SETUP --- */}
        <ambientLight intensity={0.6} />

        {/* Key light */}
        <directionalLight
          position={[4, 3, 4]}
          intensity={1.4}
          color="#bcd9ff"
        />

        {/* Rim light for 3D highlight */}
        <directionalLight
          position={[-3, -2, -4]}
          intensity={0.9}
          color="#d8a6ff"
        />

        {/* Fill light */}
        <directionalLight
          position={[0, 2, -3]}
          intensity={0.8}
          color="#88aaff"
        />

        {/* DNA */}
        <MovingDNATube />

        <OrbitControls enableZoom={false} enablePan={false} />
      </Canvas>
    </div>
  );
}
