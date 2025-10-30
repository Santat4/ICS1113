# from gurobipy import Model, GRB, quicksum, gp
import pandas as pd


def cargar_parametro_con_J(csv_filename, columnabuscada ,J_depositos):
    P_dict = {}
    try:
        # Cargar el dataframe
        df = pd.read_csv(csv_filename)
        
        # 1. Verificar que el J coincida con las filas
        if len(df) != J_depositos:
            print(f"¡Advertencia! Tu J={J_depositos} no coincide con las {len(df)} filas del CSV.")
            print(f"Se usará el número de filas del CSV: {len(df)}")
            J_depositos = len(df) # Ajusta J al tamaño real del archivo

        print(f"CSV '{csv_filename}' cargado. J={J_depositos} coincide con las {len(df)} filas.")

        # 2. Seleccionar la columna
        if columnabuscada not in df.columns:
            print(f"Error Crítico: La columna '{columnabuscada}' no se encontró en el archivo.")
            return {}

        # 3. Extraer, limpiar (reemplazar NaNs por 0) y convertir a kg
        print(f"Limpiando {df[columnabuscada].isna().sum()} valores nulos en '{columnabuscada}' y convirtiendo a kg.")
        if columnabuscada == 'TONELAJE_AUTORIZADO':
            valores_P = df[columnabuscada].fillna(0) * 1000
        else:
            valores_P = df[columnabuscada].fillna(0)

        # 4. Convertir a lista
        lista_valores_P = valores_P.tolist()
        
        # 5. Crear el diccionario con llaves de 1 a J
        # Gurobi usará P[j] donde j está en range(1, J+1)
        # El diccionario mapea {1 -> fila 0, 2 -> fila 1, ...}
        P_dict = {j: lista_valores_P[j-1] for j in range(1, J_depositos + 1)}
        
        print("Diccionario P[j] creado exitosamente.")
        return P_dict

    except FileNotFoundError:
        print(f"Error Crítico: No se pudo encontrar el archivo '{csv_filename}'.")
        return {}
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return {}


### Conjuntos
I =  157                            # Número de minas
J = 310                             # Número de depósitos de relaves
K = 4                               # Número de procesamiento mineros (Flotacion, Lixiviación, gravimetrico, Magnetico)
L = 6                               # Número de tipos de mineral (oro, plata, cobre, caliza, molibdeno, Hierro)

Minas = range(1, I+1)              # I
Deposito_relaves = range(1, J+1)   # J
Proceso_minero = range(1, K+1)     # K
Tiempo_meses = range(1, 13)        # T (horizonte de 12 meses)
Mineral = range(1, L+1)            # L

### Parámetros
nombre_archivo = "Filtradas activas inactivas.csv"
P = cargar_parametro_con_J(nombre_archivo,'TONELAJE_AUTORIZADO', J)
v = cargar_parametro_con_J(nombre_archivo,'VOL_AUTORIZADO', J)

# https://www.sernageomin.cl/pdf/anuario/Anuario_de_la_mineria_de_chile_2023_web.pdf
demanda_anual_kg = {
    1: 5372694 * 1000,   # Cobre
    2: 1262287,           # Plata
    3: 35790,             # Oro
    4: 44127 * 1000,      # Molibdeno
    5: 5250584 * 1000,    # Caliza
    6: 11443370 * 1000    # Hierro
}

demanda_mensual_kg = {l: demanda_anual_kg[l] / 12 for l in demanda_anual_kg}
d = {(l, t): demanda_mensual_kg[l] for l in Mineral for t in Tiempo_meses} #Demanda por el mineral l en el periodo de tiempo t (kg)

