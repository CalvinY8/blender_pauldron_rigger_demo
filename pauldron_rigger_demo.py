bl_info = {
    "name": "Pauldron Rigger",
    "author": "CalvinY8",
    "version": (1,0),
    "blender": (2,93,1),
    "location" : "View3d > Tool",
    "warning" : "",
    "wiki_url" : "",
    "category": "rigging",
    }


import bpy
from bpy.props import PointerProperty
from mathutils import Vector, Matrix
from math import degrees, radians

#            toggle comment/uncomment lines using ctrl /

#https://blender.stackexchange.com/questions/6173/where-does-console-output-go
def print(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")


class rigit(bpy.types.Operator):
    bl_idname = "rigit.func_1"
    #must have valid Python syntax for a name, including a single dot; the part to the left of the dot must be the name of one of the valid categories of operators,
    bl_label = "rig it!"
    bl_options = {"UNDO"} #enable undo/redo
    
    #class members which once assigned will be used by various methods of the class
    side = "anything"
    armature = ""
    armature_pose = "" #the armature pose data
    pauldron = "anything"
    
    shoulder_bone_name = "" #name of upperarm bone
    
    upperarm_bone_x_angle = "" #angle of upperarm bone in DEGREES relative to global +X axis.
   #                            all 3 pauldron rigging bones are generated relative to this angle.
    
    #contains vectors shoulderbone.head and forearm.head, representing true distance from shoulder to elbow.
    upperarm_vectors = [[0,0,0],[0,0,0]]
    #upperarm.head is assigned to the first indice
    #forearm.head is assigned to the 2nd indice
    
    
    forearm_bone_name = ""
    clavicle_bone_name = ""
    xz_rotator_bone_name = "" #name of the bone that pauldron is parented to.
    
    def execute(self, context):
        #self.report({'INFO'}, f"calling function {self.bl_idname}")
        
        print("-----------------------------") #differentiate prev/new printouts
        if self.hasComponents(context) and self.hasArmature(context):
            print('components found...armature found')
            self.clean_all(context=context)
            
            self.side = "L"
            #print("rigging " + s + " side")
            
            if self.checkBones(context) and self.checkShoulderAngle(context):
                #following two lines temporarily disabled in order to test reading of upperarm bone angle.
                self.assignPauldron(context)
                self.makeBones(context)
                
                #--------------------------------------------------------
        else:
            print("missing components")

        return {'FINISHED'}
    

    def hasComponents(self, context):
        upperarm_status = context.scene.upperarm is not None
        forearm_status =  context.scene.forearm is not None 
        
        #IMPORTANT: add another check here to check pauldron exists
        
        return (upperarm_status and forearm_status)


    def assignPauldron(self, context):
        self.pauldron = context.scene.padL.name
        #print("self.pauldron assigned as " + self.pauldron)
    
    #get the armature
    def hasArmature(self, context):
        if context.scene.arma is not None:
            armature = context.scene.arma
            
            armature.select_set(True) #is this unecessary? pretty sure select_set will also make it active...
            bpy.context.view_layer.objects.active = armature
            
            self.armature = armature.data
            self.armature_pose = armature.pose
            return True
        
        print('armature missing')
        return False
    
    def checkBones(self, context):
        self.shoulder_bone_name = context.scene.upperarm
        self.forearm_bone_name = context.scene.forearm
        
        print('checking for required bones...')
        bpy.ops.object.mode_set (mode ='EDIT')
        
        shoulder_bone = self.armature.edit_bones[self.shoulder_bone_name]
        forearm_bone = self.armature.edit_bones[self.forearm_bone_name]

        
    #   check that shoulder_bone has a parent, the collarbone
        if shoulder_bone.parent is None:
            print('shoulder bone missing parent')
            bpy.ops.object.mode_set (mode ='OBJECT')
            return False
        
        #compare Y value of vectors of shoulder head and tail
        #WARNING: temporarily disable the following if statemeent in order to test ability to generate bones from a shoulder arm with Y displacement
        if self.has_Y_displacement(context, self.shoulder_bone_name):
            print('shoulder bone has global Y displacement')
            bpy.ops.object.mode_set (mode ='OBJECT')
            return False
        
    #   check that the upper arm bone points at the forearm.head
        if not self.bone_pointed_at_target_bone_head(context, self.shoulder_bone_name, self.forearm_bone_name):
            print('shoulder bone does not point at forearm.head')
            bpy.ops.object.mode_set (mode ='OBJECT')
            return False
    
    #   check that the upper arm bone does not extend longer than forearm.head
        if not self.pointing_bone_shorter_or_equal_to_target_bone_head(context, self.shoulder_bone_name, self.forearm_bone_name):
            print('shoulder_bone.tail must be at forearm.head or shorter. shoulder bone too long.')
            bpy.ops.object.mode_set (mode ='OBJECT')
            return False
        
        
        #if code has reached this point, we can be sure shoulder bone does possess a parent
        self.clavicle_bone_name = shoulder_bone.parent.name
        
        
        #at this point, shoulder bone and forearm have passed all checks
        #notice that copy() is used in order to avoid keeping references to the edit bone's head and tail
        self.upperarm_vectors = [shoulder_bone.head.copy(),forearm_bone.head.copy()]
        
        
        print('all required bones present')
        bpy.ops.object.mode_set (mode ='OBJECT')
        return True


    #given bone name, compare Y values of the bone head and tail vectors
    # being in edit mode before being run
    def has_Y_displacement(self, context, bone_name):
        Y_values_arr = [] #arr to hold y values of head and tail vectors
        
        edit_bone = self.armature.edit_bones[bone_name]
        
        for vector_data in [edit_bone.tail, edit_bone.head]:
            #extracting the Y value of each vector from everything else. 
            vectorValList = str(vector_data)[9:-2].replace(" ", "").split(",")
            Y_values_arr.append(float(vectorValList[1]))
            
        #test print to see if head and tail values sucessfully entered into array
#        for f in Y_values_arr:
#            print(str(f))
        
        #if the head and tail have different Y-values, then the bone has some Y-displacement
        return (Y_values_arr[0] != Y_values_arr[1])

        
    
        
        
        #do 2 things:
        #check the upper arm bone angle is valid
        #if valid, assign to class member self.upperarm_bone_x_angle
        
        #must be in edit mode before being run
        #https://blender.stackexchange.com/questions/70703/bone-angle-in-python
    def checkShoulderAngle(self, context):
        val = True
        
        #this represents a bone pointed in the global +x axis, used to calculate upper arm bone position
        #WARNING: this will have to change when doing calculations for right side of rig.
        head = Vector((0.0, 0.0, 0.0))
        tail = Vector((1.0, 0.0, 0.0))
        
        #switch back to object mode in order to register
        bpy.ops.object.mode_set (mode ='POSE')

        #for b in self.armature.bones:
            #print(b.name)

        pb1 = self.armature_pose.bones.get(self.shoulder_bone_name)

        v1 = pb1.head - pb1.tail
        v2 = head - tail
        
        #"upperarm_bone_x_angle" refers to the arm bone x rotation angle IN DEGREES!
        #this is the angle between the upperarm bone and a vertical line pointed straight down from origin.
        upperarm_bone_x_angle = round(degrees(v1.angle(v2)), 0) #round to nearest whole number
        print("upper arm bone x rotation angle, degrees: " + str(upperarm_bone_x_angle))
        
        
        #return to edit mode for the next function to run use.
        bpy.ops.object.mode_set (mode ='EDIT')
        
        
        #the main job of this function is to exclude abnormal angles.
        if upperarm_bone_x_angle < 0 or upperarm_bone_x_angle > 90:
            #testing
            print('upper arm bone angle bad. Angle must be in [0, 90)]')
            val = False
        else:
            print('upper arm bone angle good')
            self.upperarm_bone_x_angle = upperarm_bone_x_angle #assign to global variable for use later.

        return val


    
     
    
    #must be in object mode to run
    #remove all extraneous bones from armature, regardless of R or L side.   
    def clean_all(self, context):
        #---business logic for bone removal not available in this demo---
        
        bpy.ops.object.mode_set (mode ='OBJECT')
    
    
    
    def makeBones(self, context):
        #---business logic for bone generation not available in this demo---
        bpy.ops.object.mode_set (mode ='OBJECT')
        return True
        
        
        
        
        
        #relative to +X global bone axis:
        #given a bone at a certain angle, if I were to rotate this bone (pivot point at bone.head) along global Y axis to a targetAngle,
        #what is the bone's tail vector?
        #accomplish this without actually rotating the bone.
        #currentAngle and targetAngle must be in DEGREES
    def calculateTailVectorIfBoneAtTargetAngle(self, context, targetAngle, currentAngle, boneHead, boneVector):
        if targetAngle == currentAngle:
            #just return the original tail vector. the bone is already at sourceAngle
            return boneHead + boneVector
        

        need_this_angle_to_reach_targetAngle = targetAngle - currentAngle
        
        
        #print("need_this_angle_to_reach_80deg:  " + str(need_this_angle_to_reach_80deg))
        
        DegRot = Matrix.Rotation(radians(need_this_angle_to_reach_targetAngle), 4, "Y")
        
        
        rotation_vec = boneVector
        
        #print('vector before rotation' + str(rotation_vec))
        
        rotation_vec.rotate(DegRot) #this only rotates the vector, will not return anything
        
        #print('vector after rotation' + str(rotation_vec))
        
        
        
        position_tail_at_80deg = boneHead + rotation_vec
        #-------------------------------------------------------------------------------tested.
        
        return position_tail_at_80deg
        
        

        #point the bone's tail at the targetBone's head
        #assumes you are in edit mode
    def pointBoneAtTargetBoneHead(self, context, pointerBoneName, targetBoneName):
        pb = self.armature.edit_bones[pointerBoneName]
        target = self.armature.edit_bones[targetBoneName]
        
        v = target.head - pb.head
        #v is the displacement vector, calculated by targetbone.head - pointerbone.head
        #pointerbone must displace by v in order to point at targetbone.head.
        
        #bv is the bone vector, between head and tail of spine bone
        bv = pb.tail - pb.head

        rd = bv.rotation_difference(v)
        #print(str(type(rd)))

        
        #otation_difference() gives quarternions, which are converted to_matrix()
        
        M = (  #make transformation matrix
            Matrix.Translation(pb.head) @
            rd.to_matrix().to_4x4() @
            Matrix.Translation(-pb.head)
            )
        pb.matrix = M @ pb.matrix #modify pointer bone's matrix in order to apply transform it.
    
    
    #parent mesh to bone
    #requires armature.data to be saved as class member
    def parentMeshToBone(self, context, mesh_name, bone_name):
        #https://blender.stackexchange.com/questions/77465/python-how-to-parent-an-object-to-a-bone-without-transformation
        #obj = self.pauldron
        arma = bpy.context.scene.objects.get(self.armature.name)
        obj = bpy.context.scene.objects.get(mesh_name)
        
        #deselect everything while in object mode before trying to parent
        bpy.ops.object.select_all(action='DESELECT')
        
        #set armature object as selcted
        arma.select_set(True)
        
        #set the armature object as active
        bpy.context.view_layer.objects.active = arma
        
        bpy.ops.object.mode_set(mode='EDIT')
        arma.data.edit_bones.active = arma.data.edit_bones[bone_name]
        print("parenting " + obj.name + " to " + 'xz_rotator.' + self.side)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        obj.select_set(True)
        arma.select_set(True)
        bpy.context.view_layer.objects.active = arma
        bpy.ops.object.parent_set(type='BONE')
        
    
    #assumes you are in edit mode
    #create a non-deforming duplicate, given a list[head vector, tail vector] to copy
    def duplicateBone(self, context, newBoneName, boneVectorsToCopy, nameOfParentBone):
        
        newBone = self.armature.edit_bones.new(newBoneName)
        
        newBone.head = boneVectorsToCopy[0]
        newBone.tail = boneVectorsToCopy[1]
        
        #give matrix of shoulder
        #shoulder_bone = self.armature.edit_bones[self.shoulder_bone_name]
        #newBone.matrix = shoulder_bone.matrix
        
        newBone.parent = self.armature.edit_bones[nameOfParentBone]
        newBone.use_deform = False
        

        return newBone
    
    
    #given a bone, see if it is pointed at the head of a given target bone.
    def bone_pointed_at_target_bone_head(self, context, pointer_bone_name, target_bone_name):
        #target_bone_vector = self.armature.edit_bones[target_bone_name].vector.copy()
        target_bone_head = self.armature.edit_bones[target_bone_name].head.copy()
        
        pointer_bone_vector = self.armature.edit_bones[pointer_bone_name].vector.copy()
        pointer_bone_head = self.armature.edit_bones[pointer_bone_name].head.copy()
        
        
        #make vector from pointer.head to target.head
        pointerToTargetVector =  target_bone_head - pointer_bone_head
        
        
        #rotational diff between (pointer_bone_vector) and (pointerToTargetVector) should be zero
        return(degrees(pointerToTargetVector.angle(pointer_bone_vector)) == 0)
    
    
    
    #given a bone pointed at a given target bone
    #see if pointer_bone.tail overlaps/inersects/goes past the target_bone.head
    def pointing_bone_shorter_or_equal_to_target_bone_head(self, context, pointer_bone_name, target_bone_name):
        #(dist from pointerBone.head to pointerBone.tail) <= (dist from pointerBone.head to targetBone.head)

        
        target_bone_vector = self.armature.edit_bones[target_bone_name].vector.copy()
        target_bone_head = self.armature.edit_bones[target_bone_name].head.copy()
        
        
        pointer_bone_vector = self.armature.edit_bones[pointer_bone_name].vector.copy()
        pointer_bone_head = self.armature.edit_bones[pointer_bone_name].head.copy()

        
        pointerToTargetVector =  target_bone_head - pointer_bone_head
        
        #theory 1:
        return(pointer_bone_vector <= pointerToTargetVector)
    #-------------------------------------------------------------
    
    
    


class TestPanel(bpy.types.Panel):
    bl_label = "Test Panel" #give it text
    bl_idname = "PANEL123_PT_TestPanel"  #give panel an identification name
    
    #where to sit on screen
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Pauldron Rigger'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        #https://blender.stackexchange.com/questions/177368/how-do-i-use-multiple-columns-in-my-add-on-ui
        #column_flow = layout.column_flow(columns=2, align=False)
        
        #https://blenderartists.org/t/how-to-draw-an-object-selection-eyedropper-in-an-addon/1287437/8
        row2 = layout.row()
        row2.prop(scene, "padL") #show left eyedropper
        
        row3 = layout.row()
        row3.prop(scene, "arma")
        
        row4 = layout.row()
        if scene.arma is not None:
            row4.prop(scene, "upperarm")

        row5 = layout.row()
        if all([scene.arma, scene.upperarm]):
            row5.prop(scene, "forearm")

        row = layout.row()
        row.operator(rigit.bl_idname)

        
#mesh objects only
def meshes_only_poll(self, object):
        return object.type == 'MESH'

#armature objects only
def armature_only_poll(self, object):
        return object.type == 'ARMATURE'

#https://blender.stackexchange.com/questions/19293/prop-search-armature-bones
def bone_items(self, context):
    if self.arma is None:
        return [("NONE", "None", "", 0)]
    arma = context.scene.objects.get(self.arma.name)
    return [(bone.name, bone.name, "") for bone in arma.data.bones if bone.name[-1] == "L"]


def forearm_items(self, context):
    if self.arma is None:
        return [("NONE", "None", "", 0)]
    if self.upperarm is None:
        return [("NONE", "None", "", 0)]
    arma = context.scene.objects.get(self.arma.name)
    return [(child.name, child.name, "") for child in arma.data.bones[self.upperarm].children]


classes = (rigit, TestPanel)


def register():
    bpy.types.Scene.forearm = bpy.props.EnumProperty(items=forearm_items)
    bpy.types.Scene.upperarm = bpy.props.EnumProperty(items=bone_items)
    
    #https://blender.stackexchange.com/questions/213735/how-to-pick-an-object-before-operator-execution-object-picker-pointer-ux
    bpy.types.Scene.arma = PointerProperty(
        type=bpy.types.Object,
        poll=armature_only_poll,
        )
    
    bpy.types.Scene.padL = PointerProperty(
        type=bpy.types.Object,
        poll=meshes_only_poll,
        )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    del bpy.types.Scene.bone
    del bpy.types.Scene.arma
    del bpy.types.Scene.padL

    
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()