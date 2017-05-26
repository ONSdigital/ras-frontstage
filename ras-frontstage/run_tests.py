import unittest
import os
import sys

if __name__ == "__main__":
    test_dirs = os.listdir('./ras-frontstage/tests')
    suites_list = []
    loader = unittest.TestLoader()
    for directory in test_dirs:
        if directory == "app":
            test_path = "./ras-frontstage/tests/{}".format(directory)
            os.getcwd()
            print(test_path)
            suite = loader.discover(test_path)
            suites_list.append(suite)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            i = len(result.failures) + len(result.errors)
            if i != 0:
                sys.exit(1)
