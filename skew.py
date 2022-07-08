# Fix XY skew on cantilever printers
#
# The cantilevered X axis can be slightly not perpendicular to the Y axis, 
# this causes a skew in the XY axis. 
# The solution is to offset the Y axis by a linear amount depending on 
# the hotend X location
#

# usage:
# $ python skew.py some_gcode_file.gcode
#
# creates new file some_gcode_file-fix-skew.gcode

#     alignment/measurement guide:
#                          _______
#              ______------      |      ^
#       -------                  |      |
#       |                        |      |
#       |                        |      |
#       |                        |      |
#       |                        |      | squareEdge e.g. 156mm
#       |                        |      |
#       |                        |      |
#   +Y  |                        |      |
#    ^  |                        |      |
#    |  |                  ______|      |
#    |  |      _______------     ^
#    |  -------                  | positive yDiff e.g. 1.3mm
#    |                                             
#    --------> +X
#
#       ______
#       |     ------______       
#       |                 -------|
#       |                        |
#       |                        |
#       |                        |
#       |                        |
#       |                        |
#       |                        |
#   +Y  |                        |
#    ^  |                        |
#    |  |_____                   | 
#    |        ------______       | ^
#    |                    -------| | negative yDiff e.g. -1.3mm
#    |                                             
#    --------> +X

# =========================================================================
# === CONFIG - change these ===============================================
# =========================================================================

# 'yDiff' - in millimetres, the measured y offset of the far X corner
yDiff = 1.3

# 'squareEdge' - in millimetres, the side length of the whole square
#                most likely the inside edge, depends how you measure
squareEdge = 156

# =========================================================================   
# === END CONFIG ==========================================================   
# =========================================================================      

import re
import os
import sys
import math

gcodeFile = sys.argv[1]
outFile = re.sub(r'.gcode', '-fix-skew.gcode', gcodeFile)

if os.path.isfile(outFile):
    os.remove(outFile)
outfile = open(outFile, 'a')

# amount to shift the Y axis by to make the X axis perpendicular
yCorrectPerMm = yDiff / squareEdge

# amount to multiply the X axis by to counter the shrinking from moving directly down
# this should be tiny and make practically no difference but is correct mathematically 
xCorrectPerMm = squareEdge / (math.sqrt( (squareEdge*squareEdge)-(yDiff*yDiff) ))

xIn = 0.0
yIn = 0.0
nModified = 0

with open(gcodeFile) as file:
    for line in file:
        # check that the current 'line' is a move, if so the line is processed
        isMovement = re.match(r'G[0-1]', line, re.I)
        if isMovement:
            # check there are X and Y coords        
            containsX = re.search(r'[xX]-?\d*\.*\d*', line, re.I)
            containsY = re.search(r'[yY]-?\d*\.*\d*', line, re.I)

            if containsX:
                xIn = float(re.sub(r'[xX]', '', containsX.group()))

            if containsY:
                yIn = float(re.sub(r'[yY]', '', containsY.group()))

            # calculate the Y offset required to realign the angled X axis and adjust yIn
            yOut = round(yIn - (xIn*yCorrectPerMm), 3)
            # multiply the X position by a constant factor to extend it to the real distance 
            xOut = round(xIn*xCorrectPerMm, 3)

            lineout = line
            
            if containsY and containsX:
                lineout = re.sub(r'[yY]-?\d*\.*\d*', 'Y' + str(yOut), lineout)
                lineout = re.sub(r'[xX]-?\d*\.*\d*', 'X' + str(xOut), lineout)
                nModified += 1

            outfile.write(lineout)
        else:
            outfile.write(line)
    print("Modified", nModified, "lines")
