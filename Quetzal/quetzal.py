import argparse
import collections
import logging as log
import os
import subprocess
import sys
import time
import math

import Swoop
import shapely
from Swoop.ext.ShapelySwoop import  Element as ShapelyElement
from Swoop.ext.ShapelySwoop import ShapelyEagleFilePart as SEFP
from Swoop.ext.ShapelySwoop import  ShapelySwoop
from Swoop.ext.ShapelySwoop import polygon_as_svg
from shapely.geometry import *

from descartes import PolygonPatch

############################
## Global Variables       ##
############################

smoothness=0

# Plot Colors
RED = "#ff0000"
GREEN = "#00ff00"
BLACK = "#000000"
WHITE = "#ffffff"
GRAY = "#888888"
BLUE = "#0000ff"
YELLOW = "#ff00ff"
PURPLE = "#ff00ff"

# Board layers for plotting
ALL_LAYERS = ["Dimension", "Holes", "Top", "Bottom", "onBoard", "offBoard", "tKeepout", "bKeepout"]
ALL_COMPONENTS = ["Dimension", "Holes", "onBoard", "offBoard", "tKeepout", "bKeepout"]

############################
## Functions              ##
############################


def extract_board(brd):

    return brd.get_geometry(layer_query="Dimension", polygonize_wires=SEFP.POLYGONIZE_STRICT, apply_width=False)


def extract_components(element):

    holes = element.get_geometry(layer_query="Holes", width_smoothness=smoothness).buffer(1, resolution=smoothness)  # unplated holes
    on_board = element.get_geometry(layer_query="onBoard", polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT, width_smoothness=smoothness)
    #off_board = element.get_geometry(layer_query="offBoard", polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT, width_smoothness=smoothness)
    tKeepout = element.get_geometry(layer_query="tKeepout",
                                fill_circles=True,
                                polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT,
                                width_smoothness=smoothness)
    bKeepout = element.get_geometry(layer_query="bKeepout",
                                fill_circles=True,
                                polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT,
                                width_smoothness=smoothness)
    return shapely.ops.unary_union([holes, on_board, tKeepout, bKeepout])


# Prints locked and unlocked elements dictionaries together with the board dimension
# (e.g  print_board_elements(board, locked_elements, unlocked_elements))
def print_board_elements (brd, elementone, elementtwo):
    from matplotlib import pyplot as plt

    # Extract Polygons
    brdDimension = extract_board(brd)

    # Create plot
    fig = plt.figure(2, figsize=(10,10), dpi=90)
    subfig = fig.add_subplot(111)

    # Add Multi-polygons of the element to plot

    # Add board polygons
    patch = PolygonPatch(brdDimension, facecolor=GREEN, edgecolor=BLACK, alpha=0.5, zorder=2)
    subfig.add_patch(patch)

    # Add element one polygons
    for e, polygon in elementone.iteritems():
        if (polygon.geom_type == 'Polygon'):
            patch = PolygonPatch(polygon, facecolor=BLUE, edgecolor=BLACK, alpha=0.5, zorder=2)
            subfig.add_patch(patch)
        elif (polygon.geom_type == 'MultiPolygon'):
            for single in polygon:
                patch = PolygonPatch(single, facecolor=BLUE, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)

    # Add element two polygons
    for e, polygon in elementtwo.iteritems():
        if (polygon.geom_type == 'Polygon'):
            patch = PolygonPatch(polygon, facecolor=RED, edgecolor=BLACK, alpha=0.5, zorder=2)
            subfig.add_patch(patch)
        elif (polygon.geom_type == 'MultiPolygon'):
            for single in polygon:
                patch = PolygonPatch(single, facecolor=RED, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)

    # Get board width and height
    bounds = brdDimension.bounds
    width  = abs(bounds[2] - bounds[0])
    height = abs(bounds[3] - bounds[1])

    # Plot Board

    subfig.set_title('PCB')
    xrange = [bounds[0] - 0.1*width,  bounds[2] + 0.1*width]
    yrange = [bounds[1] - 0.1*height, bounds[3] + 0.1*height]
    subfig.set_xlim(*xrange)
    subfig.set_ylim(*yrange)
    subfig.set_aspect(1)

    subfig.xaxis.set_ticks(range(int(math.floor(float(bounds[0]))), int(math.ceil(float(bounds[2])))))
    subfig.yaxis.set_ticks(range(int(math.floor(float(bounds[1]))), int(math.ceil(float(bounds[3])))))
    subfig.grid(True)    

    plt.show()

    return

