/**
 * Sa bàn 3D Lumi Hanoi — interactive massing model of the nine towers.
 *
 * The layout is a massing study traced from the project masterplan (mặt bằng
 * tổng thể) held in this repository. Tower count, tower grouping, floor counts,
 * floor-plan group counts and amenity names come from the verified project
 * documents already published on this site. Footprint sizes and landscape
 * shapes are indicative: the model is a reading aid, not survey data.
 *
 * Local plan frame used throughout:
 *   +X = tower long axis, pointing ENE (azimuth ≈ 56°)
 *   +Z = across the rows, pointing SSE (azimuth ≈ 146°)
 *   1 unit = 1 metre.
 */
import * as THREE from "three";

const FLOOR_H = 3.25;   // typical floor-to-floor used for the massing
const GROUND_H = 5.2;   // taller ground/lobby level
const PODIUM_H = 7.4;

/**
 * Facade tones follow the "Thiết kế mặt đứng" palette in the project brochure —
 * a charcoal glass field behind a light frame, with the second tone changing per
 * building group (stone, copper, bronze). Which swatch belongs to which tower is
 * not stated in the documents, so the mapping here is indicative.
 */
const ZONES = {
  signature: { name: "Lumi Signature", frame: 0xbdb3a1, chip: "#9c7951" },
  prestige: { name: "Lumi Prestige", frame: 0xa8703f, chip: "#705335" },
  elite: { name: "Lumi Elite", frame: 0x8a7358, chip: "#41565a" }
};

/** seg = [centreX, centreZ, lengthX, lengthZ] */
const TOWERS = [
  {
    id: "S1", name: "Signature 1", zone: "signature", floors: 35, plans: 8,
    href: "/mat-bang-lumi-hanoi/lumi-signature/s1/", row: "Khu Sole — dãy phía Đông",
    segs: [[-8, -16, 33, 21], [24, -7, 33, 21]]
  },
  {
    id: "S2", name: "Signature 2", zone: "signature", floors: 35, plans: 8,
    href: "/mat-bang-lumi-hanoi/lumi-signature/s2/", row: "Khu Sole — dãy phía Đông",
    segs: [[-6.6, 22.6, 33, 21], [24.4, 31.6, 33, 21]]
  },
  {
    id: "S3", name: "Signature 3", zone: "signature", floors: 35, plans: 8,
    href: "/mat-bang-lumi-hanoi/lumi-signature/s3/", row: "Khu Sole — dãy phía Đông",
    segs: [[-6.5, 65.7, 33, 21], [25.1, 74.7, 33, 21]]
  },
  {
    id: "S5", name: "Signature 5", zone: "signature", floors: 34, plans: 8,
    href: "/mat-bang-lumi-hanoi/lumi-signature/s5/", row: "Khu Luna — dãy phía Tây",
    segs: [[-85.6, 28.6, 31, 21], [-55.6, 37.6, 31, 21]]
  },
  {
    id: "S6", name: "Signature 6", zone: "signature", floors: 35, plans: 12,
    href: "/mat-bang-lumi-hanoi/lumi-signature/s6/", row: "Khu Luna — dãy phía Tây",
    segs: [[-109.1, -16.2, 49, 21], [-62.1, -7.2, 49, 21]]
  },
  {
    id: "P1", name: "Prestige 1", zone: "prestige", floors: 30, plans: 5, code: "L30.1",
    href: "/mat-bang-lumi-hanoi/lumi-prestige/p1/", row: "Cụm Prestige — phía Tây Bắc",
    segs: [[-97.4, -135.6, 43, 22], [-116.7, -112.6, 22, 44]]
  },
  {
    id: "P2", name: "Prestige 2", zone: "prestige", floors: 30, plans: 5, code: "L30M.1",
    href: "/mat-bang-lumi-hanoi/lumi-prestige/p2/", row: "Cụm Prestige — phía Tây Bắc",
    segs: [[-52.7, -119.5, 22, 36], [-66.9, -104.8, 30, 22]]
  },
  {
    id: "E1", name: "Elite 1", zone: "elite", floors: 29, plans: 5, code: "Z29M.1",
    href: "/mat-bang-lumi-hanoi/lumi-elite/e1/", row: "Cụm Elite — phía Đông Bắc",
    segs: [[-2, -104, 30, 21], [28, -94, 30, 21]]
  },
  {
    id: "E2", name: "Elite 2", zone: "elite", floors: 29, plans: 6, code: "Z29.1",
    href: "/mat-bang-lumi-hanoi/lumi-elite/e2/", row: "Cụm Elite — phía Đông Bắc",
    segs: [[-4, -50, 30, 21], [26, -59, 30, 21]]
  }
];

/** Amenity graphics on the ground plane. `kind` drives how each one is drawn. */
const AMENITIES = [
  { name: "Bể bơi Resort Sole", kind: "pool", x: -4, z: 51, w: 36, d: 15 },
  { name: "Bể bơi Cầu Vồng & sân chơi nước", kind: "pool", x: -8, z: 8, w: 30, d: 17 },
  { name: "Bể bơi Spa Luna", kind: "pool", x: -71, z: 15, w: 26, d: 14 },
  { name: "Hồ bơi Lấp Lánh & bể Jacuzzi", kind: "pool", x: -52, z: 15, w: 15, d: 11 },
  { name: "Bể bơi Aurora 50 m", kind: "pool", x: -62, z: -78, w: 50, d: 12 },
  { name: "Bể bơi khu thể thao", kind: "pool", x: -14, z: 86, w: 20, d: 12 },
  { name: "Sân tennis khu Sole", kind: "court", x: 7, z: 93, w: 34, d: 17 },
  { name: "Sân thể thao đa năng", kind: "court", x: -58, z: 55, w: 30, d: 18 },
  { name: "Sân tennis khu Prestige", kind: "court", x: -102, z: -72, w: 30, d: 16 },
  { name: "Sân tennis khu Elite", kind: "court", x: -57, z: -54, w: 30, d: 16 },
  { name: "Công viên trung tâm & Rừng Khám Phá", kind: "green", x: -38, z: 32, w: 34, d: 108 },
  { name: "Vườn cảnh quan Prestige – Elite", kind: "green", x: -26, z: -96, w: 30, d: 46 },
  { name: "Rạp chiếu phim ngoài trời", kind: "spot", x: -33, z: -18 },
  { name: "Công viên thú cưng", kind: "spot", x: -44, z: 68 },
  { name: "Đường dạo trên không", kind: "spot", x: -40, z: 4 },
  { name: "Khu phố thương mại Sole", kind: "block", height: 8, x: 42, z: 34, w: 15, d: 58 },
  { name: "Khu phố thương mại Luna", kind: "block", height: 8, x: -120, z: 12, w: 15, d: 40 },
  { name: "Nhà đỗ xe nổi", kind: "block", height: 15, x: -178, z: -146, w: 92, d: 60 }
];

