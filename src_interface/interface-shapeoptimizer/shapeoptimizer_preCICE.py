#!/usr/bin/env python3

# Borealis adapter (pilot): Python script for Shape Optimization with preCICE.
# Version: shape_optimization_preCICE-v-0.1.0-pilot
# Release date: 2026/04/30

# Author: Yusuke Takahashi, Hokkaido University
# Contact: ytakahashi@eng.hokudai.ac.jp

import os
import sys
import time
#from optparse import OptionParser	# use a parser for configuration
import numpy as np
import precice
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

def load_mapped_data(filename, nDim=2):
    _, ext = os.path.splitext(filename)
    data = []
    if ext == ".csv":
        with open(filename, "r") as f:
            header = f.readline()  # skip header
            for line in f:
                values = line.strip().split(",")
                if nDim == 2 :
                  d = {
                      "sample_point": [float(values[0]), float(values[1])],
                      "nearest_node_id": int(values[3]),
                      "nearest_node_coord": [float(values[4]), float(values[5])],
                      "triangle_id": int(values[7])
                  }
                else:
                  d = {
                      "sample_point": [float(values[0]), float(values[1]), float(values[2])],
                      "nearest_node_id": int(values[3]),
                      "nearest_node_coord": [float(values[4]), float(values[5]), float(values[6])],
                      "triangle_id": int(values[7])
                  }
                data.append(d)
    elif ext == ".dat":
        with open(filename, "r") as f:
            # Skip Tecplot headers
            while True:
                line = f.readline()
                if not line:
                    raise ValueError("ZONE not found in .dat file.")
                if line.strip().startswith("ZONE"):
                    break
            for line in f:
                if not line.strip():
                    continue  # skip empty lines
                values = line.strip().split()
                if nDim == 2 :
                  d = {
                      "sample_point": [float(values[0]), float(values[1])],
                      "nearest_node_id": int(values[3]),
                      "nearest_node_coord": [float(values[4]), float(values[5])],
                      "triangle_id": int(values[7])
                  }
                else:
                  d = {
                      "sample_point": [float(values[0]), float(values[1]), float(values[2])],
                      "nearest_node_id": int(values[3]),
                      "nearest_node_coord": [float(values[4]), float(values[5]), float(values[6])],
                      "triangle_id": int(values[7])
                  }
                data.append(d)
    else:
        raise ValueError("Unsupported file extension. Use .csv or .dat")
    return data

def write_forces_marker(filename, forces, moments):
    with open(filename, 'w') as f:
        line_forces = ' '.join(f"{value:.6e}" for value in np.atleast_1d(forces))
        line_moments = ' '.join(f"{value:.6e}" for value in np.atleast_1d(moments))
        f.write(line_forces + '\n')
        f.write(line_moments + '\n')
    #with open(filename, 'w') as f:
    #    data = np.atleast_2d(data)  # 1Dなら(1,N)の2Dに変換
    #    for row in data:
    #        line = ' '.join(f"{val:.6e}" for val in row)
    #        f.write(line + '\n')

def read_displacements_from_file(filename):
    """
    Displacement データをテキストファイルから読み込む。
    Parameters:
        filename (str): 入力ファイル名
    Returns:
        np.ndarray: (nDeformedMarker, nDim) の 2次元配列
    """
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            data = [list(map(float, line.strip().split())) for line in lines]
        displacements = np.array(data)
        print(f"[INFO] Displacements read from '{filename}'")
        return displacements
    except Exception as e:
        print(f"[ERROR] Failed to read displacements from file: {e}")
        return None

def main():

    # Read control file
    file_control_default = "shapeoptimizer.yml"
    #arg          = orbit.argument(file_control_default)
    #file_control = arg.file
    config       = read_config_yaml(file_control_default)

    with_MPI          = config.get('with_MPI', False) 
    precice_name      = config.get('precice_name', 'Optimizer')
    precice_config    = config.get('precice_config', '../precice-config.xml')
    precice_mesh      = config.get('precice_mesh', 'Optimizer-Mesh')
    nDim              = config.get('nDim', 2)
    in_sequential     = config.get('in_sequential', False)
    step_digit_series = config.get('step_digit_series', 5)

    # Import mpi4py for parallel run
    comm = 0
    rank = 0
    size = 1

    # Configure preCICE:
    try:
#        participant = precice.Participant(options.precice_name, options.precice_config, rank, size)#, comm)
        participant = precice.Participant(precice_name, precice_config, rank, size)#, comm)
    except:
        print("There was an error configuring preCICE")
        return

    mesh_name = precice_mesh

    # Check preCICE + SU2 dimensions
    #if options.nDim != participant.get_mesh_dimensions(mesh_name):
    if nDim != participant.get_mesh_dimensions(mesh_name):
        print("Optimizer and preCICE dimensions are not the same! Exiting")
        return
    
    # Reading file defining coordinates for the shape deformation