# Prints given board layers in an array 
# (e.g  print_board_layers (brd, ["Dimensions", "tKeepout"])) 
def print_board_layers (brd, layers):
    from matplotlib import pyplot as plt

    # Extract Polygons
    brdDimension = extract_board(brd)

    # Create plot
    fig = plt.figure(2, figsize=(10,10), dpi=90)
    subfig = fig.add_subplot(111)

    # Add Multi-polygons to plot

    for layer in layers:
        if layer == "Dimension":
            polygon = brd.get_geometry(layer_query="Dimension", polygonize_wires=SEFP.POLYGONIZE_STRICT, apply_width=False)
            patch = PolygonPatch(polygon, facecolor=GREEN, edgecolor=BLACK, alpha=0.5, zorder=2)
            subfig.add_patch(patch)
        elif layer == "Holes":
            polygons = brd.get_geometry(layer_query="Holes", width_smoothness=smoothness).buffer(1, resolution=smoothness)  # unplated holes
            for polygon in polygons:
                patch = PolygonPatch(polygon, facecolor=RED, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)
        elif layer == "Top":
            polygons = brd.get_geometry(layer_query="Top", width_smoothness=smoothness).buffer(0.5, resolution=smoothness)
            for polygon in polygons:
                patch = PolygonPatch(polygon, facecolor=RED, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)
        elif layer == "Bottom":
            polygons = brd.get_geometry(layer_query="Bottom", width_smoothness=smoothness).buffer(0.5, resolution=smoothness)
            for polygon in polygons:
                patch = PolygonPatch(polygon, facecolor=BLUE, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)
        elif layer == "onBoard":
            polygons = brd.get_geometry(layer_query="onBoard", polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT, width_smoothness=smoothness)
            for polygon in polygons:
                patch = PolygonPatch(polygon, facecolor=PURPLE, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)
        elif layer == "offBoard":
            polygons = brd.get_geometry(layer_query="offBoard", polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT, width_smoothness=smoothness)
            for polygon in polygons:
                patch = PolygonPatch(polygon, facecolor=PURPLE, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)
        elif layer == "tKeepout":
            polygons = brd.get_geometry(layer_query="tKeepout",
                fill_circles=True,
                polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT,
                width_smoothness=smoothness)
            for polygon in polygons:
                patch = PolygonPatch(polygon, facecolor=RED, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)
        elif layer == "bKeepout":
            polygons = brd.get_geometry(layer_query="bKeepout",
                fill_circles=True,
                polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT,
                width_smoothness=smoothness)
            for polygon in polygons:
                patch = PolygonPatch(polygon, facecolor=BLUE, edgecolor=BLACK, alpha=0.5, zorder=2)
                subfig.add_patch(patch)
        else:
            continue

    # Plot Board
    
    bounds = brdDimension.bounds
    width  = abs(bounds[2] - bounds[0])
    height = abs(bounds[3] - bounds[1])

    subfig.set_title('PCB')
    xrange = [bounds[0] - 0.1*width,  bounds[2] + 0.1*width]
    yrange = [bounds[1] - 0.1*height, bounds[3] + 0.1*height]
    subfig.set_xlim(*xrange)
    subfig.set_ylim(*yrange)
    subfig.set_aspect(1)

    subfig.xaxis.set_ticks(range(int(math.floor(float(bounds[0]))), int(math.ceil(float(bounds[2])))))
    subfig.yaxis.set_ticks(range(int(math.floor(float(bounds[1]))), int(math.ceil(float(bounds[3])))))
    subfig.grid(True)    

    plt.show()

    return 


