import shutil
import tempfile
import glob
import os.path


class Analyzer():
    def __init__(self, file: str, idx: int):
        super().__init__()
        self.file = file
        self.idx = idx

    def analyze(self):
        print("\033[34m"+self.file+"\033[m")
        target = tempfile.TemporaryDirectory(prefix='sltx-ua-log').name
        shutil.unpack_archive(self.file, extract_dir=target)
        # TODO: make this more sensitive (makeindex logs etc...)
        templogs = glob.glob(os.path.join(target, '*.log'))
        for templog in templogs:
            print("\033[34m  - "+templog+"\033[m")
            with open(templog) as tl:
                offsetpr = 0
                for line in tl.readlines():
                    if line.startswith('!') or 'LaTeX error' in line:
                        offsetpr = 4
                    if offsetpr > 0:
                        print(line,end='')
                        offsetpr -= 1
                        if offsetpr == 0:
                            print("-------")
