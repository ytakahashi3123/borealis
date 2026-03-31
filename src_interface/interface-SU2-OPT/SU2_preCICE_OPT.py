#!/usr/bin/env python3

# Original source was copied from preCICE SU2 adapter
# Modified by Y.Takahashi for Borealis optimization, 20260430


import sys
from optparse import OptionParser	# use a parser for configuration
import pysu2			            # imports the SU2 wrapped module
import SU2
import numpy
import precice
from time import sleep
import yaml

def read_config_yaml(file_control):
    print("Reading control file...:", file_control)
    try:
      with open(file_control) as file:
        config = yaml.safe_load(file)
    except Exception as e:
      print('Exception occurred while loading YAML...', file=sys.stderr)
      print(e, file=sys.stderr)
      sys.exit(1)
    return config


def update_running_mean(mean, new_value, count):
    return mean + (new_value - mean) / count


def calculate_marker_area(SU2Driver, MarkerID, iVertices_PHYS, nDim):
    """
    指定されたマーカーの表面積を計算する関数
    Args:
        SU2Driver: SU2のドライバオブジェクト (pysu2.PyDriver等)
        MarkerID (int): 面積を計算したいマーカーのインデックス
        iVertices_PHYS (list): このランクが担当する物理頂点のインデックスリスト
        nDim (int): 次元数 (2 or 3)
        comm (MPI.Comm, optional): mpi4pyのコミュニケータ。指定すると全ランクで集計を行う。
    Returns:
        float: マーカーの総表面積
    """
    local_total_area = 0.0    
    if MarkerID is not None:
        for iVertex in iVertices_PHYS:
            # GetVertexNormal(markerID, vertexID, unitNormal=False)
            # unitNormal=Falseにより、ベクトルの長さが「その頂点の寄与面積(Dual cell area)」となる
            normal_vector = SU2Driver.GetVertexNormal(MarkerID, iVertex, False)
            
            # 法線ベクトルのノルム（長さ）を計算
            vert_area_sq = 0.0
            for iDim in range(nDim):
                vert_area_sq += normal_vector[iDim]**2
            
            local_total_area += numpy.sqrt(vert_area_sq)

    return local_total_area


def write_surfacearea_marker(filename, area, area_init):
    with open(filename, 'w') as f:
        header = '# Surface area [m2], Surface area (initial) [m2]\n'
        line = f"{area:.10e}, {area_init:.10e}\n"
        f.write(header + line)


def main():

    # Command line options
    parser=OptionParser()
    parser.add_option("-f", "--file", dest="filename", help="Read config from FILE for SU2", metavar="FILE")
    parser.add_option("--parallel", action="store_true", dest="with_MPI", help="Specify if we need to initialize MPI", default=False)

    # preCICE options with default settings
    #parser.add_option("-p", "--precice-participant", dest="precice_name", help="Specify preCICE participant name", default="Fluid" )
    #parser.add_option("-c", "--precice-config", dest="precice_config", help="Specify preCICE config file", default="../precice-config.xml")
    #parser.add_option("-m", "--precice-mesh", dest="precice_mesh", help="Specify the preCICE mesh name", default="Fluid-Mesh")

    # Dimension
    #parser.add_option("-d", "--dimension", dest="nDim", help="Dimension of fluid domain (2D/3D)", type="int", default=2)
  
    # Sequential
    #parser.add_option("--sequential", action="store_true", dest="with_sequential", help="Sequential process", default=False)

    (options, args) = parser.parse_args()
    options.nZone = int(1)

    # Read control file
    file_control   = "config_su2opt.yml"
    config         = read_config_yaml(file_control)
    ##with_MPI        = config.get('with_MPI', False) 
    precice_name   = config.get('precice_name', 'Fluid')
    precice_config = config.get('precice_config', '../precice-config.xml')
    precice_mesh   = config.get('precice_mesh', 'Fluid-Mesh')
    nDim           = config.get('nDim', 2)
    in_sequential  = config.get('in_sequential', False)

    filename_area = 'surfacearea_su2.dat'

    # SU2 config file
    #config_su2 = SU2.io.Config(options.filename)
    #state  = SU2.io.State()
    #flag_steady = True
    #if config_su2.get('TIME_DOMAIN') == 'YES' :
    #    flag_steady = False
    #flag_restart = True
    #if config_su2.get('RESTART_SOL') == 'NO' :
    #    flag_restart = False
    #print( config_su2.get('TIME_DOMAIN'),state.find_files(config_su2) )

    # Import mpi4py for parallel run
    if options.with_MPI == True:
        from mpi4py import MPI
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        print('Using MPI')
    else:
        comm = 0
        rank = 0
        size = 1
        print('Not using MPI')

    # Initialize the corresponding driver of SU2, this includes solver preprocessing
    try:
        SU2Driver = pysu2.CSinglezoneDriver(options.filename, options.nZone, comm)
    except TypeError as exception:
        print('A TypeError occured in pysu2.CDriver : ',exception)
        return

    # Configure preCICE:
    try:
        participant = precice.Participant(precice_name, precice_config, rank, size)#, comm)
    except:
        print("There was an error configuring preCICE")
        return

