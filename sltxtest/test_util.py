import copy
import unittest

import sltxpkg.globals as sg

import sltxtest.util.globals as sug


class TestConfig(unittest.TestCase):

    def test_configuration_restore(self):
        before_config = copy.deepcopy(sg.configuration)
        sg.configuration[sg.C_CACHE_DIR] = "1234/Walter"
        self.assertNotEqual(before_config, sg.configuration,
                            'Changed the cache dir')
        sug.restore_configuration()
        self.assertEqual(before_config, sg.configuration,
                         'Restored configuration')


if __name__ == '__main__':
    unittest.main()
