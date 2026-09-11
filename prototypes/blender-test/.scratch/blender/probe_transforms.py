import bpy
from mathutils import Vector
for name in ['NH_Body','NH_Ragged_Robe','NH_Upper_Mantle','NH_Pauldron','NH_Hand_Front']:
    o=bpy.data.objects[name]
    print('\n',name,'parent',o.parent.name if o.parent else None)
    print('loc',tuple(round(v,3) for v in o.location),'scale',tuple(round(v,3) for v in o.scale))
    print('matrix_world')
    for row in o.matrix_world:
        print(tuple(round(v,3) for v in row))
    if o.type=='MESH':
        pts=[o.matrix_world@Vector(c) for c in o.bound_box]
        print('bounds',tuple(round(v,3) for v in (min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts),min(p.z for p in pts),max(p.z for p in pts))))
