#this is the cadquery branch!!!!!!!!
# you can't offset2D multiple items well, for some reason

#pockets = (smalleroutline - struts- - biggerholes) * unfillitedPockets
#result = outline - fillet|Z(pockets) - holes

import cadquery as cq
import ezdxf
from math import sqrt, atan2, degrees

THICKNESS = 1/16

def midpoint(p1, p2):
    return [ (p1[0] + p2[0])/2 , (p1[1] + p2[1])/2 ]

def distance(p1, p2):
    return sqrt( (p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 )

def angle(p1, p2):
    return degrees( atan2( p2[1] - p1[1], p2[0] - p1[0]) )


inputPath = 'tests/simplePlateIn.dxf'

dxf = ezdxf.readfile(inputPath)
mdl = dxf.modelspace()

#get hole definitions from circles
holeDefs = []
for c in mdl.query('CIRCLE'):
    holeDefs.append([c.get_dxf_attrib("radius"), c.get_dxf_attrib("center")[0], c.get_dxf_attrib("center")[1]])

#get strut definitions from construction lines and polylines
strutDefs = []
for l in mdl.query('LINE[linetype=="DASHED"]'): 
    strutDefs.append([l.get_dxf_attrib("start"),l.get_dxf_attrib("end")])
for p in mdl.query('POLYLINE[linetype=="DASHED"]'): 
    n = 0
    while n <= p.__len__()-2:
        strutDefs.append([p.__getitem__(n).dxf.location, p.__getitem__(n+1).dxf.location])
        n += 1

# get outer plate shape from non-construction polyline
outline = cq.Workplane("XY")

n = 0
for o in mdl.query('POLYLINE[!linetype=="DASHED"]'): 
     n = 0
     while n <= o.__len__()-1:
        bulge = o.__getitem__(n).dxf.bulge
        pos = o.__getitem__(n).dxf.location
        posNext = (o.__getitem__((n+1) %  o.__len__())).dxf.location

        if n == 0:
            outline = outline.moveTo(pos[0], pos[1])

        if o.__getitem__(n).dxf.bulge == 0:
            outline = outline.lineTo(posNext[0], posNext[1])

        else:
            #print(posNext[:2])
            outline = outline.radiusArc(posNext[:2], -ezdxf.math.bulge_to_arc(pos,posNext,bulge)[3] )

        outline = outline.moveTo(posNext[0], posNext[1])
        n += 1

outline = outline.close()

outlineInside = outline.offset2D(-THICKNESS).extrude(0.1)

outline2 = cq.Workplane("XY")

n = 0
for o in mdl.query('POLYLINE[!linetype=="DASHED"]'): 
     n = 0
     while n <= o.__len__()-1:
        bulge = o.__getitem__(n).dxf.bulge
        pos = o.__getitem__(n).dxf.location
        posNext = (o.__getitem__((n+1) %  o.__len__())).dxf.location

        if n == 0:
            outline2 = outline2.moveTo(pos[0], pos[1])

        if o.__getitem__(n).dxf.bulge == 0:
            outline2 = outline2.lineTo(posNext[0], posNext[1])

        else:
            #print(posNext[:2])
            outline2 = outline2.radiusArc(posNext[:2], -ezdxf.math.bulge_to_arc(pos,posNext,bulge)[3] )

        outline2 = outline2.moveTo(posNext[0], posNext[1])
        n += 1

outline2 = outline2.close()
outlineOutside= outline2.extrude(0.1)





holeOutlines = cq.Workplane("XY")
for h in holeDefs:
    holeOutlines = holeOutlines.moveTo(h[1],h[2]).circle(h[0] + THICKNESS).extrude(0.1)

holes = cq.Workplane("XY")
for h in holeDefs:
    holes = holes.moveTo(h[1],h[2]).circle(h[0]).extrude(0.1)

struts = cq.Workplane("XY")
for s in strutDefs:
    p1 = s[0][:2]
    p2 = s[1][:2]
    struts = struts.moveTo(*midpoint(p1,p2)).slot2D(distance(p1,p2), THICKNESS, angle(p1,p2)).extrude(0.1)

# insideShape = obj.wires().toPending().offset2D(-0.05).extrude(1)
# outsideShape = obj.wires().toPending().extrude(1)

# insideShape = obj2.wires().toPending().offset2D(-0.05).extrude(1)
# outsideShape = obj2.wires().toPending().extrude(1)

#m2 = outsideShape2.cut(insideShape2)

result = outlineOutside.cut(outlineInside.cut(holeOutlines.union(struts)).edges("|Z").fillet(1/16).intersect(outlineInside.cut(holeOutlines.union(struts)))).cut(holes)

cq.exporters.export(result,'result.step')
