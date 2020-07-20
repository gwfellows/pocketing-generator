import ezdxf
from solid import *
from solid.utils import *
import os
import sys
import math

#$fn
SEGMENTS = 48 

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

def arcPoly(center, a1, a2, r):
    points = []
    t = 0
    while t <+ 1:
        a = a2-a1
        # switch to positive angle
        if a <= 0:
            a += math.pi*2
        points.append([center[0] + r*math.cos(a1 + a*t), center[1] + r*math.sin(a1 + a*t)])
        t += 1/SEGMENTS
    return points

#get outer plate shape from non-construction polyline
outerPoly = []
outer = mdl.query('POLYLINE[!linetype=="DASHED"]')
n = 0
for o in outer: 
     n = 0
     while n <= o.__len__()-1:
        bulge = o.__getitem__(n).dxf.bulge
        pos = o.__getitem__(n).dxf.location
        if o.__getitem__(n).dxf.bulge == 0:
            outerPoly.append([pos[0], pos[1]])
        else:
            posNext = (o.__getitem__((n+1) %  o.__len__())).dxf.location
            for p in arcPoly(*ezdxf.math.bulge_to_arc(pos,posNext,bulge)):
                outerPoly.append(p)
        n += 1

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
os.system('cmd /c ""C:\Program Files\OpenSCAD\openscad.com" -o "' + outputPath + '" pocketing.scad"')
