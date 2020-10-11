import copy
import os.path as path
import unittest
import shutil

import sltxpkg.config as sc
import sltxpkg.globals as sg

import sltxtest.util.dir as sud
import sltxtest.util.globals as sug


class TestCache(unittest.TestCase):

    def test_assure_dirs(self):
        # assign temporary directory
        tmp_base = sud.retrieve_tmpdir()
        sg.configuration[sg.C_TEX_HOME] = path.join(tmp_base, 'tex_home')
        sg.configuration[sg.C_WORKING_DIR] = path.join(tmp_base, 'working_dir')
        sg.configuration[sg.C_DOWNLOAD_DIR] = path.join(tmp_base, 'download_dir')
        sg.configuration[sg.C_CACHE_DIR] = path.join(tmp_base, 'cache')
        sg.configuration[sg.C_CREATE_DIRS] = True

        sc.assure_dirs()
        for config in [sg.C_TEX_HOME,sg.C_WORKING_DIR,sg.C_DOWNLOAD_DIR,sg.C_CACHE_DIR]:
            self.assertTrue(path.isdir(sg.configuration[config]), config + ' should exist.')

        shutil.rmtree(tmp_base)

    def tearDown(self):
        sug.restore_configuration()

if __name__ == '__main__':
    unittest.main()