# This function should be called before starting to move components.
# It checks if the unlocked elements doesn't have any overlapping 
# with locked elements or off-Board errors. Then this function passes
# any unlocked elements without errors to the locked elements dictionary 
def unlocked_to_locked (board, locked_elements, unlocked_elements):

    # Returning variable (1 if board has overlapping problems: 0 if Not)
    ret = 0

    # Copy dictionaries
    cpy_unlocked_elements = unlocked_elements.copy()
    cpy_locked_elements = locked_elements.copy()

    # Make an off-Board Polygon with the difference between a big polygon and the board size
    universe = Polygon([(-1000,-1000),(1000,-1000),(1000,1000),(-1000,1000)])
    un_board = universe.difference(board);

    # Check if each locked_element overlaps with a unlocked_element
    for unlock_element, unlock_polygon in cpy_unlocked_elements.iteritems():

        # print "Checking unlocked component: " + unlock_element.get_name()
        e1 = { unlock_element : unlock_polygon } 
        error = 0

        ## Check if a part of the component is off-Board 
        offb = e1[unlock_element].intersection(un_board)
        if offb:
            # print ("A portion of Part {} is off the board".format(unlock_element.get_name()))
            error = 1

        ## Check that the component is on the Board.  
        for lock_element, lock_polygon in cpy_locked_elements.iteritems():
            e2 = { lock_element : lock_polygon }

            ## Check that the component doesn't overlap for top and bottom. 
            overlap = e1[unlock_element].intersection(e2[lock_element])
            if overlap:
                # print ("Part {} overlaps Part {}".format
                #     (unlock_element.get_name(),
                #      lock_element.get_name()))
                error = 1

        if (not error):
            # Move unlocked_element to locked_element dictionary
            # if unlocked_element doesn't overlap
            locked_elements.update(e1)
            unlocked_elements.pop(unlock_element, None)
        else:
            ret = 1

    return ret


# Check if any element in the dictionary of unlocked_elements overlaps
# with any element of the dictionary with locked_elements 
def check_unlocked_components (board, locked_elements, unlocked_elements):

    # Copy dictionaries
    cpy_unlocked_elements = unlocked_elements.copy()
    cpy_locked_elements = locked_elements.copy()

    # Make an off-Board Polygon with the difference between a big polygon and the board size
    universe = Polygon([(-1000,-1000),(1000,-1000),(1000,1000),(-1000,1000)])
    un_board = universe.difference(board);

    # Check if each locked_element overlaps with a unlocked_element
    for unlock_element, unlock_polygon in cpy_unlocked_elements.iteritems():

        e1 = { unlock_element : unlock_polygon } 

        ## Check if a part of the component is off-Board 
        offb = e1[unlock_element].intersection(un_board)
        if offb:
            # print ("A portion of Part {} is off the board".format(unlock_element.get_name()))
            return unlock_element

        ## Check that the component is on the Board.  
        for lock_element, lock_polygon in cpy_locked_elements.iteritems():
            e2 = { lock_element : lock_polygon }

            ## Check that the component doesn't overlap for top and bottom. 
            overlap = e1[unlock_element].intersection(e2[lock_element])
            if overlap:
                # print ("Part {} overlaps Part {}".format
                #     (unlock_element.get_name(),
                #      lock_element.get_name()))
                return unlock_element

        # Move unlocked_element to locked_element dictionary
        # if unlocked_element doesn't overlap
        locked_elements.update(e1)
        unlocked_elements.pop(unlock_element, None)

    return None



