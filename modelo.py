from gurobipy import Model, GRB, quicksum, gp

### Conjuntos
I = 0   # Número de minas
J = 0   # Número de depósitos de relaves
K = 0   # Número de procesos mineros
L = 0   # Número de tipos de mineral
Minas = range(1, I+1)              # I
Deposito_relaves = range(1, J+1)   # J
Proceso_minero = range(1, K+1)     # K
Tiempo_meses = range(1, 13)        # T (horizonte de 12 meses)
Mineral = range(1, L+1)            # L

m = gp.Model("Modelo_Proyecto_Minero")

# Variables
x  = m.addVars(Minas, Proceso_minero, Mineral, Tiempo_meses,  vtype=GRB.CONTINUOUS, name="x")  # x_{iklt}
y  = m.addVars(Minas, Deposito_relaves, Tiempo_meses, vtype=GRB.BINARY, name="y")              # y_{ijt}
z  = m.addVars(Minas, Proceso_minero, Mineral, Tiempo_meses,  vtype=GRB.CONTINUOUS, name="z")  # z_{iklt}
u  = m.addVars(Minas, Tiempo_meses, lb=0.0, vtype=GRB.CONTINUOUS, name="u")                    # u_{it}
w  = m.addVars(Deposito_relaves, lb=0.0, vtype=GRB.BINARY, name="w")                           # w_{j}
v  = m.addVars(Proceso_minero, Tiempo_meses, lb=0.0, vtype=GRB.BINARY, name="v")               # v_{kt}

r = []
# Costo operativo de cada depósito de relaves
m.setObjective(
    quicksum(x[i,k,j,t] for i in Minas for k in Proceso_minero for j in Mineral for t in Tiempo_meses) +
    quicksum(y[i,j,t] for i in Minas for j in Deposito_relaves for t in Tiempo_meses) + 
    quicksum(w[j] * r[j] for j in Deposito_relaves),
    GRB.MINIMIZE
)