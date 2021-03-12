import shutil
import tempfile
import glob
import os.path
import re

ANALYZER_PATTERN = re.compile(
    '^! |Error:|Undefined control sequence|improper alph|Incomplete \\\\if|Runaway preamble\\?|has an extra|Permission denied|not loadable: Metric|Extra alignment tab has been|Can\'t create output|too long|Runaway argument|al parameter number|Misplaced (alignment)?|doesn\'t match|Invalid UTF-8|forgotten \\\\end|ERROR|Missing')
ARCHIVE_PATTERN = re.compile('.*(\.tar(\.gz)?$|\.zip|\.7z)')

ANALYZE_DIVIDER = "\033[38;5;247m    # -------------------------------------\033[m"


class Analyzer():
    def __init__(self, file: str, idx: int):
        super().__init__()
        self.file = file
        self.idx = idx

    def __unpack_or_cp(self) -> str:
        if(re.match(ARCHIVE_PATTERN, self.file)):
            print("\033[38;5;31m" + self.file.replace(os.getcwd(),
                                                      '\033[38;5;247m[cwd]\033[38;5;31m') + "\033[m")
            target = tempfile.TemporaryDirectory(prefix='sltx-ua-log').name
            shutil.unpack_archive(self.file, extract_dir=target)
            return target
        else:
            print("Analyze Logfile...")
            return ""

    def __analyze_file(self, analyze_f: str):
        print("\033[38;5;31m  - "+analyze_f+"\033[m", end=' ')
        self.fine = True
        with open(analyze_f) as tl:
            self.offset_ptr = 0
            for line in tl.readlines():
                self.__analyze_line(line)
        if self.fine:
            print('\033[32m(fine)\033[m')

    def __analyze_line(self, line):
        if re.search(ANALYZER_PATTERN, line):
            self.offset_ptr = 6
            if self.fine:
                print()
                self.fine = False
            print('\033[38;5;64m', end='')
        if self.offset_ptr > 0:
            self.__print_error_line(line)

    def __print_error_line(self, line):
        print('    >', line, end='\033[m')
        self.offset_ptr -= 1
        if not self.offset_ptr:
            print(ANALYZE_DIVIDER)

    def __analyze_folder(self, target: str):
        templogs = []
        for ext in ('*.log', '*.ilg', '*.glg', '*.alg', '*.blg', '*.sltx-log'):
            templogs.extend(glob.glob(os.path.join(target, ext)))
        for templog in templogs:
            self.__analyze_file(templog)

    # TODO: make this more sensitive (makeindex logs etc...)
    def analyze(self):
        target: str = self.__unpack_or_cp()
        if target:
            self.__analyze_folder(target)
        else:
            self.__analyze_file(self.file)
        print()
