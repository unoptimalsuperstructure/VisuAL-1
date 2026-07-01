def toString(lst, acc):
    maxLen = 0
    for i in lst:
        for j in i:
            x = str(abs(round(j - int(j), acc)))
            extra_zeros = acc + 2 - len(x)
            if len(str(abs(round(j, acc)))) + extra_zeros > maxLen:
                maxLen = len(str(abs(round(j, acc)))) + extra_zeros
    newList = []
    for line in lst:
        newLine = []
        for entry in line:
            entry2 = str(abs(round((entry) - int(entry), acc)))
            extra_zeros = acc + 2 - len(entry2)
            extra_spaces = maxLen - len(str(abs(round(entry, acc)))) - extra_zeros
            val = abs(round(entry, acc))
            if val > 0.0001:
                val = str(val)
            else:
                val = f"{val:.{acc}f}"
                extra_zeros = 0
            final = extra_spaces * " " + val
            if extra_zeros == acc + 1:
                final += "." + "0" * acc
            else:
                final += extra_zeros * "0"
            if entry >= 0:
                final = "+" + final
            else:
                final = "-" + final
            newLine.append(final)
        newList.append(newLine)
    return newList

def concat(lst):
    a = [None]*len(lst[0])
    if len(lst[0]) != len(a):
        return "Error: This operation only works on square matrices of the same size"
    for arr in lst:
        if len(arr) != len(a) or len(arr[0]) != len(a):
            return "Error: This operation only works on square matrices of the same size"
        i = 0
        for line in arr:
            if a[i]:
                a[i].append(line)
            else:
                a[i] = [line]
            i += 1
    return(str(a).replace("[[[", "[").replace("]]]", "]").replace("[[", "[").replace("]], ", "]\n").replace(",", "").replace("'", ""))

def displayAsMatrix(matrix: list, augcol: int):
    res = ""
    i = 0
    for line in matrix:
        string = "["
        j = 0
        for entry in line:
            string += entry
            j += 1
            string += (" | " if j + augcol == len(line) else " ") if j < len(line) else "]"
        res += string
        i += 1
        res += "\n" if i < len(matrix) else ""
    return res

def displayAsBasis(matrix: list):
    res = ""
    for i in range(len(matrix[0])):
        string = "["
        for j in range(len(matrix)):
            string += matrix[j][i]
            string += "] [" if j < len(matrix) - 1 else "]"
        res += string
        res += "\n" if i < len(matrix[0]) - 1 else ""
    return res