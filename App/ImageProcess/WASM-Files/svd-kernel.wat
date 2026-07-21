;; svd-kernel.wat file for svd kernel wasm, pushing this into repo for reference 

(module
  (memory (export "mem") 1)

  ;; AV = A dot V     A: hxw   V: wxk   AV: hxk
  (func (export "av")
    (param $A i32) (param $V i32) (param $AV i32)
    (param $h i32) (param $w i32) (param $k i32)
    (local $r i32) (local $c i32) (local $j i32)
    (local $a f64) (local $avRow i32) (local $vRow i32) (local $off i32)

    (local.set $r (i32.const 0))
    (block $zdone (loop $zloop
      (br_if $zdone (i32.ge_s (local.get $r) (i32.mul (local.get $h) (local.get $k))))
      (f64.store (i32.add (local.get $AV) (i32.shl (local.get $r) (i32.const 3))) (f64.const 0))
      (local.set $r (i32.add (local.get $r) (i32.const 1)))
      (br $zloop)))
    ;; for r in h: for c in w: a=A[r,c]; for j in k: AV[r,j]+=a*V[c,j]
    (local.set $r (i32.const 0))
    (block $rdone (loop $rloop
      (br_if $rdone (i32.ge_s (local.get $r) (local.get $h)))
      (local.set $avRow (i32.add (local.get $AV)
        (i32.shl (i32.mul (local.get $r) (local.get $k)) (i32.const 3))))
      (local.set $c (i32.const 0))
      (block $cdone (loop $cloop
        (br_if $cdone (i32.ge_s (local.get $c) (local.get $w)))
        (local.set $a (f64.load (i32.add (local.get $A)
          (i32.shl (i32.add (i32.mul (local.get $r) (local.get $w)) (local.get $c)) (i32.const 3)))))
        (if (f64.ne (local.get $a) (f64.const 0)) (then
          (local.set $vRow (i32.add (local.get $V)
            (i32.shl (i32.mul (local.get $c) (local.get $k)) (i32.const 3))))
          (local.set $j (i32.const 0))
          (block $jdone (loop $jloop
            (br_if $jdone (i32.ge_s (local.get $j) (local.get $k)))
            (local.set $off (i32.shl (local.get $j) (i32.const 3)))
            (f64.store (i32.add (local.get $avRow) (local.get $off))
              (f64.add (f64.load (i32.add (local.get $avRow) (local.get $off)))
                       (f64.mul (local.get $a)
                                (f64.load (i32.add (local.get $vRow) (local.get $off))))))
            (local.set $j (i32.add (local.get $j) (i32.const 1)))
            (br $jloop)))))
        (local.set $c (i32.add (local.get $c) (i32.const 1)))
        (br $cloop)))
      (local.set $r (i32.add (local.get $r) (i32.const 1)))
      (br $rloop))))

  ;; W = AT dot AV  A: hxw   AV: hxk   W: wxk
  (func (export "atav")
    (param $A i32) (param $AV i32) (param $W i32)
    (param $h i32) (param $w i32) (param $k i32)
    (local $r i32) (local $c i32) (local $j i32)
    (local $a f64) (local $wRow i32) (local $avRow i32) (local $off i32)
    (local.set $r (i32.const 0))
    (block $zdone (loop $zloop
      (br_if $zdone (i32.ge_s (local.get $r) (i32.mul (local.get $w) (local.get $k))))
      (f64.store (i32.add (local.get $W) (i32.shl (local.get $r) (i32.const 3))) (f64.const 0))
      (local.set $r (i32.add (local.get $r) (i32.const 1)))
      (br $zloop)))
    (local.set $r (i32.const 0))
    (block $rdone (loop $rloop
      (br_if $rdone (i32.ge_s (local.get $r) (local.get $h)))
      (local.set $avRow (i32.add (local.get $AV)
        (i32.shl (i32.mul (local.get $r) (local.get $k)) (i32.const 3))))
      (local.set $c (i32.const 0))
      (block $cdone (loop $cloop
        (br_if $cdone (i32.ge_s (local.get $c) (local.get $w)))
        (local.set $a (f64.load (i32.add (local.get $A)
          (i32.shl (i32.add (i32.mul (local.get $r) (local.get $w)) (local.get $c)) (i32.const 3)))))
        (local.set $wRow (i32.add (local.get $W)
          (i32.shl (i32.mul (local.get $c) (local.get $k)) (i32.const 3))))
        (local.set $j (i32.const 0))
        (block $jdone (loop $jloop
          (br_if $jdone (i32.ge_s (local.get $j) (local.get $k)))
          (local.set $off (i32.shl (local.get $j) (i32.const 3)))
          (f64.store (i32.add (local.get $wRow) (local.get $off))
            (f64.add (f64.load (i32.add (local.get $wRow) (local.get $off)))
                     (f64.mul (local.get $a)
                              (f64.load (i32.add (local.get $avRow) (local.get $off))))))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $jloop)))
        (local.set $c (i32.add (local.get $c) (i32.const 1)))
        (br $cloop)))
      (local.set $r (i32.add (local.get $r) (i32.const 1)))
      (br $rloop))))

  ;; B = (A dot V) dot VT, B[r,c] = sum_j AV[r,j] dot V[c,j]
  (func (export "project")
    (param $A i32) (param $V i32) (param $AV i32) (param $B i32)
    (param $h i32) (param $w i32) (param $k i32)
    (local $r i32) (local $c i32) (local $j i32)
    (local $sum f64) (local $avRow i32) (local $vRow i32)
    ;; caller runs av(), AV dot VT
    (local.set $r (i32.const 0))
    (block $rdone (loop $rloop
      (br_if $rdone (i32.ge_s (local.get $r) (local.get $h)))
      (local.set $avRow (i32.add (local.get $AV)
        (i32.shl (i32.mul (local.get $r) (local.get $k)) (i32.const 3))))
      (local.set $c (i32.const 0))
      (block $cdone (loop $cloop
        (br_if $cdone (i32.ge_s (local.get $c) (local.get $w)))
        (local.set $vRow (i32.add (local.get $V)
          (i32.shl (i32.mul (local.get $c) (local.get $k)) (i32.const 3))))
        (local.set $sum (f64.const 0))
        (local.set $j (i32.const 0))
        (block $jdone (loop $jloop
          (br_if $jdone (i32.ge_s (local.get $j) (local.get $k)))
          (local.set $sum (f64.add (local.get $sum)
            (f64.mul (f64.load (i32.add (local.get $avRow) (i32.shl (local.get $j) (i32.const 3))))
                     (f64.load (i32.add (local.get $vRow) (i32.shl (local.get $j) (i32.const 3)))))))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $jloop)))
        (f64.store (i32.add (local.get $B)
          (i32.shl (i32.add (i32.mul (local.get $r) (local.get $w)) (local.get $c)) (i32.const 3)))
          (local.get $sum))
        (local.set $c (i32.add (local.get $c) (i32.const 1)))
        (br $cloop)))
      (local.set $r (i32.add (local.get $r) (i32.const 1)))
      (br $rloop))))
)