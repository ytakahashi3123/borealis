# Calculatetion condition --------------
500000      # Maximum calcuation number
10176486    # Start time (0~10236310 sec)
10186536    # Maximum time, sec
10.0         # Time increment (sec)
1           # TC number for Display (MC routine), 1--8
# Material properties ------------------
6.11d-5      # Thickness, m
274.d0      # Temperaturem K
900.d0      # Density, kg/m3
1.0d3       # Specific heat, J/kg.K
0.2d0       # Conductivity, W/m.K
0.9d0       # Emissivity
200.d0      # Background temperature, K
2.0d0       # Shape factor for blackbody radiation
1.0d0       # Characteristic length, m
7800        # Velocity
# Solar condition ----------------------
10176486 10186536 # Duration that solar radiation occurs
0.0d0              # Coeffiecient for solar radiation
# Ambient condition --------------------
0.7d0		# Prandtl number of air
0.025d0		# Conductivity of air, W/m.K
1.0d-5		# Viscosity, Pa.sec
# Input heatflux -----------------------
.false.              # true:Reading heat flux file, false:Setting in control file
.false.              # true:Set by altitude data, false:set by elapsed time data
11                    # Number of heat flux case
10186536, 10185852, 10184992, 10184663, 10183288, 10182027, 10181325, 10179621, 10179263, 10177587, 10176486 # Aerodynamic heating: Time
200,       190,      180,     170,      160,       150,      140,      130,     120,      110,      100  # Aerodynamic heating: Altitude (dummy)
  0,        0,        0       500,      500,       500,      0,        0,       500,      500,      500  # Aerodynamic heating: Heatflux
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
'/Users/ytakahashi/research/calc/code/heatconduction/heatcond_membraneaeroshell/database/atmospheremodel/atmospheremodel.txt'  # Atmosphere file
'/Users/ytakahashi/research/calc/code/heatconduction/heatcond_membraneaeroshell/database/reference_egg/2017_0715_EGG_ADC_PHY.dat'  # ADC-PHY (flight)
'/Users/ytakahashi/research/calc/code/heatconduction/heatcond_membraneaeroshell/database/reference_egg/2017_0715_EGG_GPS.dat'      # GPS data (flight)
'DSMC_heatflux_TC1.dat'                  # Heat flux file (input)
'heatflux.dat'                        # Heat flux result by Monte Carlo (output)
'temperature_mc.dat'                     # Temperature result by Monte Carlo (output)
'error_mc.dat'                           # Temperature Error by Monte Carlo (output)
'heatflux_ml.dat'                        # Maximum likelihood Heat flux result (output)
'history.dat'	                         # Time hisotry file name (output)
'tc.dat'                                 # Measured temperature file (output)
