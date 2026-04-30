import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

let scene, camera, renderer, controls, mesh;

function init() {
    const container = document.getElementById('viewerContainer');
    const w = container.clientWidth || 800;
    const h = container.clientHeight || 600;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);

    camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 10000);
    camera.position.set(50, 50, 50);
    camera.lookAt(0, 0, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(w, h);
    container.appendChild(renderer.domElement);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;

    const ambient = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambient);

    const dir1 = new THREE.DirectionalLight(0xffffff, 2);
    dir1.position.set(50, 50, 50);
    scene.add(dir1);

    const dir2 = new THREE.DirectionalLight(0xffffff, 1);
    dir2.position.set(-50, -30, -50);
    scene.add(dir2);

    const grid = new THREE.GridHelper(100, 20, 0x30363d, 0x21262d);
    scene.add(grid);

    renderer.render(scene, camera);
    window.addEventListener('resize', onResize);
}

function onResize() {
    const container = document.getElementById('viewerContainer');
    if (!container || !camera || !renderer) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    animate();
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

function loadObj(objBase64) {
    if (!objBase64 || !objBase64.trim()) return;

    if (mesh) {
        scene.remove(mesh);
        mesh.geometry.dispose();
        mesh.material.dispose();
        mesh = null;
    }

    const objText = atob(objBase64);
    const { vertices, normals } = parseObj(objText);

    if (vertices.length === 0) return;

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    if (normals.length > 0) {
        geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
    } else {
        geo.computeVertexNormals();
    }

    const mat = new THREE.MeshStandardMaterial({
        color: 0x4a90d9,
        side: THREE.DoubleSide,
        shininess: 80,
        flatShading: false,
    });

    mesh = new THREE.Mesh(geo, mat);
    scene.add(mesh);

    const box = new THREE.Box3().setFromObject(mesh);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = camera.fov * (Math.PI / 180);
    const camDist = (maxDim / 2) / Math.tan(fov / 2) * 2.0;
    camera.position.set(center.x + camDist * 0.5, center.y + camDist * 0.5, center.z + camDist * 0.7);
    camera.lookAt(center);
    controls.target.copy(center);
    controls.update();

    renderer.render(scene, camera);
}

function parseObj(text) {
    const vPositions = [];
    const vNormals = [];
    const lines = text.split('\n');

    for (const line of lines) {
        const parts = line.trim().split(/\s+/);
        if (parts[0] === 'v' && parts.length >= 4) {
            vPositions.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
        } else if (parts[0] === 'vn' && parts.length >= 4) {
            vNormals.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
        }
    }

    const faceVerts = [];
    const faceNorms = [];
    const vertexSet = new Set();

    for (const line of lines) {
        const parts = line.trim().split(/\s+/);
        if (parts[0] !== 'f' || parts.length < 4) continue;

        const faceIndices = [];
        const faceNormRef = [];
        for (let i = 1; i < parts.length; i++) {
            const ref = parts[i].split('/');
            const vIdx = parseInt(ref[0]) - 1;
            const nIdx = ref[2] ? parseInt(ref[2]) - 1 : -1;
            faceIndices.push(vIdx);
            faceNormRef.push(nIdx);
        }

        for (let i = 1; i < faceIndices.length - 1; i++) {
            faceVerts.push(faceIndices[0], faceIndices[i], faceIndices[i + 1]);
            faceNorms.push(faceNormRef[0], faceNormRef[i], faceNormRef[i + 1]);
        }
    }

    const verts = [];
    const norms = [];
    for (let i = 0; i < faceVerts.length; i++) {
        const vi = faceVerts[i];
        if (!vertexSet.has(vi)) {
            vertexSet.add(vi);
        }
        verts.push(vPositions[vi * 3], vPositions[vi * 3 + 1], vPositions[vi * 3 + 2]);
        const ni = faceNorms[i];
        if (ni >= 0 && vNormals.length > 0) {
            norms.push(vNormals[ni * 3], vNormals[ni * 3 + 1], vNormals[ni * 3 + 2]);
        }
    }

    return { vertices: verts, normals: norms };
}

window.loadObj = loadObj;
init();
animate();
