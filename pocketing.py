import ezdxf
from solid import *
from solid.utils import *
import os
import sys

# python pocket .py <input_file> <thickness> <radius> <output_file>
inputPath = sys.argv[1]
thickness = float(sys.argv[2])
radius = float(sys.argv[3])
outputPath = sys.argv[4]

dxf = ezdxf.readfile(inputPath)

mdl = dxf.modelspace()

#get hole definitions from circles
holeDefs = []
circles = mdl.query('CIRCLE')
for c in circles:
    holeDefs.append([c.get_dxf_attrib("radius"), c.get_dxf_attrib("center")[0], c.get_dxf_attrib("center")[1]])

#get strut definitions from construction lines and polylines
strutDefs = []
lines = mdl.query('LINE[linetype=="DASHED"]')
for l in lines: 
    strutDefs.append([l.get_dxf_attrib("start"),l.get_dxf_attrib("end")])
polylines = mdl.query('POLYLINE[linetype=="DASHED"]')
for p in polylines: 
    n = 0
    while n <= p.__len__()-2:
        strutDefs.append([p.__getitem__(n).dxf.location, p.__getitem__(n+1).dxf.location])
        n += 1

#get outer plate shape from non-circle non-construction shape
outerPoly = []
outer = mdl.query('POLYLINE[!linetype=="DASHED"]')
n = 0
for o in outer: 
     n = 0
     while n <= o.__len__()-1:
        outerPoly.append(o.__getitem__(n).dxf.location)
        print(o.__getitem__(n).dxf.bulge)
        n += 1


#$fn
SEGMENTS = 48 

#generate pocketed geometry
#thickness = min thickness of any part
#radius = fillet radius
def pocketedPlate(thickness, radius):

    def fillet(shape,r):
        return offset(-r)(
            offset(r)(
                shape()
            )
        )

    def addHoles(offset): 
        holes = []
        for c in holeDefs:
            holes.append(translate([c[1],c[2]])(
                circle(c[0]+offset)
                )
            )
        return union()(holes)

    def addStruts():
        struts = []
        for s in strutDefs:
            struts.append(hull()(
                translate([s[0][0],s[0][1]])(
                    circle(d=thickness)
                ),
                translate([s[1][0],s[1][1]])(
                    circle(d=thickness)
                )
                )
            )
        return union()(struts)

    
    a = fillet(((polygon(outerPoly) - offset(delta = -thickness)(polygon(outerPoly)) + addStruts() + addHoles(thickness)) * polygon(outerPoly)), radius) - addHoles(0)

    return a


a = pocketedPlate(thickness, radius)

scad_render_to_file(a, file_header=f'$fn = {SEGMENTS};', include_orig_code=True)

os.system('cmd /c "openscad.exe -o "' + outputPath + '" pocketing.scad"')


# TODO:
# - add support for arcs in outer poly
# - switch to freecad scripting? (for true arcs)