/** Parcel outline in the local plan frame. */
const SITE_OUTLINE = [
  [52, -158], [59, -96], [65, -47], [65, 2], [63, 67], [51, 113],
  [-13, 109], [-95, 51], [-149, -7], [-130, -151]
];

const CONTEXT = {
  highway: { from: [-390, -60], to: [140, 172], width: 36, label: "Đại lộ Thăng Long" },
  park: { x: 92, z: 162, w: 150, d: 132, label: "Công viên Sha (quy hoạch)" }
};

// True north expressed in the local plan frame (azimuth 0°).
const NORTH_X = 0.559;
const NORTH_Z = -0.829;

/* --------------------------------------------------------------- helpers */

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

const towerHeight = (floors) => GROUND_H + (floors - 1) * FLOOR_H;

function makeSeededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function pointInPolygon(x, z, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i, i += 1) {
    const [xi, zi] = polygon[i];
    const [xj, zj] = polygon[j];
    if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) inside = !inside;
  }
  return inside;
}

/**
 * One storey of facade, seen behind the vertical fins: a bright slab edge over a
 * dark recessed glass field. The material colour supplies the frame tone, so the
 * texture only has to darken the glass band.
 */
function makeFacadeTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 16;
  canvas.height = 32;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#272b2d";
  ctx.fillRect(0, 0, 16, 32);
  ctx.fillStyle = "#15181a";
  ctx.fillRect(0, 3, 16, 21);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 26, 16, 6);
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function shapeFromPoints(points) {
  const shape = new THREE.Shape();
  points.forEach(([x, z], index) => {
    if (index === 0) shape.moveTo(x, z);
    else shape.lineTo(x, z);
  });
  shape.closePath();
  return shape;
}

/** Flat slab extruded from a 2D outline and laid on the XZ plane. */
function slab(points, y, thickness, material) {
  const geometry = new THREE.ExtrudeGeometry(shapeFromPoints(points), {
    depth: thickness,
    bevelEnabled: false,
    curveSegments: 6
  });
  geometry.rotateX(Math.PI / 2);
  geometry.translate(0, y + thickness, 0);
  return new THREE.Mesh(geometry, material);
}

/** Shrinks a convex-ish outline towards its centroid by roughly `metres`. */
function insetOutline(points, metres) {
  const cx = points.reduce((sum, p) => sum + p[0], 0) / points.length;
  const cz = points.reduce((sum, p) => sum + p[1], 0) / points.length;
  return points.map(([x, z]) => {
    const dx = x - cx;
    const dz = z - cz;
    const length = Math.hypot(dx, dz) || 1;
    const scale = Math.max(0, length - metres) / length;
    return [cx + dx * scale, cz + dz * scale];
  });
}

function roundedRectPoints(x, z, w, d, radius, steps = 5) {
  const r = Math.max(0.5, Math.min(radius, w / 2 - 0.1, d / 2 - 0.1));
  const corners = [
    [x + w / 2 - r, z + d / 2 - r, 0],
    [x - w / 2 + r, z + d / 2 - r, Math.PI / 2],
    [x - w / 2 + r, z - d / 2 + r, Math.PI],
    [x + w / 2 - r, z - d / 2 + r, -Math.PI / 2]
  ];
  const points = [];
  corners.forEach(([cx, cz, start]) => {
    for (let i = 0; i <= steps; i += 1) {
      const angle = start + (i / steps) * (Math.PI / 2);
      points.push([cx + Math.cos(angle) * r, cz + Math.sin(angle) * r]);
    }
  });
  return points;
}

/* ---------------------------------------------------------- orbit camera */

/**
 * Compact orbit controller: drag to rotate, wheel or pinch to zoom, right-drag
 * / shift-drag / two-finger drag to pan, arrow keys and +/- for keyboard use.
 * Written locally so the page loads a single module from the CDN.
 */
class Orbit {
  constructor(camera, element, view) {
    this.camera = camera;
    this.element = element;
    this.target = view.target.clone();
    this.goalTarget = view.target.clone();
    this.azimuth = view.azimuth;
    this.polar = view.polar;
    this.distance = view.distance;
    this.goal = { azimuth: view.azimuth, polar: view.polar, distance: view.distance };
    this.minDistance = 90;
    this.maxDistance = 1300;
    this.minPolar = 0.1;
    this.maxPolar = 1.45;
    this.dragged = false;
    this.pointers = new Map();
    this.mode = null;
    this.pinch = 0;
    this.bind();
    this.apply(1);
  }

