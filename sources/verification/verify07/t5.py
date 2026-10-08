import sys
exec(open(sys.argv[1],encoding='utf-8').read())
print(take_within_budget(['a','b','c','d'],{'a':160,'b':170,'c':150,'d':40},640))
print(take_within_budget(['x'],{'x':700},640))
exec(open(sys.argv[2],encoding='utf-8').read())
T="abcdefghijklmnopqrstuvw"
print(windows(T,10,3))
print(windows(T,10,-2))