def main():

    parser = argparse.ArgumentParser(description="This tool automatically places unlocked elements \
                                    (unplaced components) of a Eagle .brd file inside the board.")
    parser.add_argument("-i","--inbrd",
                        help="The .brd file with unlocked elements to be placed.",
                        metavar="<unplaced_board>.brd",
                        required=True)
    parser.add_argument("-o","--outbrd",help="Name of output .brd file",metavar="<output>.brd")
    args = parser.parse_args()

    
    try:
        ## ShapelySwoop Open Board
        brd = ShapelySwoop.open(args.inbrd)

        ## Extract elements
        board = extract_board(brd)
        elements = brd.get_elements()
        pass

    except IOError:
        print "Filed to open {} : Not such file".format(args.inbrd)
        sys.exit(0)
        pass

    except AttributeError:
        print "Error reading {} : file extension is not Eagle Board (*.brd)".format(args.inbrd)
        sys.exit(0)
        pass
    

    ## Get locked and unlocked elements in a dictionary
    locked_elements = {}
    unlocked_elements = {}
    for e in elements:
        if (e.get_locked() == 1):
            #  Locked element
            locked_elements.update({e: extract_components(e)})
        else:
            # Unlocked element
            unlocked_elements.update({e: extract_components(e)})

    # TODO: Add this with display option
    # print_board_elements(brd, locked_elements, unlocked_elements)


    # Checks if any unlocked component can be passed to the locked dictionary. 
    ret = unlocked_to_locked(board, locked_elements, unlocked_elements)
    if (ret == 0):
        print ("No parts overlap or are off-Board")
        sys.exit(0)

    ## Get board dimensions
    board_min_x = board.bounds[0]
    board_min_y = board.bounds[1]
    board_max_x = board.bounds[2]
    board_max_y = board.bounds[3]

    ## Move component
    element_x = 0
    element_y = 0
    BOARD_CLEARANCE = 1.5
    move_dictionary = {} # Type {element.get_name(): [moves_x, moves_y, width, height]}
    board_pass = 0
    while (board_pass == 0):

        ## Check if element overlaps or is off Board
        element = check_unlocked_components(board, locked_elements, unlocked_elements)

        if (element == None):
            print ("Finish moving overlapped or off-Board elements")
            board_pass = 1
        else:

            ## Check if unlocked element is already in move_dictionary
            if element.get_name() in move_dictionary:

                e = move_dictionary[element.get_name()]
                moves_x = e[0]  # Get number of moves in x direction
                moves_y = e[1]  # Get number of moves in y direction
                width   = e[2]  # Get element width 
                height  = e[3]  # Get element height
                moves_x = moves_x + 1 # Move the element once in x 
                element_x = board_min_x + (width/2 * moves_x) + BOARD_CLEARANCE

                ## If moving in x causes element to be off-Board then
                ## reset moves_x counter to 1 and increment moves_y counter. 
                if ( (element_x + width/2) > (board_max_x - BOARD_CLEARANCE)):
                    moves_x = 1
                    moves_y = moves_y + 1
                    element_x = board_min_x + (width/2 * moves_x) + BOARD_CLEARANCE

                element_y = board_min_y + (height/2 * moves_y) + BOARD_CLEARANCE

                ## If moving in y causes element to be off-Board then
                ## we have reach all possible moves through the board. 
                if ( (element_y + height/2)  > (board_max_y - BOARD_CLEARANCE)):
                    print ("Error unlocked part couldn't be placed on board")
                    board_pass = -1

                ## Save updated moves in the dictionary 
                move_dictionary.update({element.get_name(): [moves_x, moves_y, width, height]})

            else:

                ## Get width and height of element 
                ## (Its saves time to store the size in the dictionary)
                element_bounds = element.get_geometry().bounds
                width = element_bounds[2] - element_bounds[0]
                height = element_bounds[3] - element_bounds[1]

                ## If element not in dictionary save it with initial x & y move values of 1
                moves_x = 1
                moves_y = 1
                move_dictionary.update({element.get_name(): [moves_x, moves_y, width, height]})

                ## Set element starting x and y positions
                element_x = board_min_x + (width/2 * moves_x) + BOARD_CLEARANCE
                element_y = board_min_y + (height/2 * moves_y) + BOARD_CLEARANCE

                ## Check if the unlocked element is smaller than the board
                if ((element_x + width/2) > (board_max_x - BOARD_CLEARANCE) or 
                    (element_y + height/2) > (board_max_y - BOARD_CLEARANCE)):
                    print ("Element to move is bigger than the board")
                    board_pass = -1

            ## Update unlocked element with new x and y values
            element.set_x(element_x) 
            element.set_y(element_y)

            #START = time.time()
            unlocked_elements[element] = extract_components(element)
            #END = time.time()
            #print "Exec Time 3 = {}".format(END - START)

    # TODO: Add this with display option
    # print_board_elements(brd, locked_elements, unlocked_elements)
    # print_board_layers(brd, ALL_LAYERS)

    # Write Output board file
    if (args.outbrd):
        brd.write(args.outbrd)


    # Exit
    sys.exit(0)


if __name__ == "__main__":
    main()