  bind() {
    const el = this.element;
    el.addEventListener("pointerdown", this.onDown.bind(this));
    el.addEventListener("pointermove", this.onMove.bind(this));
    el.addEventListener("pointerup", this.onUp.bind(this));
    el.addEventListener("pointercancel", this.onUp.bind(this));
    el.addEventListener("wheel", this.onWheel.bind(this), { passive: false });
    el.addEventListener("contextmenu", (event) => event.preventDefault());
    el.addEventListener("keydown", this.onKey.bind(this));
  }

  onDown(event) {
    if (event.target.closest(".model-ui") || event.target.closest(".model-label")) {
      this.mode = null;
      return;
    }
    this.element.setPointerCapture?.(event.pointerId);
    this.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    this.dragged = false;
    if (this.pointers.size === 2) {
      this.mode = "pinch";
      this.pinch = this.spread();
    } else {
      this.mode = event.button === 2 || event.shiftKey ? "pan" : "rotate";
    }
  }

  spread() {
    const [a, b] = [...this.pointers.values()];
    return Math.hypot(a.x - b.x, a.y - b.y);
  }

  centre() {
    const list = [...this.pointers.values()];
    const sum = list.reduce((acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y }), { x: 0, y: 0 });
    return { x: sum.x / list.length, y: sum.y / list.length };
  }

  onMove(event) {
    if (!this.pointers.has(event.pointerId)) return;
    const previous = this.pointers.get(event.pointerId);
    const before = this.centre();
    this.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    const after = this.centre();
    const dx = after.x - before.x;
    const dy = after.y - before.y;
    if (Math.hypot(event.clientX - previous.x, event.clientY - previous.y) > 2) this.dragged = true;

    if (this.mode === "pinch" && this.pointers.size === 2) {
      const spread = this.spread();
      if (this.pinch > 0 && spread > 0) this.zoom(this.pinch / spread);
      this.pinch = spread;
      this.pan(dx, dy);
      return;
    }
    if (this.mode === "pan") {
      this.pan(dx, dy);
      return;
    }
    if (this.mode === "rotate") {
      this.goal.azimuth -= dx * 0.0055;
      this.goal.polar = clamp(this.goal.polar - dy * 0.0045, this.minPolar, this.maxPolar);
    }
  }

  onUp(event) {
    this.pointers.delete(event.pointerId);
    this.mode = this.pointers.size ? "rotate" : null;
  }

  onWheel(event) {
    event.preventDefault();
    this.zoom(Math.exp(clamp(event.deltaY, -140, 140) * 0.0012));
  }

  onKey(event) {
    const step = event.shiftKey ? 0.16 : 0.07;
    if (event.key === "ArrowLeft") this.goal.azimuth -= step;
    else if (event.key === "ArrowRight") this.goal.azimuth += step;
    else if (event.key === "ArrowUp") this.goal.polar = clamp(this.goal.polar - step * 0.6, this.minPolar, this.maxPolar);
    else if (event.key === "ArrowDown") this.goal.polar = clamp(this.goal.polar + step * 0.6, this.minPolar, this.maxPolar);
    else if (event.key === "+" || event.key === "=") this.zoom(0.88);
    else if (event.key === "-" || event.key === "_") this.zoom(1.14);
    else return;
    event.preventDefault();
  }

  zoom(factor) {
    this.goal.distance = clamp(this.goal.distance * factor, this.minDistance, this.maxDistance);
  }

  pan(dx, dy) {
    const scale = this.goal.distance * 0.0016;
    const right = new THREE.Vector3(Math.cos(this.azimuth), 0, -Math.sin(this.azimuth));
    const forward = new THREE.Vector3(Math.sin(this.azimuth), 0, Math.cos(this.azimuth));
    this.goalTarget.addScaledVector(right, -dx * scale);
    this.goalTarget.addScaledVector(forward, -dy * scale);
    this.goalTarget.x = clamp(this.goalTarget.x, -330, 240);
    this.goalTarget.z = clamp(this.goalTarget.z, -330, 280);
  }

  moveTo(view) {
    if (view.azimuth !== undefined) this.goal.azimuth = view.azimuth;
    if (view.polar !== undefined) this.goal.polar = clamp(view.polar, this.minPolar, this.maxPolar);
    if (view.distance !== undefined) this.goal.distance = clamp(view.distance, this.minDistance, this.maxDistance);
    if (view.target) this.goalTarget.copy(view.target);
  }

  apply(lerp) {
    this.azimuth += (this.goal.azimuth - this.azimuth) * lerp;
    this.polar += (this.goal.polar - this.polar) * lerp;
    this.distance += (this.goal.distance - this.distance) * lerp;
    this.target.lerp(this.goalTarget, lerp);
    const sinPolar = Math.sin(this.polar);
    this.camera.position.set(
      this.target.x + this.distance * sinPolar * Math.sin(this.azimuth),
      this.target.y + this.distance * Math.cos(this.polar),
      this.target.z + this.distance * sinPolar * Math.cos(this.azimuth)
    );
    this.camera.lookAt(this.target);
  }

  update() {
    this.apply(0.12);
  }
}

/* ----------------------------------------------------------- scene build */

