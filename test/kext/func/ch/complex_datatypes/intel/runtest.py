# runtest.py
# 
from kext_func_ch_complex_datatypes_test import KExtFuncCHCDTTest

class CustomTest(KExtFuncCHCDTTest):
    def config(self, myname, result):

        result[myname]['FC'] = 'ifort'
        result[myname]['FC_FLAGS'] = ''
        result[myname]['PRERUN'] = 'module purge; module try-load ncarenv/1.2; module try-load ncarcompilers/0.4.0; module try-load intel/17.0.1; module try-load netcdf/4.4.1.1; module try-load mpt/2.15f'

        self.set_status(result, myname, self.PASSED)

        return result

if __name__ == "__main__":
    print('Please do not run this script from command line. Instead, run this script through KGen Test Suite .')
    print('Usage: cd ${KGEN_HOME}/test; ./kgentest.py')
    sys.exit(-1)
