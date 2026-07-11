import numpy as np
import sympy as sp
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtGui import QPixmap

#np.set_printoptions(suppress=True)

def GaussianEliminate(mat: np.array, pivot: bool, enableLU: bool):
    global hist
    global norm
    if mat.dtype != 'float64':
        mat = np.float64(mat)
    hist = [[mat.copy(), ""]]
    if enableLU:
        hist[0].append(np.eye(mat.shape[0]))
        hist[0].append(np.eye(mat.shape[0]))
    norm = np.linalg.norm(mat, np.inf)
    def helper(mat: np.array, top: np.array, size: int):
        global hist
        i = 0
        swap = 0
        while i < mat.shape[1]:
            if np.linalg.norm(mat.T[i]) > 0:
                break
            i += 1
        if i == mat.shape[1]:
            return mat
        else:
            if pivot:
                lst = abs(mat)[:,i].tolist()
                swap = lst.index(max(lst))
            else:
                while mat[swap, i] == 0:
                    swap += 1
            if swap > 0:
                temp = mat[0].copy()
                mat[0] = mat[swap]
                mat[swap] = temp
                if top is not None:
                    x = top.shape[0] if top.shape[0] != top.size else 1
                    hist.append([np.block([[top], [mat]]), f"R{x + 1} <-> R{swap + x + 1}"])
                    if enableLU:
                        elementary = np.eye(size)
                        tempRow = elementary[x].copy()
                        elementary[x] = elementary[swap + x]
                        elementary[swap + x] = tempRow
                        tempL = hist[-2][3].copy()
                        for m in range(size - mat.shape[0]):
                            tempEntry1 = tempL[x, m]
                            tempEntry2 = tempL[x + swap, m]
                            tempL[x, m] = tempEntry2
                            tempL[x + swap, m] = tempEntry1
                        hist[-1].append(elementary @ hist[-2][2])
                        hist[-1].append(tempL)
                else:
                    hist.append([mat.copy(), f"R1 <-> R{swap + 1}"])
                    if enableLU:
                        elementary = np.eye(size)
                        tempRow = elementary[0].copy()
                        elementary[0] = elementary[swap]
                        elementary[swap] = tempRow
                        hist[-1].append(elementary @ hist[-2][2])
                        hist[-1].append(hist[-2][3])
            elif enableLU:
                try:
                    hist[-1].append(hist[-2][2])
                    hist[-1].append(hist[-2][3])
                except:
                    elementary = np.eye(size)
                    tempRow = elementary[0].copy()
                    elementary[0] = elementary[swap]
                    elementary[swap] = tempRow
                    hist[-1].append(elementary)
                    hist[-1].append(np.eye(size))
        for k in range(1, mat.shape[0]):
            coeff = mat[k,i]/mat[0,i]
            mat[k] -= coeff * mat[0]
            global norm
            if abs(mat[k,i]) < (10 ** -6) * norm:
                mat[k,i] = 0
            val = round(coeff, 3)
            if top is not None:
                x = top.shape[0] if top.shape[0] != top.size else 1
                hist.append([np.block([[top], [mat]]), f"R{k + x + 1} {"-" if val >= 0 else "+"} {abs(val)}R{x + 1}"])
                if enableLU:
                    temp = hist[-2][3].copy()
                    temp[k + x, x] = coeff
                    hist[-1].append(hist[-2][2])
                    hist[-1].append(temp)
            else:
                hist.append([mat.copy(), f"R{k + 1} {"-" if val >= 0 else "+"} {abs(val)}R1"])
                if enableLU:
                    temp = hist[-2][3].copy()
                    temp[k, 0] = coeff
                    hist[-1].append(hist[-2][2])
                    hist[-1].append(temp)
        if mat.shape[0] == 1:
            return mat
        else:
            top = np.block([[top], [mat[0]]]) if top is not None else mat[0]
            return np.block([[mat[0]], [helper(mat[1:], top, size)]])
    return helper(mat, None, mat.shape[0]), hist

