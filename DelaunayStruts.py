from scipy.spatial import Delaunay
import sys
import ezdxf
from ezdxf.math import OCS

# python DelaunayStruts.py <input_file>
inputPath = sys.argv[1]

dxf = ezdxf.readfile(inputPath)
mdl = dxf.modelspace()

points = []

circles = mdl.query('CIRCLE')
for c in circles:
    points.append(c.get_dxf_attrib("center")[:-1])

tri = Delaunay(points)
ocs = OCS((0, 1, 1))

struts = []
for i in tri.simplices.copy():
    struts.append([points[i[0]], points[i[1]]])
    struts.append([points[i[1]], points[i[2]]])
    struts.append([points[i[2]], points[i[0]]])

for c in struts:
    mdl.add_line(start = c[0], end = c[1], dxfattribs={'linetype':'DASHED', 'extrusion':ocs.uz})

dxf.save()