#    filename_marker = "marker_points.dat"
    filename_marker = config.get("filename_marker", "marker_points.dat")
    marker_data = load_mapped_data(filename_marker,nDim=nDim)
    marker_coords   = [d["nearest_node_coord"] for d in marker_data]
    #marker_node_ids = [d["nearest_node_id"] for d in marker_data]

    # Get coords of vertices
    nDeformedMarker = len(marker_data)
    coords = np.array( marker_coords )
    print('coords', coords)

    # Set mesh vertices in preCICE:
    try:
        vertex_ids = participant.set_mesh_vertices(mesh_name, coords)
    except:
        print("Could not set mesh vertices for preCICE. Was a (known) mesh specified in the options?")
        return

    # Get read and write data IDs
    # By default:
    #precice_write = "Displacement"
    #precice_read = "Force"
    precice_write = config.get("precice_write", "Displacement")
    precice_read  = config.get("precice_read", "Force")

    # Set arrays for displacements and aerodynamic coefficients
    precice_write_var_initial = config.get("precice_write_var_initial", 0.0)
    precice_readvar_initial   = config.get("precice_read_var_initial", 0.0)

    #displacements = np.ones((nDeformedMarker,options.nDim))*1e-3
    #forces = np.zeros((nDeformedMarker,options.nDim))
    displacements = np.ones((nDeformedMarker,nDim)) * precice_write_var_initial
    forces = np.ones((nDeformedMarker,nDim)) * precice_readvar_initial

    # 下記は物体全体に働く力・・
    forces_object = np.zeros((nDim))

    #center_of_gravity = (0.1, 0.0)
    center_of_gravity = config.get("center_of_gravity", np.zeros((nDim)))
    if len(center_of_gravity) != nDim:
        print('Error, Number of dimension is invalid:',nDim)
        sys.exit()

    # Time variables
    timestep_set = config.get("timestep", 1.e-3)
    iteration_start = config.get("iteration_start", 0)

    time_elapsed = timestep_set * float(iteration_start)
    iteration = iteration_start

    print('Initial settings')
    print('Vertex_IDs:',vertex_ids)
    print('Displacements:',displacements)

    # Read initial displacements data from Borealis for optimization
    if in_sequential:
        step_str = f"{iteration:0{step_digit_series}d}"
        displacements_file = f"displacements_step{step_str}.dat"
    else :
        displacements_file = f"displacements.dat"
    displacements = read_displacements_from_file(displacements_file)
    # Set displacements
    #print('displacements',displacements)

    # Set up initial data for preCICE
    if (participant.requires_initial_data()):
        participant.write_data(mesh_name, precice_write, vertex_ids, displacements)

    # Initialize preCICE
    participant.initialize()

    # Time loop is defined in Python so that we have acces to SU2 functionalities at each time step
    if rank == 0:
        print("Start shape deformation for optimization")
    sys.stdout.flush()

    precice_saved_time = 0
    precice_saved_iter = 0

    while (participant.is_coupling_ongoing()): #(TimeIter < nTimeIter):
        
        # Implicit coupling
        if (participant.requires_writing_checkpoint()):
            precice_saved_time = time_elapsed
            precice_saved_iter = iteration

        # Set the maximum time step allowed by preCICE
        precice_timestep = participant.get_max_time_step_size()

        # Update timestep based on preCICE
        timestep = min(precice_timestep, timestep_set)

        # Read data from Borealis for optimization
        if in_sequential :
            step_str = f"{iteration:0{step_digit_series}d}"
            displacements_file = f"displacements_step{step_str}.dat"
        else:
            displacements_file = f"displacements.dat"
        while not os.path.exists(displacements_file):
          time.sleep(0.1)
        displacements = read_displacements_from_file(displacements_file)
        # Set displacements
        print('Displacements:',displacements)
        # Write data to preCICE
        participant.write_data(mesh_name, precice_write, vertex_ids, displacements)

        # Get data fo aerodynamic forces to evaluate the objective function from preCICE
        forces = participant.read_data(mesh_name, precice_read, vertex_ids, timestep)
        
        # Calculate aerodynamic forces working on marker
        forces_object[:] = 0.0
        for i in range(0,nDeformedMarker):
          forces_object[:] += forces[i,:]
        print('Forces working on object [N]',forces_object)

        # Calculate aerodynamic moments working on marker
        distance_cg = coords + displacements - center_of_gravity
        if nDim == 2:
            moments = (distance_cg[:, 0] * forces[:, 1]- distance_cg[:, 1] * forces[:, 0])
            moments_object = np.sum(moments)
        else:
            moments = np.cross(distance_cg, forces)
            moments_object = np.sum(moments, axis=0)
        print('Moments around rotation center [N.m]:',moments_object)

        # Update control parameters
        iteration += 1
        time_elapsed += timestep
        
        # Advance preCICE
        participant.advance(timestep)

        # Implicit coupling:
        if (participant.requires_reading_checkpoint()):
            time_elapsed = precice_saved_time
            iteration = precice_saved_iter
        
        if participant.is_time_window_complete() :
            # Writing data to Borealis for optimization
            if in_sequential :
                forces_file = f"forces_step{step_str}.dat"
                participant.requires_writing_checkpoint() # これがないと、終了時エラー
                write_forces_marker(forces_file, forces_object, moments_object)
            else:
                forces_file = f"forces.dat"
                participant.requires_writing_checkpoint() # これがないと、終了時エラー
                write_forces_marker(forces_file, forces_object, moments_object)
                break

    participant.finalize()


if __name__ == '__main__':
    main()
