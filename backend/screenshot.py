import base64
import os
import tempfile
from playwright.sync_api import sync_playwright

# Minimal Three.js OBJ viewer HTML template
VIEWER_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { margin: 0; background: #1a1a2e; }
canvas { display: block; width: 800px; height: 600px; }
</style>
</head>
<body>
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);

const camera = new THREE.PerspectiveCamera(50, 800 / 600, 0.1, 10000);
camera.position.set(50, 50, 50);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(800, 600);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);

const ambient = new THREE.AmbientLight(0x404040, 2);
scene.add(ambient);

const dir1 = new THREE.DirectionalLight(0xffffff, 2);
dir1.position.set(50, 50, 50);
scene.add(dir1);

const dir2 = new THREE.DirectionalLight(0xffffff, 1);
dir2.position.set(-50, -30, -50);
scene.add(dir2);

window.loadObj = function(objText) {
    const vertices = [];
    const normals = [];
    const faces = [];
    const lines = objText.split('\\n');

    for (const line of lines) {
        const parts = line.trim().split(/\\s+/);
        if (parts[0] === 'v' && parts.length >= 4) {
            vertices.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
        } else if (parts[0] === 'vn' && parts.length >= 4) {
            normals.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
        } else if (parts[0] === 'f' && parts.length >= 4) {
            const faceVerts = [];
            for (let i = 1; i < parts.length; i++) {
                const indices = parts[i].split('/');
                const vi = parseInt(indices[0]) - 1;
                faceVerts.push(vertices[vi * 3], vertices[vi * 3 + 1], vertices[vi * 3 + 2]);
            }
            faces.push(...faceVerts);
        }
    }

    if (faces.length === 0) return;

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(faces, 3));
    if (normals.length > 0) {
        geo.computeVertexNormals();
    }
    const mat = new THREE.MeshPhongMaterial({
        color: 0x4a90d9,
        side: THREE.DoubleSide,
        shininess: 80,
        flatShading: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    scene.add(mesh);

    const box = new THREE.Box3().setFromObject(mesh);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = camera.fov * (Math.PI / 180);
    let camDist = (maxDim / 2) / Math.tan(fov / 2);
    camDist *= 2.0;
    camera.position.set(center.x + camDist * 0.5, center.y + camDist * 0.5, center.z + camDist * 0.7);
    camera.lookAt(center);
    controls.target.copy(center);
    controls.update();

    window.__renderReady__ = true;
    renderer.render(scene, camera);
};

renderer.render(scene, camera);
</script>
</body>
</html>
"""


class Screenshotter:
    """Captures a screenshot of an OBJ model using headless Three.js + Playwright."""

    def __init__(self):
        self._html_path = None

    def capture(self, obj_text: str) -> str:
        """Render OBJ text in Three.js and return a base64-encoded PNG screenshot.

        Args:
            obj_text: The raw OBJ file content as a string.

        Returns:
            Base64-encoded PNG screenshot string (no data URI prefix).
        """
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
            f.write(VIEWER_HTML)
            f.flush()
            self._html_path = f.name

        file_url = f"file://{self._html_path}"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
                page = browser.new_page(viewport={"width": 800, "height": 600})
                page.goto(file_url, wait_until="networkidle")

                # Wait for Three.js module to define window.loadObj
                page.wait_for_function("typeof window.loadObj === 'function'", timeout=15000)

                # Inject OBJ data and render
                obj_b64 = base64.b64encode(obj_text.encode()).decode()
                page.evaluate(f"window.loadObj(atob('{obj_b64}'))")

                # Wait for render to complete
                page.wait_for_function("window.__renderReady__", timeout=10000)

                screenshot_bytes = page.screenshot(full_page=False)
                browser.close()

                return base64.b64encode(screenshot_bytes).decode("utf-8")
        finally:
            if self._html_path and os.path.exists(self._html_path):
                os.unlink(self._html_path)


screenshotter = Screenshotter()
