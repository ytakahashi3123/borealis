# Calculatetion condition --------------
500000      # Maximum calcuation number
0           # Start time (0~10236310 sec)
100000      # Maximum time, sec
10.0         # Time increment (sec)
1           # TC number for Display (MC routine), 1--8
# Material properties ------------------
1.d-4       # Thickness, m
300.d0      # Temperaturem K
1000.d0      # Density, kg/m3
1.0d3       # Specific heat, J/kg.K
0.2d0       # Conductivity, W/m.K
0.9d0       # Emissivity
200.d0      # Background temperature, K
2.0d0       # Shape factor for blackbody radiation
1.0d0       # Characteristic length, m
7800        # Velocity
# Solar condition ----------------------
0 100000    # Duration that solar radiation occurs
0.0d0       # Coeffiecient for solar radiation
# Ambient condition --------------------
0.7d0		# Prandtl number of air
0.025d0		# Conductivity of air, W/m.K
1.0d-5		# Viscosity, Pa.sec
# Input heatflux -----------------------
.false.              # true:Set by altitude data, false:set by elapsed time data
21                   # Number of heat flux case
0.0, 5000.0, 10000.0, 15000.0, 20000.0, 25000.0, 30000.0, 35000.0, 40000.0, 45000.0, 50000.0, 55000.0, 60000.0, 65000.0, 70000.0, 75000.0, 80000.0, 85000.0, 90000.0, 95000.0, 100000.0 # Aerodynamic heating: Time
200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200  # Aerodynamic heating: Altitude (dummy)
732.260078878219, 386.8660467479343, 525.161645256603, 164.98059245116625, 350.4145410995614, 402.43269104478816, 858.4164156504579, 212.6675606533954, 322.0935428103617, 775.7943034456384, 1038.6495398686689, 158.34325409155747, 1957.9703292156416, 1785.9984249439324, 1612.8700612954892, 344.6285482302418, 1450.1118980492756, 552.4841994826533, 1278.4014753011136, 306.3111777361429, 1174.821070305121 # Aerodynamic heating: Heatflux
# Atmosphere model (constant) ----------------------
2                   # 1: File reading, 2: Parameter setting
1.e-3               # Density, kg
300.e0              # Temperature, K
7                   # Number of parameter
"Height", "km"      # Parameters
"O", "cm-3" 
"N2", "cm-3"
"O2", "cm-3"
"Mass_density", "g/cm-3"
"Temperature_neutral", "K"
"N", "cm-3"
# Flight -------------------------------
2                   # 1: File reading, 2: Parameter setting
300.0               # Altitude set, km
69                  # number of variables (ADC)
24                  # (GPS)
# Filename -----------------------------
'/opt/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.30/database/atmospheremodel/atmospheremodel.txt'  # Atmosphere file
'/opt/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.30/database/reference_egg/2017_0715_EGG_ADC_PHY.dat'  # ADC-PHY (flight)
'/opt/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.30/database/reference_egg/2017_0715_EGG_GPS.dat'      # GPS data (flight)
'heatflux.dat'                        # Heat flux result by Monte Carlo (output)
'history.dat'	                        # Time hisotry file name (output)
0                                     # Display verbose: 0:less,  1:more
