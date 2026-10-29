# Bischoff 137: CCCC 96 f.240r "p3p3lap3edff.p4.g.gggharazy p3ar." ; pN = vowel by stroke count
import itertools, string
ct = [("p",3),("p",3),"l","a",("p",3),"e","d","f","f",".",("p",4),".","g",".","g","g","g","h","a","r","a","z","y"," ",("p",3),"a","r"]
A = string.ascii_lowercase
for vow in ["aeiou","uoiea"]:
  for k in range(26):
    out=""
    for t in ct:
      if isinstance(t,tuple): out+=vow[t[1]-1].upper()
      elif t in ". ": out+=t
      else: out+=A[(A.index(t)+k)%26]
    print(vow,k,out)
