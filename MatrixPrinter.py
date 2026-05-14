def toString(lst):
    maxLen = 0
    for i in lst:
        for j in i:
            x = str(abs(round(j - int(j), 3)))
            extra_zeros = 5 - len(x)
            if len(str(abs(round(j, 3)))) + extra_zeros > maxLen:
                maxLen = len(str(abs(round(j, 3)))) + extra_zeros
    newList = []
    for line in lst:
        newLine = []
        for entry in line:
            entry2 = str(abs(round((entry) - int(entry), 3)))
            extra_zeros = 5 - len(entry2)
            extra_spaces = maxLen - len(str(abs(round(entry, 3)))) - extra_zeros
            final = extra_spaces * " " + str(abs(round(entry, 3)))
            if extra_zeros == 4:
                final += ".000"
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