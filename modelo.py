from gurobipy import Model, GRB, quicksum, gp

### Conjuntos
I =  166                            # Número de minas
J = 352                             # Número de depósitos de relaves
K = 0                              # Número de procesos mineros
L = 14                              # Número de tipos de mineral 

Minas = range(1, I+1)              # I
Deposito_relaves = range(1, J+1)   # J
Proceso_minero = range(1, K+1)     # K
Tiempo_meses = range(1, 13)        # T (horizonte de 12 meses)
Mineral = range(1, L+1)            # L

### Parámetros
P = []
v = []
A = []
d = []
a = []
b = 0.0
r = []
delta = []
f = []
rho = []
e = []
c = 0.0
g = []
h = 0.0
q = []
# ... (rellenar)


### Modelo

m = gp.Model("Modelo_Proyecto_Minero")

#### Variables (la naturaleza se define acá) (lb=lower bound, vtype=variable type)
x  = m.addVars(Minas, Proceso_minero, Mineral, Tiempo_meses, lb=0.0, vtype=GRB.CONTINUOUS, name="x")       # x_{iklt}
y  = m.addVars(Minas, Deposito_relaves, Tiempo_meses, lb=0.0, vtype=GRB.CONTINUOUS, name="y")              # y_{ijt}
z  = m.addVars(Minas, Proceso_minero, Mineral, Tiempo_meses,  lb=0.0, vtype=GRB.CONTINUOUS, name="z")      # z_{iklt}
u  = m.addVars(Minas, Tiempo_meses, lb=0.0, vtype=GRB.CONTINUOUS, name="u")                                # u_{it}
w  = m.addVars(Deposito_relaves, vtype=GRB.BINARY, name="w")                                               # w_{j}
V  = m.addVars(Proceso_minero, Tiempo_meses, vtype=GRB.BINARY, name="V")                                   # v_{jt}

#### Función Objetivo
m.setObjective(
    quicksum(x[i,k,j,t] for i in Minas for k in Proceso_minero for j in Mineral for t in Tiempo_meses) +
    quicksum(y[i,j,t] for i in Minas for j in Deposito_relaves for t in Tiempo_meses) + 
    quicksum(w[j] * r[j] for j in Deposito_relaves),
    GRB.MINIMIZE
)

#### Restricciones
# No sobrepasar peso máximo de relaves
m.addConstrs(quicksum(y[i,j,t] for i in Minas for t in Tiempo_meses) <= P[j] for j in Deposito_relaves)  
# No se debe sobrepasar volumen máximo permitido de relave
m.addConstrs(quicksum(y[i,j,t] * e[j] for i in Minas for t in Tiempo_meses) <= v[j] for j in Deposito_relaves)
# Se tien que hacer una inspeccion anual en el deposito
m.addConstrs(quicksum(V[j,t] for t in Tiempo_meses) == 1 for j in Deposito_relaves)
# Se debe usar menos del 10% de agua continental producida
m.addConstrs(quicksum(x[i,k,l,t] for i in Minas for k in Proceso_minero for l in Mineral) <= 0.1 * h for t in Tiempo_meses)
# Cada mineral debe satisfacer una demanda
m.addConstrs(quicksum(z[i,k,l,t] for i in Minas for k in Proceso_minero) >= d[l,t] for l in Mineral for t in Tiempo_meses)
# Cada proceso minero necesita ocupar agua en cierta cantidad
m.addConstrs(quicksum(x[i,k,l,t] for i in Minas) >= quicksum(a[k,l] * z[i,k,l,t] for i in Minas) for k in Proceso_minero for l in Mineral for t in Tiempo_meses)
# Cada mina no puede superar una cantidad máxima de agua disponible
m.addConstrs(quicksum(x[i,k,l,t] for k in Proceso_minero for l in Mineral for t in Tiempo_meses) <= A[i] for i in Minas)
# Si el deposito está inactivo, no se puede depositar material en él
m.addConstrs(quicksum(y[i,j,t] for i in Minas) <= P[j] * w[j] for j in Deposito_relaves for t in Tiempo_meses)
# Al procesar mineral, se genera relave, este puede transportarse hacia un deposito o quedarse en la mina
m.addConstrs(u[i,t] + quicksum(y[i,j,t] for j in Deposito_relaves) == u[i-1] + quicksum(rho[k,l] * z[i,k,l,t] for k in Proceso_minero for l in Mineral) for i in Minas for t in Tiempo_meses)
m.addConstrs(u[i,0] == 0 for i in Minas)  # Condición inicial de relaves en minas
# El presupuseto está dado por utilizar agua, por las inspecciones anuales y el gasto por transporte de relave
m.addConstr(
    quicksum(x[i,k,l,t] * f[k] for i in Minas for k in Proceso_minero for l in Mineral for t in Tiempo_meses) +
    quicksum(V[j,t] * delta[j] for j in Deposito_relaves for t in Tiempo_meses) +
    c * (quicksum(g[i,j] for i in Minas for j in Deposito_relaves))
    <= b
)
# Cota máxima para los desechos acumulados
m.addConstrs(u[i,t] <= q[i] for i in Minas for t in Tiempo_meses)