b = 1200000000  #CLP https://www.dipres.gob.cl/597/articles-133289_doc_pdf.pdf
c = 0.00004 #CLP/(kg·m) https://www.argentina.gob.ar/sites/default/files/instructivo_simplificado-_mcc_web_v1_mayo_2019_dnptcyl.pdf#:~:text=Argentina,Costo%20por%20km
h = 7691666666.67 # Agua continental disponible mensualmente en m^3 (anualmente es 923000000000) https://aqua-lac.org/index.php/Aqua-LAC/article/download/365/312
e = 0.00071 # https://www.sernageomin.cl/wp-content/uploads/2023/03/PÚBLICA_GeoquimicaRelavesChile23032023.pdf#:~:text=,En%20este%20campo
f = 1000 #CLP #https://www.latercera.com/pulso-pm/noticia/siete-veces-mas-caro-como-el-uso-de-agua-desalada-impacta-en-la-rentabilidad-de-los-proyectos-mineros/LWXUX4VEOZFWROZ5UQPOES4UTM

A = []
a = []
r = []
delta = []
rho = []
g = []
q = []
# ... (rellenar)

### Modelo
'''
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
# No sobrepasar peso máximo de relaves.
m.addConstrs(quicksum(y[i,j,t] for i in Minas for t in Tiempo_meses) <= (P[j] * w[j]) for j in Deposito_relaves)
# No se debe sobrepasar volumen máximo permitido de relave.
m.addConstrs(quicksum(y[i,j,t] * e[j] for i in Minas for t in Tiempo_meses) <= v[j] for j in Deposito_relaves)
# Se tiene que hacer una inspección anual en el depósito.
m.addConstrs(quicksum(V[j,t] for t in Tiempo_meses) == 1 for j in Deposito_relaves)
# Se debe usar menos del 10% de agua continental producida.
m.addConstrs(quicksum(x[i,k,l,t] for i in Minas for k in Proceso_minero for l in Mineral) <= 0.1 * h for t in Tiempo_meses)
# Cada mineral debe satisfacer una demanda.
m.addConstrs(quicksum(z[i,k,l,t] for i in Minas for k in Proceso_minero) >= d[l,t] for l in Mineral for t in Tiempo_meses)
# Cada proceso minero necesita ocupar agua en cierta cantidad.
m.addConstrs(quicksum(x[i,k,l,t] for i in Minas) >= quicksum(a[k,l] * z[i,k,l,t] for i in Minas) for k in Proceso_minero for l in Mineral for t in Tiempo_meses)
# Cada mina no puede superar una cantidad máxima de agua disponible.
m.addConstrs(quicksum(x[i,k,l,t] for k in Proceso_minero for l in Mineral for t in Tiempo_meses) <= A[i] for i in Minas)
# Si el deposito está inactivo, no se puede depositar material en él.
m.addConstrs(quicksum(y[i,j,t] for i in Minas) <= (P[j] * w[j]) for j in Deposito_relaves for t in Tiempo_meses)
# Al procesar mineral, se genera relave, este puede transportarse hacia un deposito o quedarse en la mina.
m.addConstrs(u[i,t] + quicksum(y[i,j,t] for j in Deposito_relaves) == u[i-1] + quicksum(rho[k,l] * z[i,k,l,t] for k in Proceso_minero for l in Mineral) for i in Minas for t in Tiempo_meses)
m.addConstrs(u[i,0] == 0 for i in Minas)  # Condición inicial de relaves en minas.
# El presupuesto está dado por utilizar agua, por las inspecciones anuales y el gasto por transporte de relave.
m.addConstr(
    quicksum(x[i,k,l,t] * f[k] for i in Minas for k in Proceso_minero for l in Mineral for t in Tiempo_meses) +
    quicksum(V[j,t] * delta[j] for j in Deposito_relaves for t in Tiempo_meses) +
    c * (quicksum((g[i,j] * y[i,j,t]) for i in Minas for j in Deposito_relaves for t in Tiempo_meses))
    <= b
)
# Cota máxima para los desechos acumulados.
m.addConstrs(u[i,t] <= q[i] for i in Minas for t in Tiempo_meses)
'''