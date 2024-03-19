# Calculatetion condition --------------
500000      # Maximum calcuation number
10234520    # Start time (0~10236310 sec)
10235300    # Maximum time, sec
1.0         # Time increment (sec)
1           # TC number for Display (MC routine), 1--8
# Material properties ------------------
6.11d-5      # Thickness, m
265.d0      # Temperaturem K
900.d0      # Density, kg/m3
1.0d3       # Specific heat, J/kg.K
0.2d0       # Conductivity, W/m.K
0.9d0       # Emissivity
200.d0      # Background temperature, K
2.0d0       # Shape factor for blackbody radiation
1.0d0       # Characteristic length, m
7800        # Velocity
# Solar condition ----------------------
10234610, 10235300 # Duration that solar radiation occurs
0.0d0              # Coeffiecient for solar radiation
# Ambient condition --------------------
0.7d0		# Prandtl number of air
0.025d0		# Conductivity of air, W/m.K
1.0d-5		# Viscosity, Pa.sec
# Input heatflux -----------------------
.false.              # true:Set by altitude data, false:set by elapsed time data
8                    # Number of heat flux case
10234510, 10234600, 10234620, 10234660, 10234880,10235120, 10235230, 10235300 # Aerodynamic heating: Time
135, 133, 130, 127, 125, 120, 115, 110         # Aerodynamic heating: Altitude
300, 450, 680, 710, 1000, 1300, 2100, 2900     # Aerodynamic heating: Heatflux
# Atmosphere model (constant) ----------------------
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
69                  # number of variables (ADC)
24                  # (GPS)
# Filename -----------------------------
'/Users/ytakahashi/research/calc/code/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.10/database/atmospheremodel/atmospheremodel.txt'  # Atmosphere file
'/Users/ytakahashi/research/calc/code/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.10/database/reference_egg/2017_0715_EGG_ADC_PHY.dat'  # ADC-PHY (flight)
'/Users/ytakahashi/research/calc/code/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.10/database/reference_egg/2017_0715_EGG_GPS.dat'      # GPS data (flight)
'heatflux.dat'                        # Heat flux result by Monte Carlo (output)
'history.dat'	                      # Time hisotry file name (output)
1                                     # Display verbose: 0:less,  1:more
