import shutil
import tempfile
import glob
import os.path
import re

ANALYZER_PATTERN = re.compile(
    '^! |Error:|Undefined control sequence|improper alph|Incomplete \\\\if|Runaway preamble\\?|has an extra|Permission denied|not loadable: Metric|Extra alignment tab has been|Can\'t create output|too long|Runaway argument|al parameter number')


class Analyzer():
    def __init__(self, file: str, idx: int):
        super().__init__()
        self.file = file
        self.idx = idx

    def analyze(self):
        print("\033[34m"+self.file.replace(os.getcwd(), '\033[38;5;247m[cwd]\033[34m') +"\033[m")
        target = tempfile.TemporaryDirectory(prefix='sltx-ua-log').name
        shutil.unpack_archive(self.file, extract_dir=target)
        # TODO: make this more sensitive (makeindex logs etc...)
        templogs = glob.glob(os.path.join(target, '*.log'))
        templogs += glob.glob(os.path.join(target, '*.ilg'))
        for templog in templogs:
            print("\033[34m  - "+templog+"\033[m")
            with open(templog) as tl:
                offsetpr = 0
                for line in tl.readlines():
                    if re.search(ANALYZER_PATTERN, line):
                        offsetpr = 6
                        print('\033[38;5;64m', end='')
                    if offsetpr > 0:
                        print('    >', line, end='\033[m')
                        offsetpr -= 1
                        if offsetpr == 0:
                            print("\033[38;5;247m    # -------------------------------------\033[m")