function buildGround(scene, palette) {
  const surrounds = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), palette.surrounds);
  surrounds.rotation.x = -Math.PI / 2;
  surrounds.position.y = -1.4;
  surrounds.receiveShadow = true;
  scene.add(surrounds);

  scene.add(slab(
    roundedRectPoints(CONTEXT.park.x, CONTEXT.park.z, CONTEXT.park.w, CONTEXT.park.d, 40, 6),
    -1.3, 0.5, palette.parkland
  ));

  const plate = slab(SITE_OUTLINE, -1, 1.3, palette.plate);
  plate.receiveShadow = true;
  scene.add(plate);

  const { from, to, width } = CONTEXT.highway;
  const length = Math.hypot(to[0] - from[0], to[1] - from[1]);
  const angle = -Math.atan2(to[1] - from[1], to[0] - from[0]);
  const road = new THREE.Mesh(new THREE.BoxGeometry(length, 0.8, width), palette.road);
  road.position.set((from[0] + to[0]) / 2, -1, (from[1] + to[1]) / 2);
  road.rotation.y = angle;
  scene.add(road);

  const median = new THREE.Mesh(new THREE.BoxGeometry(length * 0.97, 0.9, 2.4), palette.roadLine);
  median.position.set(road.position.x, -0.95, road.position.z);
  median.rotation.y = angle;
  scene.add(median);

  scene.add(slab(
    [[62, 4], [70, 66], [58, 118], [44, 120], [58, 66], [50, 6]],
    -0.9, 0.5, palette.water
  ));

  // Internal circulation: a perimeter ring drawn as an inner plate inset from
  // the parcel edge, plus the road that separates the two build areas.
  scene.add(slab(insetOutline(SITE_OUTLINE, 15), 0.3, 0.4, palette.plate));
  scene.add(slab(roundedRectPoints(-178, -146, 108, 76, 8), -1, 1.1, palette.plate));
  const divider = new THREE.Mesh(new THREE.BoxGeometry(230, 0.5, 11), palette.road);
  divider.position.set(-45, 0.35, -33);
  scene.add(divider);
  const spur = new THREE.Mesh(new THREE.BoxGeometry(11, 0.5, 120), palette.road);
  spur.position.set(-40, 0.3, 40);
  scene.add(spur);
}

function buildLandscape(scene, palette) {
  [
    [-38, 32, 34, 108, 12],
    [-26, -96, 30, 48, 12],
    [-88, -74, 40, 44, 12],
    [12, 26, 20, 96, 9],
    [-74, 8, 24, 52, 9]
  ].forEach(([x, z, w, d, r]) => {
    scene.add(slab(roundedRectPoints(x, z, w, d, r), 0.3, 0.35, palette.lawn));
  });

  const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-30, 1, -32),
    new THREE.Vector3(-43, 1, -2),
    new THREE.Vector3(-31, 1, 26),
    new THREE.Vector3(-45, 1, 54),
    new THREE.Vector3(-31, 1, 82),
    new THREE.Vector3(-35, 1, 104)
  ]);
  const promenade = new THREE.Mesh(new THREE.TubeGeometry(curve, 100, 2.6, 5, false), palette.path);
  promenade.scale.y = 0.2;
  promenade.position.y = 1;
  scene.add(promenade);
}

function buildAmenities(scene, palette, shadows) {
  return AMENITIES.map((item) => {
    let y = 2;
    if (item.kind === "pool") {
      scene.add(slab(roundedRectPoints(item.x, item.z, item.w + 9, item.d + 9, 6), 0.4, 0.3, palette.deck));
      scene.add(slab(roundedRectPoints(item.x, item.z, item.w, item.d, 4), 0.55, 0.5, palette.pool));
      y = 3;
    } else if (item.kind === "court") {
      scene.add(slab(roundedRectPoints(item.x, item.z, item.w, item.d, 1.5), 0.55, 0.5, palette.court));
      y = 3;
    } else if (item.kind === "green") {
      y = 3;
    } else if (item.kind === "block") {
      const box = new THREE.Mesh(
        new THREE.BoxGeometry(item.w, item.height, item.d),
        item.height > 10 ? palette.parking : palette.retail
      );
      box.position.set(item.x, item.height / 2, item.z);
      box.castShadow = shadows;
      box.receiveShadow = true;
      scene.add(box);
      y = item.height + 3;
    }
    return { name: item.name, anchor: new THREE.Vector3(item.x, y, item.z) };
  });
}

function buildTrees(scene, palette, shadows) {
  const random = makeSeededRandom(20260906);
  const blocked = [];
  TOWERS.forEach((tower) => tower.segs.forEach(([cx, cz, lx, lz]) => {
    blocked.push({ x: cx, z: cz, w: lx + 14, d: lz + 14 });
  }));
  AMENITIES.forEach((item) => {
    if (item.w) blocked.push({ x: item.x, z: item.z, w: item.w + 10, d: item.d + 10 });
  });

  const spots = [];
  // A tree line along the perimeter road first, then scattered planting.
  const ring = insetOutline(SITE_OUTLINE, 8);
  ring.forEach(([x, z], index) => {
    const [nx, nz] = ring[(index + 1) % ring.length];
    const steps = Math.max(2, Math.round(Math.hypot(nx - x, nz - z) / 13));
    for (let i = 0; i < steps; i += 1) {
      const t = i / steps;
      spots.push([x + (nx - x) * t, z + (nz - z) * t, 5 + random() * 3]);
    }
  });

  let attempts = 0;
  while (spots.length < 320 && attempts < 12000) {
    attempts += 1;
    const x = -170 + random() * 250;
    const z = -180 + random() * 310;
    if (!pointInPolygon(x, z, SITE_OUTLINE)) continue;
    if (blocked.some((b) => Math.abs(x - b.x) < b.w / 2 && Math.abs(z - b.z) < b.d / 2)) continue;
    spots.push([x, z, 4.5 + random() * 4.5]);
  }

  const foliage = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 1, 7), palette.foliage, spots.length);
  const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.16, 0.24, 1, 5), palette.trunk, spots.length);
  foliage.castShadow = shadows;
  const dummy = new THREE.Object3D();
  spots.forEach(([x, z, h], index) => {
    const spread = h * 0.42;
    dummy.position.set(x, h * 0.62, z);
    dummy.scale.set(spread, h * 0.85, spread);
    dummy.rotation.y = index * 1.7;
    dummy.updateMatrix();
    foliage.setMatrixAt(index, dummy.matrix);
    dummy.position.set(x, h * 0.16, z);
    dummy.scale.set(1, h * 0.34, 1);
    dummy.rotation.y = 0;
    dummy.updateMatrix();
    trunk.setMatrixAt(index, dummy.matrix);
  });
  scene.add(foliage, trunk);
}

