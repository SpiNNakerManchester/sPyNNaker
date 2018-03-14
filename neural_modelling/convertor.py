import os
import math
import shutil
import sys


class Convertor(object):
    #__slots__ = [
    #    "_dest", "_dest_basename", "_src", "_src_basename"]

    def __init__(self, src, dest):
        self._src = os.path.abspath(src)
        if not os.path.exists(self._src):
            raise Exception("Unable to locate source directory {}".format(src))
        self._dest = os.path.abspath(dest)
        src_root, src_basename = os.path.split(
            os.path.normpath(self._src))
        dest_root, dest_basename = os.path.split(
            os.path.normpath(self._dest))
        if src_root != dest_root:
            # They must be siblings due to text manipulation in makefiles
            raise Exception("src and destination must be siblings")
        self._src_basename = "/" + src_basename + "/"
        self._dest_basename = "/" + dest_basename + "/"
        self._mkdir(self._dest)

    def run(self, copy_all):
        for dirName, subdirList, fileList in os.walk(self._src):
            self._mkdir(dirName)
            for fileName in fileList:
                _, extension = os.path.splitext(fileName)
                path = os.path.join(dirName, fileName)
                if fileName in ["Makefile"]:
                    self.convert_make(path)
                elif fileName in [".gitignore", "Makefile.common",
                                  "Makefile.neural_build", "Makefile.paths"]:
                    pass
                elif extension in [".mk"]:
                    self.convert_make(path)
                elif extension in [".c", ".cpp", ".h"]:
                    if copy_all:
                        self.convert_c(path)
                elif extension in [".elf", ".o", ".nm", ".txt"]:
                    if copy_all:
                        self.copy_if_newer(path)
                else:
                    print ("Unexpected file {}".format(path))
                    if copy_all:
                        self.copy_if_newer(path)

    def convert_make(self, src_path):
        destination = self._check_destination(src_path)
        if destination is None:
            return  # newer so no need to copy
        with open(src_path) as src_f:
            with open(destination, 'w') as dest_f:
                dest_f.write(
                    "# DO NOT EDIT! THIS FILE WAS GENERATED FROM {}\n\n"
                    .format(src_path))
                for line in src_f:
                    line_dest = line.replace(
                        self._src_basename, self._dest_basename)
                    dest_f.write(line_dest)

    def _start_log(self, line):
        self._log_type = None
        # checking stripped ignores comments and text elsewhere
        stripped = line.strip()
        if "log_info(" in stripped:
            self._log_type = "log_info("
        if "log_error(" in stripped:
            self._log_type = "log_error("
        if "log_debug(" in stripped:
            self._log_type = "log_debug("

        if self._log_type is None:
            return False
        else:
            self._log_start = line.index(self._log_type)
            # Empty full and lines as end_log called on first line too
            self._log_full = ""
            self._log_lines = 0
            return True

    def _end_log(self, line, dest_f):
        self._log_full += line.strip()
        self._log_lines += 1
        # may need a mopre complex test but lets start easy
        if ");" not in self._log_full:
            return True # Still inside a log
        else:
            dest_f.write(" " * self._log_start)
            dest_f.write(self._log_full)
            dest_f.write("\n" * (self._log_lines))
            return False # No longer in log

    def convert_c(self, src_path):
        destination = self._check_destination(src_path)
        if destination is None:
            return  # newer so no need to copy
        with open(src_path) as src_f:
            with open(destination, 'w') as dest_f:
                dest_f.write(
                    "// DO NOT EDIT! THIS FILE WAS GENERATED FROM {}\n\n"
                    .format(src_path))
                too_many_lines = 2
                in_log = False
                for line in src_f:
                    if too_many_lines:
                        # Try to recover the lines added by do not edit
                        check = line.strip()
                        if len(check) == 0 or check == "*":
                            too_many_lines -= 1
                            continue
                    if not in_log:
                        in_log = self._start_log(line)
                    if in_log:
                        in_log = self._end_log(line, dest_f)
                    else:
                        dest_f.write(line)

        self.copy_if_newer(src_path)

    def copy_if_newer(self, src_path):
        destination = self._check_destination(src_path)
        if destination is None:
            return  # newer so no need to copy
        shutil.copy2(src_path, destination)

    def _check_destination(self, path):
        destination = path.replace(self._src_basename, self._dest_basename)
        if not os.path.exists(destination):
            return destination
        # need to floor the time as some copies ignore the partial second
        src_time = math.floor(os.path.getmtime(path))
        dest_time = math.floor(os.path.getmtime(destination))
        if src_time > dest_time:
            return destination
        else:
            # print ("ignoring {}".format(destination))
            return None

    def _mkdir(self, path):
        destination = path.replace(self._src_basename, self._dest_basename)
        if not os.path.exists(destination):
            os.mkdir(destination, 0755)
        if not os.path.exists(destination):
            raise Exception("mkdir failed {}".format(destination))


def convert(src, modified, copy_all):
    convertor = Convertor(src, modified)
    convertor.run(copy_all)


if __name__ == '__main__':
    print (sys.argv)
    src = os.path.abspath(sys.argv[1])
    print ("src: {}".format(src))
    modified = os.path.abspath(sys.argv[2])
    print ("modified: {}".format(modified))
    if len(sys.argv) > 3:
        rule = sys.argv[3]
        if rule == "all":
            convert(src, modified, True)
            sys.exit(0)

    convert(src, modified, False)


        #print (subdirList)
    #print (fileList)