''' KGen Application '''

import sys
import os
import glob
import optparse
import subprocess

KGEN_APP = os.path.dirname(os.path.realpath(__file__))
KGEN_HOME = '%s/../..'%KGEN_APP
KEXT_TOOL = '%s/kgenapps/kernel_extractor'%KGEN_HOME
COMPFLAG_TOOL = '%s/kgenapps/compflag_detector'%KGEN_HOME
COVERAGE_TOOL = '%s/kgenapps/coverage_detector'%KGEN_HOME

sys.path.insert(0, '%s/base'%KGEN_HOME)
sys.path.insert(0, COMPFLAG_TOOL)
sys.path.insert(0, COVERAGE_TOOL)
sys.path.insert(0, KEXT_TOOL)
sys.path.insert(0, KGEN_APP)

from kgen_utils import UserException, ProgramException, Logger, Config, run_shcmd
from kgen_state import State
from kgen_analyze import analyze

def main():
    from compflag_tool import CompFlagDetect
    from coverage_tool import CoverageDetect
    from kext_tool import KExtTool

    version = [ 0, 7, '2' ]
    outdir = '.'
    retval = 0

    Logger.info('Starting KGen', stdout=True)

    # add options for all of kgen tools
    try:
        # option parser
        parser = optparse.OptionParser(version='KGEN version %d.%d.%s'%tuple(version))

        # common options
        parser.add_option("--outdir", dest="outdir", action='store', type='string', default=None, help="path to create outputs")
        parser.add_option("--rebuild", dest="rebuild", action='append', type='string', default=None, help="force to rebuild")
        parser.add_option("--prerun", dest="prerun", action='append', type='string', default=None, help="prerun commands")
        parser.add_option("-i", "--include-ini", dest="include_ini", action='store', type='string', default=None, help="INI options")
        parser.add_option("--debug", dest="debug", action='append', type='string', help=optparse.SUPPRESS_HELP)


        # kapp options
        parser.add_option("-c", "--cmd-clean", dest="cmd_clean", action='store', type='string', default=None, help="Linux command(s) to clean a target application build")
        parser.add_option("-b", "--cmd-build", dest="cmd_build", action='store', type='string', default=None, help="Linux command(s) to build a target application")
        parser.add_option("-r", "--cmd-run", dest="cmd_run", action='store', type='string', default=None, help="Linux command(s) to run a target application")

        # compflag options
        parser.add_option("--strace", dest="strace", action='store', type='string', default=None, help="strace options")

        # coverage options
        #parser.add_option("--strace", dest="strace", action='store', type='string', default=None, help="strace options")

        # kext options
        parser.add_option("--invocation", dest="invocation", action='append', type='string', default=None, help="(process, thread, invocation) pairs of kernel for data collection")
        parser.add_option("-e", "--exclude-ini", dest="exclude_ini", action='store', type='string', default=None, help="information excluded for analysis")
        parser.add_option("--kernel-option", dest="kernel_option", action='append', type='string', default=None, help="compiler and linker options for Kgen-generated kernel")
        parser.add_option("--openmp", dest="openmp", action='append', type='string', default=None, help="Specifying OpenMP options")
        parser.add_option("--mpi", dest="mpi", action='append', type='string', default=None, help="MPI information for data collection")
        parser.add_option("--timing", dest="timing", action='append', type='string', default=None, help="Timing measurement information")
        parser.add_option("--intrinsic", dest="intrinsic", action='append', type='string', default=None, help="Specifying resolution for intrinsic procedures during searching")
        parser.add_option("--check", dest="check", action='append', type='string', default=None, help="Kernel correctness check information")
        parser.add_option("--verbose", dest="verbose", action='store', type='string', default=None, help="Set the verbose level for verification output")
        parser.add_option("--add-mpi-frame", dest="add_mpi_frame", type='string', default=None, help='Add MPI frame codes in kernel_driver.')
        parser.add_option("--source", dest="source", action='append', type='string', default=None, help="Setting source file related properties")
        parser.add_option("--logging", dest="logging", action='append', type='string', help=optparse.SUPPRESS_HELP)

        opts, args = parser.parse_args()

        if len(args)<1:
            print 'ERROR: Target source files is not provided.'
            print 'Usage: kgen [options] <target file path[:namepath]> --cmd-clean <commands> --cmd-build <commands> --cmd-run <commands>'
            sys.exit(-1)

        if opts.cmd_clean is None:
            print 'ERROR: No clean command is prvoided in command line. Please add --cmd-clean option.'
            print 'Usage: kgen [options] <target file path[:namepath]> --cmd-clean <commands> --cmd-build <commands> --cmd-run <commands>'
            sys.exit(-1)

        if opts.cmd_build is None:
            print 'ERROR: No build command is prvoided in command line. Please add --cmd-build option.'
            print 'Usage: kgen [options] <target file path[:namepath]> --cmd-clean <commands> --cmd-build <commands> --cmd-run <commands>'
            sys.exit(-1)

        if opts.cmd_run is None:
            print 'ERROR: No run command is prvoided in command line. Please add --cmd-run option.'
            print 'Usage: kgen [options] <target file path[:namepath]> --cmd-clean <commands> --cmd-build <commands> --cmd-run <commands>'
            sys.exit(-1)

        # seletively copy user inputs for each kgen tools
        compflag_argv = []
        coverage_argv = []
        kext_argv = []
        #kgen_argv = []

        # collect common options
        if opts.outdir:
            kext_argv.append('--outdir')
            kext_argv.append(opts.outdir)
            compflag_argv.append('--build')
            compflag_argv.append('cwd="%s",clean="%s"'%(opts.outdir, opts.cmd_clean))
            coverage_argv.append('--outdir')
            coverage_argv.append(opts.outdir)
            outdir = opts.outdir
            if not os.path.exists(outdir):
                os.mkdir(outdir)
        else:
            kext_argv.append('--outdir')
            kext_argv.append(os.getcwd())
            compflag_argv.append('--build')
            compflag_argv.append('cwd="%s",clean="%s"'%(os.getcwd(), opts.cmd_clean))
            coverage_argv.append('--outdir')
            coverage_argv.append(os.getcwd())
            outdir = os.getcwd()

        if opts.prerun:
            coverage_argv.append('--prerun')
            coverage_argv.extend(opts.prerun)
            compflag_argv.append('--prerun')
            compflag_argv.extend(opts.prerun)
            kext_argv.append('--prerun')
            kext_argv.extend(opts.prerun)
        if opts.rebuild:
            coverage_argv.append('--rebuild')
            coverage_argv.extend(opts.rebuild)
            compflag_argv.append('--rebuild')
            compflag_argv.extend(opts.rebuild)
            kext_argv.append('--rebuild')
            kext_argv.extend(opts.rebuild)
        if opts.include_ini:
            compflag_argv.append('--include_ini')
            compflag_argv.append(opts.include_ini)
            kext_argv.append('--include-ini')
            kext_argv.append(opts.include_ini)
        if opts.debug:
            coverage_argv.append('--debug')
            coverage_argv.extend(opts.debug)
            compflag_argv.append('--debug')
            compflag_argv.extend(opts.debug)
            kext_argv.append('--debug')
            kext_argv.extend(opts.debug)

        # collect compflag options
        if opts.strace:
            compflag_argv.append('--strace')
            compflag_argv.append(opts.strace)

        compflag_argv.append(opts.cmd_build)

        # collect coverage options

        coverage_argv.append('--cmd-clean')
        coverage_argv.append(opts.cmd_clean)
        coverage_argv.append('--cmd-build')
        coverage_argv.append(opts.cmd_build)
        coverage_argv.append('--cmd-run')
        coverage_argv.append(opts.cmd_run)
        coverage_argv.append(args[0])

        # collect kext options
        if opts.invocation:
            kext_argv.append('--invocation')
            kext_argv.extend(opts.invocation)
        if opts.exclude_ini:
            kext_argv.append('--exclude-ini')
            kext_argv.append(opts.exclude_ini)
        if opts.source:
            kext_argv.append('--source')
            kext_argv.extend(opts.source)
        if opts.mpi:
            kext_argv.append('--mpi')
            kext_argv.extend(opts.mpi)
        if opts.openmp:
            kext_argv.append('--openmp')
            kext_argv.extend(opts.openmp)
        if opts.timing:
            kext_argv.append('--timing')
            kext_argv.extend(opts.timing)
        if opts.intrinsic:
            kext_argv.append('--intrinsic')
            kext_argv.extend(opts.intrinsic)
        if opts.check:
            kext_argv.append('--check')
            kext_argv.extend(opts.check)
        if opts.kernel_option:
            kext_argv.append('--kernel-option')
            kext_argv.extend(opts.kernel_option)
        if opts.verbose:
            kext_argv.append('--verbose')
            kext_argv.append(opts.verbose)
        if opts.add_mpi_frame:
            kext_argv.append('--add-mpi-frame')
            kext_argv.append(opts.add_mpi_frame)
        if opts.logging:
            kext_argv.append('--logging')
            kext_argv.extend(opts.logging)

        kext_argv.append('--state-clean')
        kext_argv.append('cmds=%s'%opts.cmd_clean)
        kext_argv.append('--state-build')
        kext_argv.append('cmds=%s'%opts.cmd_build)
        kext_argv.append('--state-run')
        kext_argv.append('cmds=%s'%opts.cmd_run)
        kext_argv.append(args[0])

        # run compflag
        compflag = CompFlagDetect()
        compflag.init(argv=compflag_argv)
        compflag.main()
        CF_flags = compflag.fini()

        Config.apply()

        analyze()

        #kext = KExtTool()
        #kext.init()

        # collect command line inputs and parse
        #kgen_argv.extend(kext_argv)
        #Config.apply(argv=kgen_argv)


        if not opts.invocation:
            coverage = CoverageDetect()
            coverage.init(argv=coverage_argv)

            #Logger.info('Program is analyzed', stdout=True)

            coverage_argv.append(opts.cmd_clean)
            coverage_argv.append(opts.cmd_build)
            coverage_argv.append(opts.cmd_run)

            # run coverage
            coverage.main()

            # parse coverage rebuild option
            is_rebuild_coverage = False
            if opts.rebuild:
                for r in opts.rebuild:
                    if isinstance(r, str):
                        subopts = r.split(',')
                        for subopt in subopts:
                            if subopt in [ 'all', 'coverage' ]:
                                is_rebuild_coverage = True
                    if is_rebuild_coverage: break
                             
            # check if coverage file exist
            has_coveragefile = False
            if os.path.exists('%s/coverage'%outdir):
                coveragefile = glob.glob('%s/coverage/%s.*'%(outdir, State.kernel['name']))
                if len(coveragefile)>0:
                    has_coveragefile = True
                    
            # generate coverage file
            if is_rebuild_coverage or not has_coveragefile:
                Logger.info('Generating coverage file at %s/coverage'%outdir, stdout=True) 
                out, err, retcode = run_shcmd('make', cwd='%s/coverage'%outdir)
                if retcode != 0:
                    Logger.info('FAILED: %s'%err, stdout=True) 
            else:
                Logger.info('Reusing coverage at %s/coverage'%outdir, stdout=True) 

            CV_flags = coverage.fini()

            kext_argv.extend( [ '--invocation', CV_flags['invocation']] )


        kext_argv.extend( [ '-i', CF_flags['incini'] ] )

        kext = KExtTool()
        kext.init()

        # run kext
        kext.main()
        extracts = kext.fini()
        # extracts contain kernel files, state files

        # parse kext rebuild option
        is_rebuild_kext = False
        if opts.rebuild:
            for r in opts.rebuild:
                if isinstance(r, str):
                    subopts = r.split(',')
                    for subopt in subopts:
                        if subopt in [ 'all', 'state' ]:
                            is_rebuild_kext = True
                if is_rebuild_kext: break
                         
        # check if state files exist
        has_statefiles = False
        if os.path.exists('%s/kernel'%outdir):
            statefiles = glob.glob('%s/kernel/%s.*.*.*'%(outdir, State.kernel['name']))
            if len(statefiles)>0:
                has_statefiles = True
                
        # generate state
        if is_rebuild_kext or not has_statefiles:
            Logger.info('Generating state data files at %s/state.'%outdir, stdout=True) 
            out, err, retcode = run_shcmd('make clean', cwd='%s/state'%outdir)
            out, err, retcode = run_shcmd('make run', cwd='%s/state'%outdir)
            if retcode != 0:
                Logger.info('FAILED: %s'%err, stdout=True) 
        else:
            Logger.info('Reusing state data files at %s/kernel'%outdir, stdout=True) 

    except UserException as e:
        print 'ERROR: %s'%str(e)
        Logger.info(e)
        #Logger.critical(e)
        retval = -1
    except ProgramException as e:
        Logger.critical(e)
        retval = -1
    except Exception as e:
        Logger.critical(e)
        retval = -1
    finally:
        if os.path.exists('%s/state/Makefile'%outdir):
            out, err, retcode = run_shcmd('make recover_from_locals', cwd='%s/state'%outdir)

    Logger.info('KGen is finished.', stdout=True)

    return retval

if __name__ == '__main__':
    main()
