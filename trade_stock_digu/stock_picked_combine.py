try:
    fo = open(r"C:\Users\Administrator\Desktop\picked.txt", "r")
    lines_file = fo.readlines()
finally:
    if fo:
        fo.close()
pool_picked = set()
for line in lines_file:
	lst_code = eval(line)
	for code_stock in lst_code:
		pool_picked.add(code_stock)
print(pool_picked)
