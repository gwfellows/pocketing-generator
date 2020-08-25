import ezdxf
from solid import *
from solid.utils import *
import os, sys, math, argparse

my_parser = argparse.ArgumentParser(description='pocket a DXF')

my_parser.add_argument('input_path', help='where to find the input DXF')
my_parser.add_argument('thickness', help='thickness of the struts, in the units of the input file \n fractions are allowed')
my_parser.add_argument('radius', help='radius of the fillets, in the units of the input file \n fractions are allowed')
my_parser.add_argument('output_path', help='where to put the output DXF')
my_parser.add_argument('-segments', help='number of segments to use when approximating arcs', required=False, default=48)

args = my_parser.parse_args()

inputPath = args.input_path
thickness = eval(str(args.thickness))
radius = eval(str(args.radius))
outputPath = args.output_path
SEGMENTS = args.segments

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
    a = a2-a1
    # switch to positive angle
    if a <= 0:
        a += math.pi*2
    while t <= 1 + 1e-9: # deal with floating point precision errors
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
            arc = arcPoly(*ezdxf.math.bulge_to_arc(pos,posNext,bulge))
            if ezdxf.math.is_close_points(arc[-1], posNext[:-1], abs_tol=1e-9):
                for p in arc:
                    outerPoly.append(p)
            else:
                arc.reverse()
                for p in arc:
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

    a = fillet((polygon(outerPoly) - offset(delta = -thickness)(polygon(outerPoly)) + addStruts() + addHoles(thickness)), radius) * polygon(outerPoly)
    return a

a = pocketedPlate(thickness, radius)
scad_render_to_file(a, file_header=f'$fn = {SEGMENTS};', include_orig_code=False)
os.system('cmd /c openscad -o ' + outputPath + ' pocketing.scad')

#then add circles
outFile = ezdxf.readfile(outputPath)
outMsp = outFile.modelspace()

for c in holeDefs:
    outMsp.add_circle(center=[c[1],c[2]], radius=c[0])

outFile.save()
