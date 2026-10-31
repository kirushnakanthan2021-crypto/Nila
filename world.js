import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/loaders/GLTFLoader.js";
const stage=document.getElementById("stage"),empty=document.getElementById("empty"),state=document.getElementById("state");
const scene=new THREE.Scene();scene.background=new THREE.Color(0x101a35);scene.fog=new THREE.Fog(0x101a35,8,18);
const camera=new THREE.PerspectiveCamera(34,stage.clientWidth/stage.clientHeight,.1,100);camera.position.set(0,1.55,5.4);
const renderer=new THREE.WebGLRenderer({antialias:false,alpha:false,powerPreference:"low-power"});renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25));renderer.setSize(stage.clientWidth,stage.clientHeight);renderer.outputColorSpace=THREE.SRGBColorSpace;stage.appendChild(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;controls.minDistance=2;controls.maxDistance=8;controls.target.set(0,1,0);
scene.add(new THREE.HemisphereLight(0xbacbff,0x25213c,2));
const key=new THREE.DirectionalLight(0xffe5d2,2.1);key.position.set(3,5,4);scene.add(key);
const fill=new THREE.PointLight(0x526fff,14,9);fill.position.set(-3,2.5,1);scene.add(fill);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(14,14),new THREE.MeshStandardMaterial({color:0x182442,roughness:.9}));floor.rotation.x=-Math.PI/2;floor.position.y=-.02;scene.add(floor);
const grid=new THREE.GridHelper(14,28,0x40568b,0x263657);grid.position.y=0;scene.add(grid);
let avatar=null,mixer=null,actions={},current=null,clock=new THREE.Clock(),turn=false;
function resize(){const w=stage.clientWidth,h=stage.clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25))}
new ResizeObserver(resize).observe(stage);
function play(name){if(!mixer||!actions[name]){state.textContent=avatar?"MODEL LOADED":"ADD AVATAR";return}if(current)current.fadeOut(.2);current=actions[name];current.reset().fadeIn(.2).play();state.textContent=name.toUpperCase()}
function loadFile(file){const url=URL.createObjectURL(file);state.textContent="LOADING";new GLTFLoader().load(url,g=>{if(avatar)scene.remove(avatar);avatar=g.scene;scene.add(avatar);const box=new THREE.Box3().setFromObject(avatar),size=box.getSize(new THREE.Vector3()),center=box.getCenter(new THREE.Vector3());avatar.position.x-=center.x;avatar.position.z-=center.z;avatar.position.y-=box.min.y;const scale=2.15/Math.max(size.y,.01);avatar.scale.setScalar(scale);mixer=new THREE.AnimationMixer(avatar);actions={};g.animations.forEach((clip,i)=>{const n=clip.name.toLowerCase();const k=n.includes("walk")?"walk":n.includes("dance")?"dance":n.includes("wave")?"wave":"idle";if(!actions[k])actions[k]=mixer.clipAction(clip)});empty.style.display="none";document.getElementById("model-note").textContent="Avatar loaded locally. Available animations: "+(Object.keys(actions).join(", ")||"No animation clips found; load a model with embedded animations.");state.textContent="AVATAR READY";play(actions.idle?"idle":Object.keys(actions)[0]);URL.revokeObjectURL(url)},undefined,e=>{state.textContent="LOAD ERROR";document.getElementById("model-note").textContent="Could not load this model. Try a .glb file with embedded textures." ;URL.revokeObjectURL(url);console.error(e)})}
document.getElementById("model").addEventListener("change",e=>{const f=e.target.files?.[0];if(f)loadFile(f)});
document.querySelectorAll("[data-action]").forEach(b=>b.addEventListener("click",()=>play(b.dataset.action)));
document.getElementById("rotate").addEventListener("click",()=>{turn=!turn;controls.autoRotate=turn;controls.autoRotateSpeed=1.1});
document.getElementById("reset").addEventListener("click",()=>{camera.position.set(0,1.55,5.4);controls.target.set(0,1,0);controls.update()});
document.getElementById("smile").addEventListener("click",()=>{if(!avatar)return alert("Load Nila's humanoid model with facial blendshapes first.");let found=0;avatar.traverse(o=>{if(o.morphTargetDictionary&&o.morphTargetInfluences){for(const [n,i] of Object.entries(o.morphTargetDictionary)){if(/smile/i.test(n)){o.morphTargetInfluences[i]=.8;found++}}}});if(!found)alert("This model has no smile blendshape. Choose a face-rigged avatar.")});
document.getElementById("speak").addEventListener("click",()=>{if(!("speechSynthesis"in window)){document.getElementById("voice-note").textContent="Speech synthesis is not supported in this browser.";return}const u=new SpeechSynthesisUtterance("Vanakkam chellam. Naan Nila.");u.lang="en-US";speechSynthesis.cancel();speechSynthesis.speak(u)});
function frame(){requestAnimationFrame(frame);const dt=Math.min(clock.getDelta(),.05);if(mixer)mixer.update(dt);controls.update();renderer.render(scene,camera)}frame();
window.addEventListener("pagehide",()=>{renderer.dispose();if(mixer)mixer.stopAllAction()});
