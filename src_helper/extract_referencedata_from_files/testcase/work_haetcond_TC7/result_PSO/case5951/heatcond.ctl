# Calculatetion condition --------------
500000      # Maximum calcuation number
10181685    # Start time (0~10236310 sec)
10186747    # Maximum time, sec
10.0         # Time increment (sec)
1           # TC number for Display (MC routine), 1--8
# Material properties ------------------
6.11d-5      # Thickness, m
250.d0      # Temperaturem K
900.d0      # Density, kg/m3
1.0d3       # Specific heat, J/kg.K
0.2d0       # Conductivity, W/m.K
0.9d0       # Emissivity
200.d0      # Background temperature, K
2.0d0       # Shape factor for blackbody radiation
1.0d0       # Characteristic length, m
7800        # Velocity
# Solar condition ----------------------
10181685 10186747 # Duration that solar radiation occurs
0.0d0              # Coeffiecient for solar radiation
# Ambient condition --------------------
0.7d0		# Prandtl number of air
0.025d0		# Conductivity of air, W/m.K
1.0d-5		# Viscosity, Pa.sec
# Input heatflux -----------------------
.false.              # true:Set by altitude data, false:set by elapsed time data
21                   # Number of heat flux case
10181685.0, 10181938.1, 10182191.2, 10182444.3, 10182697.4, 10182950.5, 10183203.6, 10183456.7, 10183709.8, 10183962.9, 10184216.0, 10184469.1, 10184722.2, 10184975.3, 10185228.4, 10185481.5, 10185734.6, 10185987.7, 10186240.8, 10186493.9, 10186747.0 # Aerodynamic heating: Time
200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200,200  # Aerodynamic heating: Altitude (dummy)
267.7056776823155, 375.4039496687248, 447.3834996840502, 468.6720505000232, 468.67292167880464, 474.360733454469, 504.645671882092, 556.4194373066236, 564.2876062504873, 509.8118757259204, 505.08539181048343, 481.8303864627849, 444.4854331382574, 182.8377195071163, 180.5260086470811, 159.9098254606616, 140.2891070773025, 126.22732865025755, 109.09226334780882, 114.10485718130926, 78.91028227224177 # Aerodynamic heating: Heatflux
# Atmosphere model (constant) ----------------------
1                   # 1: File reading, 2: Parameter setting
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
1                   # 1: File reading, 2: Parameter setting
300.0               # Altitude set, km
69                  # number of variables (ADC)
24                  # (GPS)
# Filename -----------------------------
'/opt/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.3.0/database/atmospheremodel/atmospheremodel.txt'  # Atmosphere file
'/opt/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.3.0/database/reference_egg/2017_0715_EGG_ADC_PHY.dat'  # ADC-PHY (flight)
'/opt/heatconduction/heatcond_membraneaeroshell/heatcond_membraneaeroshell_ver1.3.0/database/reference_egg/2017_0715_EGG_GPS.dat'      # GPS data (flight)
'heatflux.dat'                        # Heat flux result by Monte Carlo (output)
'history.dat'	                        # Time hisotry file name (output)
0                                     # Display verbose: 0:less,  1:more
