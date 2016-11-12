import unittest
import platform
import os
import glob
import subprocess

import Swoop
import shapely
from Swoop.ext.ShapelySwoop import  ShapelySwoop
from GadgetMaker2 import OverlapCheck


def check_routing_percent (file_string):
    file_lines = file_string.split('\n')
    for line in file_lines:
        if line.upper().startswith("FINAL"):
            while not line[0].isdigit():
                line = line[1:]
            while not line[-1].isdigit():
                line = line[:-1]
            percent = float(line)
            
            if (len(line) >= 3) and (line[:4] == "100"):
                return 100.0
            else:
                return percent

def check_autoroute (input_name):

    # Input Pro file name
    input_pro = input_name + ".pro"

    if not os.path.exists(input_pro):
        raise IOError("Could not find file: "+ input_pro)
        return False

    file = open(input_pro)
    percent = check_routing_percent(file.read())

    if percent == 100.0:
        return True
    else:
        return False


def autoroute (input_name, output_name):

    # Remove all files that match output_name.* if they exits.
    try:
        for filename in glob.glob(output_name+".*"):
            os.remove(filename) 
    except OSError:
        pass

    # Remove input Pro File if they exits. 
    try:
        os.remove(input_name + ".pro") 
    except OSError:
        pass

    # Input schematic name
    input_sch = input_name + ".sch"
    # Input board name
    input_brd = input_name + ".brd"
    # Output board name
    output_brd = output_name + ".brd"

    # Eagle command Line arguments to auto-route
    if platform.system() == "Darwin":
        # Mac
        args = [
            os.environ["EAGLE_EXE"], 
            "-CAUTO;WRITE @" + output_brd + ";QUIT;", 
            input_brd, #maybe switch these last two???
            input_sch
        ]
    else:
        # Linux
        args = [
            os.environ["EAGLE_EXE"], 
            "-CAUTO;WRITE @" + output_brd + ";QUIT;", 
            input_brd,
            input_sch
        ]

    # Start auto-routing
    subprocess.call(args)

    return

def check_parts_overlap (input_name):

    # Input board name
    input_brd = input_name + ".brd"

    ## Open the board and check that the file exists and
    ## is of type (*brd)
    try:
        ## ShapelySwoop Open Board
        brd = ShapelySwoop.open(input_brd)

        ## Extract elements
        board = OverlapCheck.extract_board(brd)
        elements = brd.get_elements()

    except IOError:
        print "Filed to open {} : Not such file".format(input_brd)
        return False

    except AttributeError:
        print "Error reading {} : file extension is not Eagle Board (*.brd)".format(input_brd)
        return False

    overlap = OverlapCheck.check_element_set_reference(elements, board)

    if not overlap:
        return True
    else:
        return False


def check_autoplace (input_name, output_name):

    # Input board name
    input_brd = input_name + ".brd"

    # Output board name
    output_brd = output_name + ".brd"

    args = "quetzal " + " --inbrd " + input_brd + " --outbrd " + output_brd

    ret = 1
    try:
        ret = subprocess.check_output(args, shell=True)
    except subprocess.CalledProcessError as e:
        pass

    if (ret == 1):
        return False 
    else: 
        return True


class TestAutoPlacing(unittest.TestCase):

    def test_first_board(self):

        print "\n Running First Board Check ..."

        ## Board to Check
        input_name = "test_1"

        ## Auto-place output board
        placed_name = "placed_1"

        ## Routed output board
        routed_name = "routed_1"


        ## Check if Quetzal auto-placer works
        ret = check_autoplace(input_name, placed_name)
        self.assertTrue (ret , True)

        ## Check if parts overlap
        ret = check_parts_overlap (placed_name)
        self.assertTrue (ret , True)

        ## Check if routing completes
        autoroute(placed_name, routed_name)
        ret = check_autoroute(placed_name)
        self.assertTrue(ret, True)


    def test_second_board(self):

        print "\n Running Second Board Check ..."

        ## Board to Check
        input_name = "test_2"

        ## Auto-place output board
        placed_name = "placed_2"

        ## Routed output board
        routed_name = "routed_2"


        ## Check if Quetzal auto-placer works
        ret = check_autoplace(input_name, placed_name)
        self.assertTrue (ret , True)

        ## Check if parts overlap
        ret = check_parts_overlap (placed_name)
        self.assertTrue (ret , True)

        ## Check if routing completes
        autoroute(placed_name, routed_name)
        ret = check_autoroute(placed_name)
        self.assertTrue(ret, True)


    def test_third_board(self):

        print "\n Running Third Board Check ..."

        ## Board to Check
        input_name = "test_3"

        ## Auto-place output board
        placed_name = "placed_3"

        ## Routed output board
        routed_name = "routed_3"


        ## Check if Quetzal auto-placer works
        ret = check_autoplace(input_name, placed_name)
        self.assertTrue (ret , True)

        ## Check if parts overlap
        ret = check_parts_overlap (placed_name)
        self.assertTrue (ret , True)

        ## Check if routing completes
        autoroute(placed_name, routed_name)
        ret = check_autoroute(placed_name)
        self.assertTrue(ret, True)


if __name__ == '__main__':
    unittest.main()