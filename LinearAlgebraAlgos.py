import numpy as np
import sympy as sp
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtGui import QPixmap

np.set_printoptions(suppress=True)

def GaussianEliminate(mat: np.array):
    global hist
    if mat.dtype != 'float64':
        mat = np.float64(mat)
    hist = [[mat.copy(), ""]]
    def helper(mat: np.array, top: np.array):
        global hist
        i = 0
        while i < mat.shape[1]:
            if np.linalg.norm(mat.T[i]) > 0:
                break
            i += 1
        if i == mat.shape[1]:
            return mat
        else:
            j = 0
            while mat[j,i] == 0:
                j += 1
            if j > 0:
                temp = mat[0].copy()
                mat[0] = mat[j]
                mat[j] = temp
                if top is not None:
                    x = top.shape[0] if top.shape[0] != top.size else 1
                    hist.append([np.block([[top], [mat]]), f"R{x + 1} <-> R{j + x + 1}"])
                else:
                    hist.append([mat.copy(), f"R1 <-> R{j + 1}"])
        for k in range(1, mat.shape[0]):
            coeff = mat[k,i]/mat[0,i]
            mat[k] -= coeff * mat[0]
            val = round(coeff, 3)
            if top is not None:
                x = top.shape[0] if top.shape[0] != top.size else 1
                hist.append([np.block([[top], [mat]]), f"R{k + x + 1} {"-" if val >= 0 else "+"} {abs(val)}R{x + 1}"])
            else:
                hist.append([mat.copy(), f"R{k + 1} {"-" if val >= 0 else "+"} {abs(val)}R1"])
        if mat.shape[0] == 1:
            return mat
        else:
            top = np.block([[top], [mat[0]]]) if top is not None else mat[0]
            return np.block([[mat[0]], [helper(mat[1:], top)]])
    return helper(mat, None), hist

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

def GaussianSolve(mat: np.array):
    mat = GaussianEliminate(mat)[0]
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
            res.append(sp.sympify(dic[i]))
        return res

def proj(u: np.array, v: np.array):
    return v * np.dot(u, v)/(np.linalg.norm(v) ** 2) if np.linalg.norm(v) > 0.00000001 else None

def GramSchmidtOrth(mat: np.array):
    if mat.dtype != 'float64':
        mat = np.float64(mat)
    hist = [[mat.copy(), "Starting Gram-Schmidt Process"]]
    res = [mat[0]]
    i = 1
    for u in mat[1:].copy():
        j = 1
        for v in res:
            val = proj(u, v)
            if val is not None:
                mat[i] -= val
                hist.append([np.round(mat.copy(), 8), f"Subtract projection of u{i + 1} onto v{j} from u{i + 1}"])
                if np.linalg.norm(mat[i]) < 0.00000001:
                    hist[-1][1] += "\nLinear dependence encountered; process terminated"
                    return hist
            else:
                hist.append([np.round(mat.copy(), 8), "Zero vector encountered; process terminated"])
                return hist
            j += 1
        res.append(mat[i])
        i += 1
    hist[-1][1] += "\nOrthogonalisation complete!"
    return hist