/**
 * Each tower owns its materials so filtering and highlighting stay isolated.
 *
 * The massing follows the brochure facade language rather than a plain slab:
 * a dark recessed glass shell, deep vertical fins on every face, bright slab
 * edges once per storey, planted sky-garden bands and a taller crown frame.
 */
function buildTower(tower, scene, palette, shadows) {
  const zone = ZONES[tower.zone];
  const group = new THREE.Group();
  const height = towerHeight(tower.floors);
  const owned = [];
  const picks = [];
  const fins = [];

  const shellMaterial = new THREE.MeshStandardMaterial({
    color: zone.frame,
    metalness: 0.18,
    roughness: 0.62,
    map: palette.facadeFor(tower.floors)
  });
  const frameMaterial = new THREE.MeshStandardMaterial({
    color: zone.frame,
    metalness: 0.22,
    roughness: 0.55
  });
  const roofMaterial = new THREE.MeshStandardMaterial({
    color: palette.roofTone,
    metalness: 0.1,
    roughness: 0.8
  });
  const gardenMaterial = new THREE.MeshLambertMaterial({ color: 0x6f8f5b });
  const podiumMaterial = new THREE.MeshStandardMaterial({
    color: palette.podiumTone,
    metalness: 0.1,
    roughness: 0.78
  });
  owned.push(shellMaterial, frameMaterial, roofMaterial, gardenMaterial, podiumMaterial);

  // Sky gardens sit on the transfer-style levels the brochure renders show
  // planted; heights are indicative, spread evenly up the shaft.
  const gardenLevels = tower.floors > 32 ? [0.33, 0.58, 0.82] : [0.38, 0.68];
  const finStep = 4.1;
  const finBase = PODIUM_H - 0.4;

  const addBox = (w, h, d, x, y, z, material, pickable) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
    mesh.position.set(x, y, z);
    mesh.castShadow = shadows;
    mesh.receiveShadow = true;
    mesh.userData.towerId = tower.id;
    group.add(mesh);
    if (pickable !== false) picks.push(mesh);
    return mesh;
  };

  tower.segs.forEach(([cx, cz, lx, lz]) => {
    addBox(lx + 8, PODIUM_H, lz + 8, cx, PODIUM_H / 2, cz, podiumMaterial);
    // Glazed retail recess with a light frame edge above it.
    addBox(lx + 7.2, 3.8, lz + 7.2, cx, 2.4, cz, shellMaterial, false);
    addBox(lx + 8.3, 1, lz + 8.3, cx, 4.8, cz, frameMaterial, false);

    const shellHeight = height - PODIUM_H;
    addBox(lx, shellHeight, lz, cx, PODIUM_H + shellHeight / 2, cz, shellMaterial);

    // Corner posts read as the structural frame between the glazed bays.
    [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([sx, sz]) => {
      addBox(1.5, shellHeight, 1.5, cx + (sx * lx) / 2, PODIUM_H + shellHeight / 2, cz + (sz * lz) / 2, frameMaterial, false);
    });

    // Vertical fins on all four faces — the strongest cue in the real facade.
    const finTop = height - 4.5;
    const finHeight = finTop - finBase;
    const finY = finBase + finHeight / 2;
    const along = Math.max(2, Math.round(lx / finStep));
    const across = Math.max(2, Math.round(lz / finStep));
    for (let i = 1; i < along; i += 1) {
      const x = cx - lx / 2 + (i * lx) / along;
      fins.push([x, finY, cz - lz / 2 - 0.55, 0.6, finHeight, 1.9]);
      fins.push([x, finY, cz + lz / 2 + 0.55, 0.6, finHeight, 1.9]);
    }
    for (let i = 1; i < across; i += 1) {
      const z = cz - lz / 2 + (i * lz) / across;
      fins.push([cx - lx / 2 - 0.55, finY, z, 1.9, finHeight, 0.6]);
      fins.push([cx + lx / 2 + 0.55, finY, z, 1.9, finHeight, 0.6]);
    }

    gardenLevels.forEach((ratio) => {
      const y = PODIUM_H + shellHeight * ratio;
      addBox(lx + 1.1, 1.1, lz + 1.1, cx, y, cz, gardenMaterial, false);
      addBox(lx + 1.4, 0.7, lz + 1.4, cx, y - 1.2, cz, frameMaterial, false);
    });

    // Crown: a taller frame band, then the dark roof deck and its plant room.
    addBox(lx + 1.5, 3.8, lz + 1.5, cx, height - 1.1, cz, frameMaterial);
    addBox(lx + 0.6, 0.7, lz + 0.6, cx, height + 1.1, cz, roofMaterial, false);
    addBox(lx * 0.22, 2.4, lz * 0.3, cx, height + 2.6, cz, roofMaterial, false);
  });

  if (fins.length) {
    const finMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), frameMaterial, fins.length);
    const dummy = new THREE.Object3D();
    fins.forEach(([x, y, z, w, h, d], index) => {
      dummy.position.set(x, y, z);
      dummy.scale.set(w, h, d);
      dummy.updateMatrix();
      finMesh.setMatrixAt(index, dummy.matrix);
    });
    finMesh.castShadow = shadows;
    finMesh.userData.towerId = tower.id;
    group.add(finMesh);
    picks.push(finMesh);
  }

  scene.add(group);
  const anchorX = tower.segs.reduce((sum, seg) => sum + seg[0], 0) / tower.segs.length;
  const anchorZ = tower.segs.reduce((sum, seg) => sum + seg[1], 0) / tower.segs.length;
  return {
    ...tower,
    materials: owned,
    picks,
    height,
    anchor: new THREE.Vector3(anchorX, height + 16, anchorZ),
    focus: new THREE.Vector3(anchorX, height * 0.35, anchorZ)
  };
}

