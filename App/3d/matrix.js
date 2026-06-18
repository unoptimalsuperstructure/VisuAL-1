function matMul4(A, v) {
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