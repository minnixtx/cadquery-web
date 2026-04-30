import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

let scene, camera, renderer, controls, mesh;
let ready = false;

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

    try {
        controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.1;
    } catch (e) {
        console.warn('OrbitControls failed, running without controls', e);
    }

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
    ready = true;
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
    if (controls) controls.update();
    renderer.render(scene, camera);
}

function loadTjs(tjsBase64) {
    if (!tjsBase64 || !tjsBase64.trim()) return;

    if (!ready) {
        setTimeout(() => loadTjs(tjsBase64), 100);
        return;
    }

    if (mesh) {
        scene.remove(mesh);
        mesh.geometry.dispose();
        mesh.material.dispose();
        mesh = null;
    }

    const tjsText = atob(tjsBase64);
    const data = JSON.parse(tjsText);
    const verts = new Float32Array(data.vertices);
    const positions = [];

    for (let i = 0; i < data.faces.length; i += 4) {
        const a = data.faces[i + 1];
        const b = data.faces[i + 2];
        const c = data.faces[i + 3];
        positions.push(verts[a * 3], verts[a * 3 + 1], verts[a * 3 + 2]);
        positions.push(verts[b * 3], verts[b * 3 + 1], verts[b * 3 + 2]);
        positions.push(verts[c * 3], verts[c * 3 + 1], verts[c * 3 + 2]);
    }

    if (positions.length === 0) return;

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geo.computeVertexNormals();

    const mat = new THREE.MeshStandardMaterial({
        color: 0x4a90d9,
        side: THREE.DoubleSide,
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
    if (controls) {
        controls.target.copy(center);
        controls.update();
    }

    renderer.render(scene, camera);
}

window.loadTjs = loadTjs;
init();
animate();
