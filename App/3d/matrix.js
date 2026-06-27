// NO matrix maths with 3js in it belongs here

function matMul4(A, v) {
  // Doing this for semantics hence separated from 4x4
  return [
    A[0]*v[0]  + A[1]*v[1]  + A[2]*v[2]  + A[3]*v[3],
    A[4]*v[0]  + A[5]*v[1]  + A[6]*v[2]  + A[7]*v[3],
    A[8]*v[0]  + A[9]*v[1]  + A[10]*v[2] + A[11]*v[3],
    A[12]*v[0] + A[13]*v[1] + A[14]*v[2] + A[15]*v[3],
  ];
}

function matMul4x4(A, B) {
  const R = new Float64Array(16);
  for (let r = 0; r < 4; r++)
    for (let c = 0; c < 4; c++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += A[r*4+k] * B[k*4+c];
      R[r*4+c] = s;
    }
  return Array.from(R);
}

function matMul3x3(A, B) {
  const R = new Float64Array(9);
  for (let r = 0; r < 3; r++)
    for (let c = 0; c < 3; c++) {
      let s = 0;
      for (let k = 0; k < 3; k++) s += A[r*3+k] * B[k*3+c];
      R[r*3+c] = s;
    }
  return R;
}

function mat3T(M) {
  return [M[0],M[3],M[6], M[1],M[4],M[7], M[2],M[5],M[8]];
}

function mat3det(M) {
  return M[0]*(M[4]*M[8]-M[5]*M[7])
       - M[1]*(M[3]*M[8]-M[5]*M[6])
       + M[2]*(M[3]*M[7]-M[4]*M[6]);
}

function identity3() {
  return [1,0,0, 0,1,0, 0,0,1];
}

function identity4() {
  return [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
}

function translationMatrix(x, y, z) {
  return [1,0,0,x, 0,1,0,y, 0,0,1,z, 0,0,0,1];
}

function reflectPlaneMatrix(a, b, c, d) {
  const n2 = a*a + b*b + c*c;
  return [
    (b*b+c*c-a*a)/n2, -2*a*b/n2,         -2*a*c/n2,         2*a*d/n2,
    -2*a*b/n2,        (a*a+c*c-b*b)/n2,  -2*b*c/n2,         2*b*d/n2,
    -2*a*c/n2,        -2*b*c/n2,         (a*a+b*b-c*c)/n2,  2*c*d/n2,
    0,                0,                 0,                  1,
  ];
}

function reflectLineMatrix(p1, p2, p3, d1, d2, d3) {
  const L = Math.sqrt(d1*d1 + d2*d2 + d3*d3);
  d1/=L; d2/=L; d3/=L;
  const c = p1*d1 + p2*d2 + p3*d3;
  return [
    2*d1*d1-1, 2*d1*d2,   2*d1*d3,   2*(p1-d1*c),
    2*d1*d2,   2*d2*d2-1, 2*d2*d3,   2*(p2-d2*c),
    2*d1*d3,   2*d2*d3,   2*d3*d3-1, 2*(p3-d3*c),
    0,         0,         0,         1,
  ];
}

function rotateLineMatrix(d1, d2, d3, angle) {
  const L = Math.sqrt(d1*d1 + d2*d2 + d3*d3);
  d1/=L; d2/=L; d3/=L;
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  const t = 1 - c;
  return [
    t*d1*d1+c,   t*d1*d2-s*d3, t*d1*d3+s*d2, 0,
    t*d1*d2+s*d3, t*d2*d2+c,   t*d2*d3-s*d1, 0,
    t*d1*d3-s*d2, t*d2*d3+s*d1, t*d3*d3+c,   0,
    0,           0,           0,           1,
  ];
}

function invertMatrix4(m) {
  const [m00,m01,m02,m03,m10,m11,m12,m13,m20,m21,m22,m23,m30,m31,m32,m33] = m;
  const b00=m00*m11-m01*m10, b01=m00*m12-m02*m10, b02=m00*m13-m03*m10;
  const b03=m01*m12-m02*m11, b04=m01*m13-m03*m11, b05=m02*m13-m03*m12;
  const b06=m20*m31-m21*m30, b07=m20*m32-m22*m30, b08=m20*m33-m23*m30;
  const b09=m21*m32-m22*m31, b10=m21*m33-m23*m31, b11=m22*m33-m23*m32;
  const det = b00*b11-b01*b10+b02*b09+b03*b08-b04*b07+b05*b06;
  if (!det) return identity4();
  const d = 1/det;
  return [
    (m11*b11-m12*b10+m13*b09)*d, (m02*b10-m01*b11-m03*b09)*d, (m31*b05-m32*b04+m33*b03)*d, (m22*b04-m21*b05-m23*b03)*d,
    (m12*b08-m10*b11-m13*b07)*d, (m00*b11-m02*b08+m03*b07)*d, (m32*b02-m30*b05-m33*b01)*d, (m20*b05-m22*b02+m23*b01)*d,
    (m10*b10-m11*b08+m13*b06)*d, (m01*b08-m00*b10-m03*b06)*d, (m30*b04-m31*b02+m33*b00)*d, (m21*b02-m20*b04-m23*b00)*d,
    (m11*b07-m10*b09-m12*b06)*d, (m00*b09-m01*b07+m02*b06)*d, (m31*b01-m30*b03-m32*b00)*d, (m20*b03-m21*b01+m22*b00)*d,
  ];
}

function applyMatrix(mat, verts, centre) {
  const nv = verts.map(v => {
    const r = matMul4(mat, [v[0], v[1], v[2], 1]);
    return [r[0], r[1], r[2]];
  });
  const rc = matMul4(mat, [centre[0], centre[1], centre[2], 1]);
  return { vertices: nv, centre: [rc[0], rc[1], rc[2]] };
}

function eigSymmetric3(A) {
  const a = A.slice();
  const V = [1,0,0, 0,1,0, 0,0,1];
  const ix = (r,c) => r*3 + c;
  const pairs = [[0,1],[0,2],[1,2]];

  for (let sweep = 0; sweep < 50; sweep++) {
    if (Math.abs(a[1]) + Math.abs(a[2]) + Math.abs(a[5]) < 1e-14) break;
    for (const [p,q] of pairs) {
      const apq = a[ix(p,q)];
      if (Math.abs(apq) < 1e-18) continue;
      const theta = (a[ix(q,q)] - a[ix(p,p)]) / (2 * apq);
      const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta*theta + 1));
      const c = 1 / Math.sqrt(t*t + 1);
      const s = t * c;
      for (let k = 0; k < 3; k++) {
        const akp = a[ix(k,p)], akq = a[ix(k,q)];
        a[ix(k,p)] = c*akp - s*akq;
        a[ix(k,q)] = s*akp + c*akq;
      }
      for (let k = 0; k < 3; k++) {
        const apk = a[ix(p,k)], aqk = a[ix(q,k)];
        a[ix(p,k)] = c*apk - s*aqk;
        a[ix(q,k)] = s*apk + c*aqk;
      }
      for (let k = 0; k < 3; k++) {
        const vkp = V[ix(k,p)], vkq = V[ix(k,q)];
        V[ix(k,p)] = c*vkp - s*vkq;
        V[ix(k,q)] = s*vkp + c*vkq;
      }
    }
  }

  const vals = [a[0], a[4], a[8]];
  const cols = [[V[0],V[3],V[6]], [V[1],V[4],V[7]], [V[2],V[5],V[8]]];
  const order = [0,1,2].sort((i,j) => vals[j] - vals[i]);
  const sv = order.map(i => cols[i]);
  return {
    values: order.map(i => vals[i]),
    vectors: [ sv[0][0],sv[1][0],sv[2][0],  sv[0][1],sv[1][1],sv[2][1],  sv[0][2],sv[1][2],sv[2][2] ],
  };
}