#    mesh_name = options.precice_mesh
    mesh_name = precice_mesh

    # Check preCICE + SU2 dimensions
    if nDim != participant.get_mesh_dimensions(mesh_name):
        print("SU2 and preCICE dimensions are not the same! Exiting")
        return

    MovingMarkerID = None
    #MovingMarker = 'interface'       #specified by the user
    MovingMarker = config.get('MovingMarker', 'interface')

    # Get all the tags with the moving option
    MovingMarkerList =  SU2Driver.GetAllDeformMeshMarkersTag()

    # Get all the markers defined on this rank and their associated indices.
    allMarkerIDs = SU2Driver.GetAllBoundaryMarkers()

    # Check if the specified marker has a moving option and if it exists on this rank.
    if MovingMarker in MovingMarkerList and MovingMarker in allMarkerIDs.keys():
        MovingMarkerID = allMarkerIDs[MovingMarker]

    # Number of vertices on the specified marker (per rank)
    nVertex_MovingMarker = 0         #total number of vertices (physical + halo)
    nVertex_MovingMarker_HALO = 0    #number of halo vertices
    nVertex_MovingMarker_PHYS = 0    #number of physical vertices
    iVertices_MovingMarker_PHYS = [] # indices of vertices this rank is working on
    # Datatypes must be primitive as input to SU2 wrapper code, not numpy.int8, numpy.int64, etc.. So a list is used
    
    if MovingMarkerID != None:
        nVertex_MovingMarker = SU2Driver.GetNumberVertices(MovingMarkerID)
        nVertex_MovingMarker_HALO = SU2Driver.GetNumberHaloVertices(MovingMarkerID)
        nVertex_MovingMarker_PHYS = nVertex_MovingMarker - nVertex_MovingMarker_HALO
        
        # Obtain indices of all vertices that are being worked on on this rank
        for iVertex in range(nVertex_MovingMarker):
            if not SU2Driver.IsAHaloNode(MovingMarkerID, iVertex):
                iVertices_MovingMarker_PHYS.append(int(iVertex))
    
    # Get coords of vertices
    coords = numpy.zeros((nVertex_MovingMarker_PHYS, nDim))
    for i, iVertex in enumerate(iVertices_MovingMarker_PHYS):
        coord_passive = SU2Driver.GetInitialMeshCoord(MovingMarkerID, iVertex)
        for iDim in range(nDim):
            coords[i, iDim] = coord_passive[iDim]

    # Set mesh vertices in preCICE:
    try:
        vertex_ids = participant.set_mesh_vertices(mesh_name, coords)
    except:
        print("Could not set mesh vertices for preCICE. Was a (known) mesh specified in the options?")
        return

    # 変形境界の面積計算    
    total_area_tmp = calculate_marker_area(SU2Driver = SU2Driver,MarkerID = MovingMarkerID,iVertices_PHYS = iVertices_MovingMarker_PHYS,nDim = nDim)
    if options.with_MPI == True:
        total_area_init = comm.allreduce(total_area_tmp, op=MPI.SUM)
    else:
        total_area_init = total_area_tmp
    
    # Get read and write data IDs
    # By default:
    #precice_read = "Displacement"
    #precice_write = "Force"
    precice_read  = config.get('precice_read',  'Displacement')
    precice_write = config.get('precice_write', 'Force')

    # Instantiate arrays to hold displacements + forces info
    displacements = numpy.zeros((nVertex_MovingMarker_PHYS,nDim))
    forces = numpy.zeros((nVertex_MovingMarker_PHYS,nDim))
    forces_mean = numpy.zeros((nVertex_MovingMarker_PHYS,nDim))

    # Retrieve some control parameters from the driver
    deltaT = SU2Driver.GetUnsteady_TimeStep()
    TimeIter = SU2Driver.GetTime_Iter()
    nTimeIter = SU2Driver.GetnTimeIter()
    time = TimeIter*deltaT

    # Set up initial data for preCICE
    if (participant.requires_initial_data()):
        for i, iVertex in enumerate(iVertices_MovingMarker_PHYS):
            forces[i] = SU2Driver.GetFlowLoad(MovingMarkerID, iVertex)[:-1]
        forces_mean = forces
        #participant.write_block_vector_data(mesh_name, precice_write, vertex_ids, forces)
        participant.write_data(mesh_name, precice_write, vertex_ids, forces_mean)

    # Initialize preCICE
    participant.initialize()

    # Remov??? Y.Takahashi20250811
    displacements = participant.read_data(mesh_name, precice_read, vertex_ids, deltaT)
    #for i, iVertex in enumerate(iVertices_MovingMarker_PHYS):
    #    print('Disp',TimeIter, i,displacements[i])

    # Sleep briefly to allow for data initialization to be processed
    # This should only be needed on some systems and use cases
    #
    sleep(3)

    # Time loop is defined in Python so that we have acces to SU2 functionalities at each time step
    if rank == 0:
        print("\n------------------------------ Begin Solver -----------------------------\n")
    sys.stdout.flush()
    
    if options.with_MPI == True:
        comm.Barrier()

    precice_saved_time = 0
    precice_saved_iter = 0

    # Coupling loop
    while (participant.is_coupling_ongoing()):#(TimeIter < nTimeIter):
        
        # Implicit coupling
        if (participant.requires_writing_checkpoint()):
            # Save the state
            SU2Driver.SaveOldState()
            precice_saved_time = time
            precice_saved_iter = TimeIter

        # Get the maximum time step size allowed by preCICE
        precice_deltaT = participant.get_max_time_step_size()

        # Retreive data from preCICE
        displacements = participant.read_data(mesh_name, precice_read, vertex_ids, deltaT)
        #for i, iVertex in enumerate(iVertices_MovingMarker_PHYS):
        #  print('Disp',TimeIter, i,displacements[i])
        
        # Set the updated displacements
        for i, iVertex in enumerate(iVertices_MovingMarker_PHYS):
            DisplX = displacements[i][0]
            DisplY = displacements[i][1]
            DisplZ = 0 if nDim == 2 else displacements[i][2]
            SU2Driver.SetMeshDisplacement(MovingMarkerID, iVertex, DisplX, DisplY, DisplZ)
        
        if options.with_MPI == True:
            comm.Barrier()

        # SU2 main routine
        # Update timestep based on preCICE
        deltaT = SU2Driver.GetUnsteady_TimeStep()
        if in_sequential: 
            deltaT = min(precice_deltaT, deltaT)
        SU2Driver.SetUnsteady_TimeStep(deltaT)    

        if in_sequential:
            TimeIter_su2 = 0
            nTimeIter_su2 = 1
        else:
            TimeIter_su2 = TimeIter
            nTimeIter_su2 = nTimeIter

        count_iter = 0
        forces_mean = 0.0
        #while (TimeIter_su2 < nTimeIter_su2):
        for TimeIter_su2 in range(TimeIter_su2, nTimeIter_su2):

            # Time iteration preprocessing (mesh is deformed here)
            SU2Driver.Preprocess(TimeIter)

            # Run one time iteration (e.g. dual-time)
            SU2Driver.Run()

            # Postprocess the solver
            SU2Driver.Postprocess()

            # Update the solver for the next time iteration
            SU2Driver.Update()

            # Monitor the solver
            stopCalc = SU2Driver.Monitor(TimeIter)

            # Loop over the vertices
            participant.requires_reading_checkpoint()
            for i, iVertex in enumerate(iVertices_MovingMarker_PHYS):
                # Get forces at each vertex
                #forces[i] = SU2Driver.GetFlowLoad(MovingMarkerID, iVertex)[:-1]
                load = SU2Driver.GetFlowLoad(MovingMarkerID, iVertex)
                forces[i] = load[:nDim]
            
            count_iter += 1
            #forces_mean += (forces - forces_mean )/count_iter
            forces_mean = update_running_mean(forces_mean, forces, count_iter)

            # Update control parameters
            TimeIter += 1
            time += deltaT

            #TimeIter_su2 += 1

        # Surface area
        total_area_tmp = calculate_marker_area(SU2Driver=SU2Driver, MarkerID=MovingMarkerID, iVertices_PHYS=iVertices_MovingMarker_PHYS, nDim=nDim)
        if options.with_MPI == True:
            total_area = comm.allreduce(total_area_tmp, op=MPI.SUM)
        else:
            total_area = total_area_tmp
        write_surfacearea_marker(filename_area, total_area, total_area_init)

        # Write data to preCICE
        participant.write_data(mesh_name, precice_write, vertex_ids, forces_mean)

        # Advance preCICE
        participant.advance(precice_deltaT)

        # Implicit coupling:
        if (participant.requires_reading_checkpoint()):
            # Reload old state
            SU2Driver.ReloadOldState()
            time = precice_saved_time
            TimeIter = precice_saved_iter

        if (participant.is_time_window_complete()):
            participant.requires_writing_checkpoint()
            SU2Driver.Output(TimeIter)
            if (stopCalc == True):
                break

        if options.with_MPI == True:
            comm.Barrier()

    # Postprocess the solver and exit cleanly
    SU2Driver.Postprocessing()

    participant.finalize()

    if SU2Driver != None:
        del SU2Driver
    
    if options.with_MPI == True:
        MPI.Finalize()
    
    #return

# -------------------------------------------------------------------
#  Run Main Program
# -------------------------------------------------------------------

# this is only accessed if running from command prompt
if __name__ == '__main__':
    main()
