import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

/**
 * Custom hook to generate the 3D coordinates of a helix curve.
 * - turns: how many rotations the helix makes
 * - length: the total length of the helix
 * - radius: radius of the helix spiral
 * - samples: number of points used to construct the curve
 * - phase: horizontal shift to create a second strand
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
 * A single strand of the DNA helix using instanced spheres.
 * We use instancing to render many small spheres efficiently.
 * The animation gives a subtle "breathing" motion to the helix.
 */
function HelixStrand({ phase = 0, color = "#ffffff" }) {
  const pts = useHelix({ phase });
  const inst = useRef();
  const o = new THREE.Object3D();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i];

      // Slight pulsating motion along y and z
      o.position.set(
        p.x,
        p.y * (1 + 0.02 * Math.sin(t + i * 0.15)),
        p.z * (1 + 0.02 * Math.cos(t + i * 0.15))
      );

      // Small scale pulsation for each sphere
      const s = 0.05 + 0.01 * Math.sin(i * 0.25 + t);
      o.scale.setScalar(s);

      // Apply transformation to the instanced mesh
      o.updateMatrix();
      inst.current.setMatrixAt(i, o.matrix);
    }
    inst.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={inst} args={[null, null, pts.length]}>
      <sphereGeometry args={[1, 12, 12]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.55}
        transparent
        opacity={0.95}
        roughness={0.15}
        metalness={0.35}
      />
    </instancedMesh>
  );
}

/**
 * Creates the horizontal rungs (ladder steps) between the two DNA strands.
 * Uses cylinders positioned and rotated between paired points.
 */
function Rungs({ color = "#ffffff" }) {
  const a = useHelix({ phase: 0, samples: 26 });
  const b = useHelix({ phase: Math.PI, samples: 26 });
  const mat = new THREE.MeshStandardMaterial({
    color,
    transparent: true,
    opacity: 0.6,
  });

  return (
    <group>
      {a.map((pa, i) => {
        const pb = b[i];
        const mid = pa.clone().add(pb).multiplyScalar(0.5);
        const len = pa.distanceTo(pb);

        // Create a cylinder between two points
        const geo = new THREE.CylinderGeometry(0.01, 0.01, len, 8);
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
 * Rotates and animates the entire DNA structure over time.
 * This gives the DNA a dynamic, floating feel.
 */
function MovingDNA() {
  const g = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (!g.current) return;

    // Gentle oscillation of the DNA
    g.current.rotation.x = 0.3 + Math.sin(t * 0.4) * 0.05;
    g.current.rotation.y = Math.cos(t * 0.3) * 0.06;
  });

  return (
    <group ref={g} scale={2} position={[3, 0, 0]}>
      <HelixStrand phase={0} />
      <HelixStrand phase={Math.PI} />
      <Rungs />
    </group>
  );
}

/**
 * Main DNA3D component:
 * - Sets up the Three.js scene using @react-three/fiber
 * - Adds lighting and controls
 * - Renders the MovingDNA component as the centerpiece
 */
export default function DNA3D({
  width = "min(960px, 90vw)",
  height = "500px",
}) {
  return (
    <div style={{ width, height }}>
      <Canvas
        camera={{ position: [-4, 3, 4], fov: 45 }}
        gl={{ alpha: true }}
        style={{ background: "transparent" }}
      >
        {/* Ambient and directional lighting for soft highlights */}
        <ambientLight intensity={0.9} />
        <directionalLight position={[2, 2, 2]} intensity={1.2} />

        {/* Rotating DNA */}
        <MovingDNA />

        {/* Disable zoom/pan for a fixed camera experience */}
        <OrbitControls enableZoom={false} enablePan={false} />
      </Canvas>
    </div>
  );
}
