import numpy as np
from UCRL.evi.prova import cython_cn
from UCRL.evi._free_utils import get_mu_and_ci


P = np.array([[  9.96604167e-01  , 1.00000000e-03  , 9.37500000e-04   ,8.33333333e-04,
    6.25000000e-04],
 [  4.96604167e-01  , 5.01000000e-01 ,  9.37500000e-04   ,8.33333333e-04,
    6.25000000e-04],
 [  4.96604167e-01 ,  1.00000000e-03 ,  5.00937500e-01  , 8.33333333e-04,
    6.25000000e-04],
 [  4.96604167e-01  , 1.00000000e-03 ,  9.37500000e-04  , 5.00833333e-01,
    6.25000000e-04],
 [  4.96604167e-01  , 1.00000000e-03 ,  9.37500000e-04  , 8.33333333e-04,
    5.00625000e-01]])
print(P)
n = P.shape[0]

D, U = np.linalg.eig(np.transpose(P))  # eigen decomposition of transpose of P
sorted_indices = np.argsort(np.real(D))
mu = np.transpose(np.real(U))[sorted_indices[-1]]
mu /= np.sum(mu)  # stationary distribution
P_star = np.repeat(np.array(mu, ndmin=2), n, axis=0)  # limiting matrix
# Compute deviation matrix
I = np.eye(n)  # identity matrix
Z = np.linalg.inv(I - P + P_star)  # fundamental matrix
DM = np.dot(Z, I - P_star)  # deviation matrix

print(D)
print(U)
print(mu)
print("DM")
print(DM)
print("-"*80)
get_mu_and_ci(P)

exit(9)

print('-'*80)
H = np.array([
    [-1.01,   0.86 , -4.60,   3.31 , -4.81],
     [3.98  , 0.53 , -7.04 ,  5.29 ,  3.55],
     [3.30,   8.26 , -3.89 ,  8.20 , -1.51],
     [4.43  , 4.96 , -7.66 , -7.33 ,  6.18],
     [7.31 , -6.43 , -6.16 ,  2.47 ,  5.58]])
n = H.shape[0]
D, U = np.linalg.eig(H)  # eigen decomposition of transpose of P
sorted_indices = np.argsort(np.real(D))
print(sorted_indices)
print(np.real(U))
print()
print(np.transpose(np.real(U)))
print()
mu = np.transpose(np.real(U))[sorted_indices[-1]]
#mu /= np.sum(mu)  # stationary distribution
P_star = np.repeat(np.array(mu, ndmin=2), n, axis=0)  # limiting matrix
# Compute deviation matrix
I = np.eye(n)  # identity matrix
Z = np.linalg.inv(I - H + P_star)  # fundamental matrix
DM = np.dot(Z, I - P_star)  # deviation matrix
condition_nb = 0  # condition number of deviation matrix
for i in range(0, n):  # Seneta's condition number
    for j in range(i + 1, n):
        condition_nb = max(condition_nb, 0.5 * np.linalg.norm(DM[i, :] - DM[j, :], ord=1))
print(D)
print()
# print(U)
print(mu)
print()
print(P_star)
print()
print(DM)
print()
print('-'*80)
cython_cn(H, 5)
print('-'*80)
print(DM)
print(condition_nb)