/* ------------------------------------------------------------------- app */

function boot() {
  const stage = document.querySelector("[data-model-stage]");
  if (!stage) return;
  const canvas = stage.querySelector("canvas");
  const labelLayer = stage.querySelector("[data-model-labels]");
  const panel = stage.querySelector("[data-model-panel]");
  const status = stage.querySelector("[data-model-status]");
  if (!canvas || !labelLayer || !panel) return;

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  } catch (error) {
    stage.dataset.modelState = "unsupported";
    return;
  }

  const shadows = window.matchMedia("(min-width: 900px)").matches;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
  renderer.shadowMap.enabled = shadows;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xe6e3d9);
  scene.fog = new THREE.Fog(0xe6e3d9, 1100, 2500);

  const VIEWS = {
    overview: { azimuth: -0.62, polar: 0.88, distance: 470, radius: 150, target: new THREE.Vector3(-30, 30, -22) },
    top: { azimuth: -0.62, polar: 0.12, distance: 470, radius: 155, target: new THREE.Vector3(-34, 0, -18) },
    // Each collection is approached from its own side of the parcel so the
    // other towers do not stand between the camera and the subject.
    signature: { azimuth: -0.42, polar: 0.84, distance: 400, radius: 120, target: new THREE.Vector3(-34, 30, 28) },
    prestige: { azimuth: -2.95, polar: 0.84, distance: 340, radius: 95, target: new THREE.Vector3(-88, 28, -118) },
    elite: { azimuth: 1.76, polar: 0.84, distance: 340, radius: 95, target: new THREE.Vector3(14, 28, -78) }
  };

  const camera = new THREE.PerspectiveCamera(38, 1, 1, 2600);
  let viewScale = 1;

  /** Smallest camera distance that still fits a sphere of `radius` on screen. */
  function fitDistance(radius) {
    const halfVertical = Math.tan((camera.fov * Math.PI) / 360);
    return radius / Math.max(0.05, Math.min(halfVertical, halfVertical * camera.aspect));
  }

  /** How much a stored distance has to grow for the current stage shape. */
  function fitScale() {
    return clamp(fitDistance(150) / 470, 1, 2.4);
  }

  /** A stored view, pulled back far enough to suit the stage proportions. */
  function framed(view, distance, radius) {
    const base = distance === undefined ? view.distance : distance;
    const span = radius === undefined ? view.radius || 120 : radius;
    return {
      azimuth: view.azimuth,
      polar: view.polar,
      distance: Math.max(base, fitDistance(span)),
      target: view.target.clone()
    };
  }

  const controls = new Orbit(camera, stage, VIEWS.overview);

  scene.add(new THREE.HemisphereLight(0xeaf1f6, 0x9aa189, 1.25));
  scene.add(new THREE.AmbientLight(0xffffff, 0.42));
  const sun = new THREE.DirectionalLight(0xfff4e2, 2.05);
  sun.position.set(-230, 320, 200);
  if (shadows) {
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.near = 60;
    sun.shadow.camera.far = 950;
    sun.shadow.camera.left = -330;
    sun.shadow.camera.right = 330;
    sun.shadow.camera.top = 330;
    sun.shadow.camera.bottom = -330;
    sun.shadow.normalBias = 0.7;
  }
  scene.add(sun);

  const facadeTexture = makeFacadeTexture();
  const facadeCache = new Map();
  const palette = {
    /** One texture per storey count, shared across towers of the same height. */
    facadeFor(floors) {
      if (!facadeCache.has(floors)) {
        const texture = facadeTexture.clone();
        texture.needsUpdate = true;
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(1, floors - 2);
        facadeCache.set(floors, texture);
      }
      return facadeCache.get(floors);
    },
    roofTone: 0x74776f,
    podiumTone: 0x8f8676,
    surrounds: new THREE.MeshLambertMaterial({ color: 0xc2cbb0 }),
    parkland: new THREE.MeshLambertMaterial({ color: 0xb6c7a1 }),
    plate: new THREE.MeshLambertMaterial({ color: 0xe8e1d0 }),
    lawn: new THREE.MeshLambertMaterial({ color: 0xadc394 }),
    path: new THREE.MeshLambertMaterial({ color: 0xd5b98f }),
    road: new THREE.MeshLambertMaterial({ color: 0x8d8b84 }),
    roadLine: new THREE.MeshLambertMaterial({ color: 0xe9e5d7 }),
    water: new THREE.MeshLambertMaterial({ color: 0x7ea7ad }),
    pool: new THREE.MeshLambertMaterial({ color: 0x4bb0c3 }),
    deck: new THREE.MeshLambertMaterial({ color: 0xdccdb1 }),
    court: new THREE.MeshLambertMaterial({ color: 0x2e6d8d }),
    retail: new THREE.MeshLambertMaterial({ color: 0xd9cfb9 }),
    parking: new THREE.MeshLambertMaterial({ color: 0xc6c1b2 }),
    foliage: new THREE.MeshLambertMaterial({ color: 0x6e8e5b }),
    trunk: new THREE.MeshLambertMaterial({ color: 0x6c5943 })
  };

  buildGround(scene, palette);
  buildLandscape(scene, palette);
  const amenityMarkers = buildAmenities(scene, palette, shadows);
  buildTrees(scene, palette, shadows);
  const towers = TOWERS.map((tower) => buildTower(tower, scene, palette, shadows));
  const pickTargets = towers.flatMap((tower) => tower.picks);

  /* ---------------------------------------------------------- overlays */

  const towerLabels = towers.map((tower) => {
    const el = document.createElement("button");
    el.type = "button";
    el.className = `model-label model-label--tower model-label--${tower.zone}`;
    el.innerHTML =
      `<span class="model-label-id">${tower.id}</span><span class="model-label-meta">${tower.floors} tầng</span>`;
    el.setAttribute("aria-label", `Tòa ${tower.id} — ${tower.name}, ${tower.floors} tầng`);
    el.addEventListener("click", () => {
      if (controls.dragged) return;
      select(tower.id, true);
    });
    labelLayer.append(el);
    return { tower, el, anchor: tower.anchor };
  });

  const amenityLabels = amenityMarkers.map((item) => {
    const el = document.createElement("span");
    el.className = "model-label model-label--amenity";
    el.textContent = item.name;
    el.hidden = true;
    labelLayer.append(el);
    return { el, anchor: item.anchor, amenity: true };
  });

  const contextLabels = [
    { text: CONTEXT.highway.label, anchor: new THREE.Vector3(-152, 4, 48) },
    { text: CONTEXT.park.label, anchor: new THREE.Vector3(CONTEXT.park.x - 30, 4, CONTEXT.park.z - 40) }
  ].map((item) => {
    const el = document.createElement("span");
    el.className = "model-label model-label--context";
    el.textContent = item.text;
    labelLayer.append(el);
    return { el, anchor: item.anchor };
  });

  /* --------------------------------------------------------- selection */

  let selected = null;
  let zoneFilter = "all";

  function paint() {
    towers.forEach((tower) => {
      const dimmed = zoneFilter !== "all" && tower.zone !== zoneFilter;
      const active = selected === tower.id;
      tower.picks.forEach((mesh) => { mesh.castShadow = shadows && !dimmed; });
      tower.materials.forEach((material) => {
        if (material.transparent !== dimmed) {
          material.transparent = dimmed;
          material.needsUpdate = true;
        }
        material.opacity = dimmed ? 0.25 : 1;
        material.depthWrite = !dimmed;
        if (material.emissive) material.emissive.setHex(active ? 0x2e2314 : 0x000000);
      });
    });
    towerLabels.forEach(({ tower, el }) => {
      el.classList.toggle("is-active", selected === tower.id);
      el.classList.toggle("is-dimmed", zoneFilter !== "all" && tower.zone !== zoneFilter);
    });
    document.querySelectorAll("[data-model-zone]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.modelZone === zoneFilter));
    });
  }

  function select(id, focus) {
    selected = selected === id && !focus ? null : id || null;
    const tower = towers.find((item) => item.id === selected);
    if (tower) {
      const zone = ZONES[tower.zone];
      panel.hidden = false;
      panel.innerHTML = `
        <button class="model-panel-close" type="button" data-model-close aria-label="Đóng bảng thông tin">×</button>
        <p class="model-panel-zone"><span style="background:${zone.chip}"></span>${zone.name}</p>
        <p class="model-panel-title">Tòa ${tower.id}</p>
        <p class="model-panel-sub">${tower.name}${tower.code ? ` · mã hồ sơ ${tower.code}` : ""}</p>
        <dl class="model-panel-facts">
          <div><dt>Tầng trên cùng có bản vẽ riêng</dt><dd>${tower.floors}</dd></div>
          <div><dt>Số nhóm mặt bằng</dt><dd>${tower.plans}</dd></div>
          <div><dt>Vị trí trong tổng thể</dt><dd>${tower.row}</dd></div>
        </dl>
        <a class="btn btn-primary model-panel-link" href="${tower.href}">Xem mặt bằng tòa ${tower.id}</a>
      `;
      if (focus) {
        const side = VIEWS[tower.zone] || VIEWS.overview;
        controls.moveTo({
          ...framed(side, 285, 90),
          target: tower.focus.clone()
        });
      }
    } else {
      panel.hidden = true;
      panel.textContent = "";
    }
    paint();
  }

  panel.addEventListener("click", (event) => {
    if (event.target.closest("[data-model-close]")) select(null, false);
  });

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  stage.addEventListener("pointerup", (event) => {
    if (controls.dragged || event.button === 2) return;
    if (event.target.closest(".model-ui") || event.target.closest(".model-label")) return;
    const rect = stage.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(pickTargets, false)[0];
    select(hit ? hit.object.userData.towerId : null, false);
  });

  /* ---------------------------------------------------------- controls */

  document.querySelectorAll("[data-model-view]").forEach((button) => {
    button.addEventListener("click", () => {
      const view = VIEWS[button.dataset.modelView];
      if (view) controls.moveTo(framed(view));
    });
  });

  document.querySelectorAll("[data-model-zone]").forEach((button) => {
    button.addEventListener("click", () => {
      const next = button.dataset.modelZone;
      zoneFilter = zoneFilter === next ? "all" : next;
      controls.moveTo(framed(VIEWS[zoneFilter] || VIEWS.overview));
      const current = towers.find((item) => item.id === selected);
      if (current && zoneFilter !== "all" && current.zone !== zoneFilter) select(null, false);
      else paint();
    });
  });

  const amenityToggle = document.querySelector("[data-model-amenities]");
  let amenitiesVisible = false;
  amenityToggle?.addEventListener("click", () => {
    amenitiesVisible = !amenitiesVisible;
    amenityToggle.setAttribute("aria-pressed", String(amenitiesVisible));
    amenityToggle.textContent = amenitiesVisible ? "Ẩn tên tiện ích" : "Hiện tên tiện ích";
  });

  const compass = document.querySelector("[data-model-compass]");

  /* -------------------------------------------------------------- loop */

  const projected = new THREE.Vector3();
  const placed = [];
  const occluder = new THREE.Raycaster();
  const rayDirection = new THREE.Vector3();

  /** True when a tower stands between the camera and this ground anchor. */
  function isHidden(anchor) {
    rayDirection.copy(anchor).sub(camera.position);
    const span = rayDirection.length();
    occluder.set(camera.position, rayDirection.divideScalar(span));
    occluder.far = span - 3;
    return occluder.intersectObjects(pickTargets, false).length > 0;
  }

  function project(item, width, height) {
    projected.copy(item.anchor).project(camera);
    if (projected.z >= 1 || Math.abs(projected.x) > 1.3 || Math.abs(projected.y) > 1.3) return null;
    return { x: ((projected.x + 1) / 2) * width, y: ((1 - projected.y) / 2) * height };
  }

  function place(item, x, y) {
    item.el.hidden = false;
    item.el.style.transform = `translate(-50%,-50%) translate(${x.toFixed(1)}px,${y.toFixed(1)}px)`;
  }

  function updateOverlays(width, height) {
    // Tower chips are decluttered: the far ones keep their spot and nearer
    // chips slide down over their own facade instead of stacking on top.
    placed.length = 0;
    const pending = [];
    towerLabels.forEach((item) => {
      const point = project(item, width, height);
      if (!point) {
        item.el.hidden = true;
        return;
      }
      if (!item.w) {
        item.el.hidden = false;
        const measuredWidth = item.el.offsetWidth;
        if (measuredWidth) {
          item.w = measuredWidth;
          item.h = item.el.offsetHeight;
        }
      }
      pending.push({ item, x: point.x, y: point.y, w: item.w || 96, h: item.h || 28 });
    });
    pending.sort((a, b) => a.y - b.y);
    pending.forEach((entry) => {
      let y = entry.y;
      for (let guard = 0; guard < 12; guard += 1) {
        const clash = placed.find((box) =>
          Math.abs(box.x - entry.x) < (box.w + entry.w) / 2 + 6 &&
          Math.abs(box.y - y) < (box.h + entry.h) / 2 + 5);
        if (!clash) break;
        y = clash.y + (clash.h + entry.h) / 2 + 6;
      }
      placed.push({ x: entry.x, y, w: entry.w, h: entry.h });
      place(entry.item, entry.x, y);
    });

    // Amenity pins are secondary: they are dropped when they would collide
    // with a tower chip or another pin, or when a tower hides them.
    const amenityPoints = [];
    amenityLabels.forEach((item) => {
      if (!amenitiesVisible) {
        item.el.hidden = true;
        return;
      }
      const point = project(item, width, height);
      if (!point || isHidden(item.anchor)) {
        item.el.hidden = true;
        return;
      }
      if (!item.w) {
        item.el.hidden = false;
        const measuredWidth = item.el.offsetWidth;
        if (measuredWidth) {
          item.w = measuredWidth;
          item.h = item.el.offsetHeight;
        }
      }
      amenityPoints.push({ item, x: point.x, y: point.y, w: item.w || 120, h: item.h || 22 });
    });
    amenityPoints.sort((a, b) => b.y - a.y);
    amenityPoints.forEach((entry) => {
      let y = entry.y;
      let free = false;
      for (let guard = 0; guard < 5; guard += 1) {
        const clash = placed.find((box) =>
          Math.abs(box.x - entry.x) < (box.w + entry.w) / 2 + 4 &&
          Math.abs(box.y - y) < (box.h + entry.h) / 2 + 4);
        if (!clash) {
          free = true;
          break;
        }
        y = clash.y + (clash.h + entry.h) / 2 + 5;
      }
      if (!free || Math.abs(y - entry.y) > 70) {
        entry.item.el.hidden = true;
        return;
      }
      placed.push({ x: entry.x, y, w: entry.w, h: entry.h });
      place(entry.item, entry.x, y);
    });

    contextLabels.forEach((item) => {
      const point = project(item, width, height);
      if (!point) {
        item.el.hidden = true;
        return;
      }
      if (!item.w) {
        item.el.hidden = false;
        const measuredWidth = item.el.offsetWidth;
        if (measuredWidth) {
          item.w = measuredWidth;
          item.h = item.el.offsetHeight;
        }
      }
      const w = item.w || 140;
      const h = item.h || 20;
      const clash = placed.some((box) =>
        Math.abs(box.x - point.x) < (box.w + w) / 2 + 4 &&
        Math.abs(box.y - point.y) < (box.h + h) / 2 + 4);
      if (clash) {
        item.el.hidden = true;
        return;
      }
      placed.push({ x: point.x, y: point.y, w, h });
      place(item, point.x, point.y);
    });

    if (compass) {
      const cos = Math.cos(controls.azimuth);
      const sin = Math.sin(controls.azimuth);
      const screenRight = NORTH_X * cos - NORTH_Z * sin;
      const screenUp = -NORTH_X * sin - NORTH_Z * cos;
      compass.style.transform = `rotate(${(Math.atan2(screenRight, screenUp) * 180) / Math.PI}deg)`;
    }
  }

  let width = 1;
  let height = 1;
  function resize() {
    const rect = stage.getBoundingClientRect();
    width = Math.max(1, Math.round(rect.width));
    height = Math.max(1, Math.round(rect.height));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    // The view distances above are tuned for a wide stage; narrow or portrait
    // stages pull the camera back by the same factor their horizontal field
    // of view lost, so the parcel keeps filling the frame.
    const next = fitScale();
    const ratio = next / viewScale;
    viewScale = next;
    controls.goal.distance = clamp(controls.goal.distance * ratio, controls.minDistance, controls.maxDistance);
    controls.distance = clamp(controls.distance * ratio, controls.minDistance, controls.maxDistance);
  }
  new ResizeObserver(resize).observe(stage);
  resize();

  let frame = 0;
  function tick() {
    frame = requestAnimationFrame(tick);
    controls.update();
    updateOverlays(width, height);
    renderer.render(scene, camera);
  }
  function start() {
    if (!frame) tick();
  }
  function stop() {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
  }

  new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) start();
    else stop();
  }, { threshold: 0 }).observe(stage);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) stop();
    else start();
  });

  stage.dataset.modelState = "ready";
  status?.remove();
  paint();
  start();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot, { once: true });
} else {
  boot();
}
