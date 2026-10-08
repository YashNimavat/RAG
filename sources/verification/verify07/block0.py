import math
import numpy as np

q = np.array([1.0, 0.0]); r = np.array([1.0, 0.0]); u = np.array([0.0, 1.0]); comp = np.array([0.6, 0.8])
cos = lambda a, b: float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
for n in range(0, 5):
    chunk = np.mean(np.vstack([r] + [u] * n), axis=0)   # rows: 1 relevant + n off-topic
    print(n, chunk, round(cos(q, chunk), 3), round(1 / math.sqrt(1 + n * n), 3), cos(q, chunk) > cos(q, comp))