function svd3(M) {
  const { values, vectors: V } = eigSymmetric3(matMul3x3(mat3T(M), M));
  const sig  = values.map(v => Math.sqrt(Math.max(0, v)));
  const Vcol = [[V[0],V[3],V[6]], [V[1],V[4],V[7]], [V[2],V[5],V[8]]];
  const Ucol = [];

  for (let i = 0; i < 3; i++) {
    const v  = Vcol[i];
    const Mv = [ M[0]*v[0]+M[1]*v[1]+M[2]*v[2],
                 M[3]*v[0]+M[4]*v[1]+M[5]*v[2],
                 M[6]*v[0]+M[7]*v[1]+M[8]*v[2] ];
    Ucol.push(sig[i] > 1e-9 ? Mv.map(x => x / sig[i]) : null);
  }
  const cross = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  for (let i = 0; i < 3; i++) {
    if (Ucol[i]) continue;
    const got = [0,1,2].filter(j => j !== i && Ucol[j]).map(j => Ucol[j]);
    let u = got.length === 2 ? cross(got[0], got[1]) : [i===0?1:0, i===1?1:0, i===2?1:0];
    const n = Math.hypot(...u) || 1;
    Ucol[i] = u.map(x => x / n);
  }
  let U  = [Ucol[0][0],Ucol[1][0],Ucol[2][0], Ucol[0][1],Ucol[1][1],Ucol[2][1], Ucol[0][2],Ucol[1][2],Ucol[2][2]];
  let Vm = V.slice();
  if (mat3det(Vm) < 0) {                       // flip last direction → proper rotations
    for (let r = 0; r < 3; r++) { Vm[r*3+2] *= -1; U[r*3+2] *= -1; }
  }
  return { U, S: sig, Vt: mat3T(Vm), V: Vm };
}