def findPivots(mat: np.array, lst: list):
    nonzeros = mat[0].nonzero()[0] if mat.size != 0 else np.array([])
    if nonzeros.size == 0:
        nonpivots = []
        for i in range(mat.shape[1]):
            if i not in lst:
                nonpivots.append(i)
        return lst, nonpivots
    else:
        lst.append(int(nonzeros[0]))
        return findPivots(mat[1:], lst)

def GaussianSolve(mat: np.array, pivot: bool, enableLU: bool):
    mat = GaussianEliminate(mat, pivot, enableLU)[0]
    pivots, nonpivots = findPivots(mat, [])
    if mat.shape[1] - 1 in pivots:
        return "No solution"
    else:
        lst = []
        for i in range(mat.shape[1] - 1):
            lst.append(0)
        dic = {}
        idx1 = len(pivots) - 1
        index = len(nonpivots) - 1
        for j in range(mat.shape[1] - 2, -1, -1):
            if j in pivots:
                string = ""
                for k in range(j + 1, mat.shape[1] - 1):
                    if mat[idx1][k] != 0:
                        string += " - (" + str(str(mat[idx1][k]) + f"*({dic[k]}) / " + str(mat[idx1][j]) + ")")
                if mat[idx1][-1] != 0:
                    string = "(" + str(mat[idx1][-1]) + " / " + str(mat[idx1][j]) + ")" + (" + " + string if string != "" else "")
                dic[j] = string
                idx1 -= 1
            else:
                dic[j] = "t" + str(index)
                index -= 1
        res = []
        for i in range(mat.shape[1] - 1):
            try:
                res.append(sp.sympify(dic[i]))
            except:
                res.append(sp.nan)
        return res

def proj(u: np.array, v: np.array, acc: int): # Projection of u onto v
    temp = round(np.dot(u, v), acc)
    return np.round(v * temp/(np.linalg.norm(v) ** 2), acc) if np.linalg.norm(v) >= 10 ** -(acc - 1) else None

def GramSchmidtOrth(mat: np.array, modified: bool, normed: bool, acc: int):
    if mat.dtype != 'float64':
        mat = np.float64(mat)
    if np.linalg.norm(mat[0]) < 10 ** -acc:
        return [[mat, "Norm of first vector is 0 or close to it; process terminated"]], None
    hist = [[mat.copy(), "Starting Gram-Schmidt Process; let u1 = v1; u2 = v2;"]]
    for i in range(1, len(mat)):
        if modified:
            for j in range(i, len(mat)):
                try:
                    mat[j] -= proj(mat[j], mat[i - 1], acc)
                    hist.append([mat.copy(), f"Subtract projection of v{j + 1} onto u{i} from u{j + 1}"])
                except:
                    hist.append([mat.copy(), "Zero vector encountered; process terminated"])
                    return hist, None
            if j < len(mat) - 1:
                hist[-1][1] += f"\nu{j + 1} formed; let u{j + 2} = v{j + 2}"
        else:
            lst = []
            for v in mat[:i]:
                lst.append(proj(mat[i], v, acc))
            for j in range(i):
                try:
                    mat[i] -= lst[j]
                    hist.append([mat.copy(), f"Subtract projection of v{i + 1} onto u{j + 1} from u{i + 1}"])
                except:
                    hist.append([mat.copy(), "Zero vector encountered; process terminated"])
                    return hist, None
            if i < len(mat) - 1:
                hist[-1][1] += f"\nu{i + 1} formed; let u{i + 2} = v{i + 2}"
        if np.linalg.norm(mat[i]) < 10 ** -(acc - 1):
            hist[-1][1] += "\nLinear dependence encountered; process terminated"
            return hist, None
    for i in range(mat.shape[0]):
        mat[i] /= np.linalg.norm(mat[i])
        mat[i] = np.round(mat[i], acc)
        if normed:
            hist.append([mat.copy(), f"Normalise vector {i + 1}"])
    hist[-1][1] += "\nOrthogonalisation complete!"
    return hist, np.linalg.norm(mat @ mat.T - np.eye(mat.shape[0]))