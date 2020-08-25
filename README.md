# pocketing-generator
Generate pocketed geometry from Autodesk Inventor sketches

~~~
usage: pocketing.py [-h] [-segments SEGMENTS]
                    input_path thickness radius output_path

pocket a DXF

positional arguments:

  input_path          where to find the input DXF
  thickness           thickness of the struts, in the units of the input file
  radius              radius of the fillets, in the units of the input file
  output_path         where to put the output DXF

optional arguments:
  -h, --help          show this help message and exit
  -segments SEGMENTS  number of segments to use when approximating arcs
~~~