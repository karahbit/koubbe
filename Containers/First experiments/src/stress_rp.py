#!/usr/bin/env python

import os
import sys
import time

verbose  = os.environ.get('RADICAL_PILOT_VERBOSE', 'REPORT')
os.environ['RADICAL_PILOT_VERBOSE'] = verbose

os.environ['RADICAL_PILOT_PROFILE'] = "True"
os.environ['RADICAL_LOG_LVL'] = "DEBUG"
os.environ['RADICAL_LOG_TGT'] = "radical.log"
os.environ['RADICAL_PROFILE'] = "TRUE"

import radical.pilot as rp
import radical.utils as ru

if __name__ == '__main__':

    start_time = time.time()

    # we use a reporter class for nicer output
    report = ru.Reporter(name='radical.pilot')
    report.title('Getting Started (RP version %s)' % rp.version)

    # use the resource specified as argument, fall back to localhost
    if   len(sys.argv)  > 2: report.exit('Usage:\t%s [resource]\n\n' % sys.argv[0])
    elif len(sys.argv) == 2: resource = sys.argv[1]
    else                   : resource = 'local.localhost'

    # Create a new session. No need to try/except this: if session creation
    # fails, there is not much we can do anyways...
    session = rp.Session()

    # all other pilot code is now tried/excepted.  If an exception is caught, we
    # can rely on the session object to exist and be valid, and we can thus tear
    # the whole RP stack down via a 'session.close()' call in the 'finally'
    # clause...
    try:

        report.header('submit pilots')

        # Add a Pilot Manager. Pilot managers manage one or more ComputePilots.
        pmgr = rp.PilotManager(session=session)

        # Define an [n]-core local pilot that runs for [x] minutes
        # Here we use a dict to initialize the description object
        if (resource == 'local.localhost'):
            pd_init = {'resource'      : resource,
                    'runtime'       : 10,  # pilot runtime (min)
                    'exit_on_error' : True,
                    'cores'         : 8
                    }
        else:
            pd_init = {'resource'      : resource,
                    'runtime'       : 30,  # pilot runtime (min)
                    'exit_on_error' : True,
                    #'project'       : 'TG-MCB090174',
                    #'queue'         : 'development',
                    'project'       : 'mc3bggp',
                    'queue'         : 'RM',
                    'access_schema' : 'gsissh',
                    'cores'         : 1
                    }
        pdesc = rp.ComputePilotDescription(pd_init)

        # Launch the pilot.
        pilot = pmgr.submit_pilots(pdesc)

        report.header('submit units')

        # Register the ComputePilot in a UnitManager object.
        umgr = rp.UnitManager(session=session)
        umgr.add_pilots(pilot)

        # Create a workload of ComputeUnits.

        n = 1   # number of units to run
        report.info('create %d unit description(s)\n\t' % n)

        cuds = list()
        for i in range(0, n):

            # create a new CU description, and fill it.
            # Here we don't use dict initialization.
            cud = rp.ComputeUnitDescription()
            #cud.pre_exec    = ['module load python3', 'export PATH=/home1/06651/tg859507/stress-ng-0.10.16:$PATH']
            #cud.pre_exec    = ['export PATH=/home/karahbit/stress-ng-0.10.16:$PATH']
            #cud.executable  = ['stress-ng']
            #cud.arguments   = ['-c', '1', '-t', '100']
            #cud.executable  = ['docker']
            #cud.arguments   = ['container', 'run', '--rm', 'alexeiled/stress-ng', '-c', '1', '-t', '100']
            cud.pre_exec    = ['module load singularity']
            cud.executable  = ['python3']
            cud.arguments   = ['/home/karahbit/singularity_stress.py']
            #cud.executable  = ['singularity']
            #cud.arguments   = ['version']
            #cud.arguments   = ['exec', '~/alexeiled_stress-ng_alpine-2020-01-14-b494d591b80f.simg', '/stress-ng', '-c', '1', '-t', '100']
            cud.cpu_processes = 1
            cuds.append(cud)
            report.progress()
        report.ok('>>ok\n')

        # Submit the previously created ComputeUnit descriptions to the
        # PilotManager. This will trigger the selected scheduler to start
        # assigning ComputeUnits to the ComputePilots.
        umgr.submit_units(cuds)

        # Wait for all compute units to reach a final state (DONE, CANCELED or FAILED).
        report.header('gather results')
        umgr.wait_units()


    except Exception as e:
        # Something unexpected happened in the pilot code above
        report.error('caught Exception: %s\n' % e)
        ru.print_exception_trace()
        raise

    except (KeyboardInterrupt, SystemExit):
        # the callback called sys.exit(), and we can here catch the
        # corresponding KeyboardInterrupt exception for shutdown.  We also catch
        # SystemExit (which gets raised if the main threads exits for some other
        # reason).
        ru.print_exception_trace()
        report.warn('exit requested\n')

    finally:
        # always clean up the session, no matter if we caught an exception or
        # not.  This will kill all remaining pilots.
        report.header('finalize')
        session.close(download=True)

    report.header()

    print("--- %s seconds ---" % (time.time() - start_time))