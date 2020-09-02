#this is the cadquery branch!!!!!!!!
# you can't offset2D circles, for some reason

# how to  fillet inside: offset(-r)( offset(r)(shape) )
# fillet_inside(shelled_outline + bigger_circles + struts) * outline - holes


import cadquery as cq
import ezdxf

inputPath = 'tests/simplePlateIn.dxf'

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

#obj2 = cq.importers.importDXF("tests/testtttt.dxf")
obj = cq.importers.importDXF("tests/circles.dxf")

insideShape = obj.wires().toPending().offset2D(-0.05).extrude(1)
outsideShape = obj.wires().toPending().extrude(1)

# insideShape = obj2.wires().toPending().offset2D(-0.05).extrude(1)
# outsideShape = obj2.wires().toPending().extrude(1)

#m2 = outsideShape2.cut(insideShape2)

result = outsideShape.cut(insideShape)

cq.exporters.export(result,'result.step')
