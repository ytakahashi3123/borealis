#!/usr/bin/env python3

from mpi4py import MPI


class mpi():

  def __init__(self,config):

    if config['mpi']['flag_mpi']:
      self.MPI = MPI
      self.comm = MPI.COMM_WORLD
      self.rank = MPI.COMM_WORLD.Get_rank()
      self.size = MPI.COMM_WORLD.Get_size()
      self.flag_mpi = True
    else:
      self.rank = 0
      self.size = 1
      self.flag_mpi = False

    return


  # Decorator for time measurement
  def mpitime_measurement_decorated(func):
    @wraps(func)
    def wrapper(*args, **kargs) :
      #text_blue = '\033[94m'
      #text_green = '\033[92m'
      text_yellow = '\033[93m'
      text_end = '\033[0m'
      flag_time_measurement = False
      if flag_time_measurement :
        start_time = self.MPI.time()
        result = func(*args,**kargs)
        elapsed_time = self.MPI.time() - start_time
        if self.rank == 0:
          print('Elapsed time of '+str(func.__name__)+str(':'),text_yellow + str(elapsed_time) + text_end,'s')
      else :
        result = func(*args,**kargs)
      return result 
    return wrapper

#  def mpi_initial_settings(self):

#    comm = MPI.COMM_WORLD
#    rank = comm.Get_rank()
#    size = comm.Get_size()
#    name = MPI.Get_processor_name() 
#    print('Rank:',rank, ', Num process:',size, ', Name:',name)
#    mpi_dict = {'comm':comm, 'rank':rank, 'size':size, 'name':name}

#    return mpi_dict
