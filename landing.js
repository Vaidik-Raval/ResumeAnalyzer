// Loading Screen
window.addEventListener('load', () => {
    const loadingScreen = document.querySelector('.loading-screen');
    loadingScreen.style.opacity = '0';
    setTimeout(() => {
        loadingScreen.style.display = 'none';
    }, 500);
});

// 3D Animation
let scene, camera, renderer, resume;
let mouseX = 0;
let mouseY = 0;
let targetX = 0;
let targetY = 0;

function init() {
    // Create scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f7fa);

    // Create camera
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 5;

    // Create renderer
    const canvas = document.getElementById('resume-canvas');
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    // Create resume geometry
    const geometry = new THREE.BoxGeometry(2, 3, 0.1);
    const material = new THREE.MeshPhongMaterial({
        color: 0x3498db,
        specular: 0x050505,
        shininess: 100,
    });
    resume = new THREE.Mesh(geometry, material);
    scene.add(resume);

    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 5, 5);
    scene.add(directionalLight);

    // Add event listeners
    window.addEventListener('resize', onWindowResize, false);
    window.addEventListener('mousemove', onMouseMove, false);
    window.addEventListener('touchmove', onTouchMove, false);

    // Start animation
    animate();
}

function onWindowResize() {
    const canvas = document.getElementById('resume-canvas');
    camera.aspect = canvas.clientWidth / canvas.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
}

function onMouseMove(event) {
    mouseX = (event.clientX - window.innerWidth / 2) / 100;
    mouseY = (event.clientY - window.innerHeight / 2) / 100;
}

function onTouchMove(event) {
    event.preventDefault();
    mouseX = (event.touches[0].clientX - window.innerWidth / 2) / 100;
    mouseY = (event.touches[0].clientY - window.innerHeight / 2) / 100;
}

function animate() {
    requestAnimationFrame(animate);

    // Smooth mouse movement
    targetX = mouseX;
    targetY = mouseY;

    // Rotate resume
    resume.rotation.y += (targetX - resume.rotation.y) * 0.05;
    resume.rotation.x += (targetY - resume.rotation.x) * 0.05;

    // Add floating animation
    resume.position.y = Math.sin(Date.now() * 0.001) * 0.1;

    renderer.render(scene, camera);
}

// Initialize 3D scene
init();

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Add fade-in animation to elements
document.querySelectorAll('.feature-card, .step').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
}); 