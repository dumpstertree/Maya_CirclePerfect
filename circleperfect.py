import maya.cmds as cmds
import maya.mel as mel
import AdvancedUI as ui
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import math
import random
import sys

class Position :
	x = 0
	y = 0
	z = 0

kPluginCmdName = "vertSnappy"
shelfName = "circle perfect"

uiName = "CIRCLEPERFECT"
toolName = "circle perfect"
uiHeaderHeight_GLOBAL = 21
uiBodyHeight_GLOBAL = 82

activeScriptJobs_PUBLIC = []
activeObjects_PUBLIC 	= []
storedObjects_PUBLIC 	= []

storedUI_PUBLIC	 = None
HUDobject_PUBLIC = None
cylObject_PUBLIC = None
centerPos_PUBLIC = Position
width_PUBLIC 	 = 0

currentUIStatus_PUBLIC  = 0

red		=[.8,.5,.5]
green	=[.5,.8,.5]
blue	=[.5,.5,.8]
black	=[.1,.1,.1]
white 	=[.9,.9,.9]

#############
#	UI
#############
def UI_create():
	UI_checkforExisting()
	UI_createWindow()
	UI_createBody()
	UI_display()
	UI_refresh()
	findDifference()

def UI_checkforExisting():
	if  cmds.window( uiName, exists=True):
		cmds.deleteUI( uiName, window=True)   
	if  cmds.windowPref( uiName, exists=True ):
		cmds.windowPref( uiName, remove=True )	

def UI_createWindow():
	global white
	cmds.window(uiName, title="", minimizeButton=False, maximizeButton=False, sizeable=False, h=1, rtf=False, bgc=white)

def UI_createBody():
	global storedUI_PUBLIC
	
	windowWidth = 120
	mainLayout = cmds.columnLayout("mainUI_C", parent=uiName, bgc = white )

	Title = cmds.rowColumnLayout(numberOfColumns=3, cw=[(1, windowWidth * .15),(2, windowWidth * .7),(3, windowWidth * .15)], p=mainLayout)
	cmds.separator(h=10,vis=True)
	cmds.text('title', label = "", align = "center", font = "boldLabelFont")
	cmds.separator(h=10,vis=True)

	cmds.rowColumnLayout(numberOfColumns=1, cw=[(1, windowWidth)], p=mainLayout)
	cmds.separator(h=5,vis=False)
	cmds.separator(h=1,vis=True)

	buttonLayout = cmds.rowColumnLayout(numberOfColumns=3, cw=[(1, windowWidth * .1),(2, windowWidth * .8),(3, windowWidth * .1)], p=mainLayout)
	cmds.separator(h=10,vis=False)
	cmds.button("mainButton", label="", h = 30, bgc=black, c=lambda arg: moveToNextPhase())
	cmds.separator(h=10,vis=False)

	cmds.rowColumnLayout(numberOfColumns=1, cw=[(1, windowWidth)], p=mainLayout)
	cmds.separator(h=1,vis=True)
	cmds.separator(h=10,vis=False)
	cmds.text(label = "@dumpstertree", font = "smallPlainLabelFont", align = "center")

	storedUI_PUBLIC = mainLayout

def UI_display():
	global uiHeaderHeight_GLOBAL
	global uiBodyHeight_GLOBAL

	cmds.showWindow(uiName) 
	ui.openAnimation(uiName, 1, uiHeaderHeight_GLOBAL, .2)
	ui.textTypingAnimation( 'title', toolName, .2)
	ui.openAnimation(uiName, uiHeaderHeight_GLOBAL, uiBodyHeight_GLOBAL, .3)

def UI_refresh():
	global currentUIStatus_PUBLIC

	if currentUIStatus_PUBLIC == 0:
		ui.buttonTypingAnimation("mainButton", "use verts", .2)

	if currentUIStatus_PUBLIC == 1:
		ui.buttonTypingAnimation("mainButton", "finish", .2)

def UI_close():
	killAllScriptJobs()
	destroyHUD()



#############
#	PHASES
#############
def moveToNextPhase():
	global currentUIStatus_PUBLIC

	if currentUIStatus_PUBLIC == 0:

		if breaker() == False:
			return None
		
		endPhase_0()
		currentUIStatus_PUBLIC = 1
		initializePhase_1()
		
		return None
	
	if currentUIStatus_PUBLIC == 1:

		endPhase_1()
		currentUIStatus_PUBLIC = 0
		initializePhase_0()

		return None

def initializePhase_0():
	
	UI_refresh()

def endPhase_0():
	global activeObjects_PUBLIC
	global centerPos_PUBLIC
	global width_PUBLIC
	global cylObject_PUBLIC
	global storedObjects_PUBLIC
	
	centerPos = findCenter_LIST(activeObjects_PUBLIC)
	width = findWidth_FLOAT(activeObjects_PUBLIC,centerPos)
	cyl = createCyl(centerPos,width,activeObjects_PUBLIC)
	
	centerPos_PUBLIC.x = centerPos[0]
	centerPos_PUBLIC.y = centerPos[1]
	centerPos_PUBLIC.z = centerPos[2]
	width_PUBLIC = width
	cylObject_PUBLIC = cyl[0]
	storedObjects_PUBLIC = activeObjects_PUBLIC[:]

	moveCyl()
	rotateCyl()
	snapToCyl()

	clearactiveObjects_PUBLIC()

	ui.pulseAnimation( 'mainUI_C', 1, .4, green)

def initializePhase_1():
	UI_refresh()
	
	drawHUD()
	rotateHUD()
	moveHUD()

	findRotation()
	lockCylToHUD()
	hideCyl()
	turnOnTrackHUDMovement()

	zoomCamera()

	cmds.select(HUDobject_PUBLIC)

def endPhase_1():
	destroyHUD()
	ui.pulseAnimation( 'mainUI_C', 1, .4, green)



#############
#	CYL
#############
def findCenter_LIST(vertListFlattened):
	totalX = 0
	totalY = 0
	totalZ = 0

	for verts in vertListFlattened:
		vertPosition = cmds.pointPosition([verts],w=True)
		totalX = totalX + vertPosition[0]
		totalY = totalY + vertPosition[1]
		totalZ = totalZ + vertPosition[2]

	averageX = totalX/len(vertListFlattened)
	averageY = totalY/len(vertListFlattened)
	averageZ = totalZ/len(vertListFlattened)
	return [averageX, averageY, averageZ]				#returns [ int ]

def findWidth_FLOAT(vertListFlattened,centerPos):
	totalDistance = 0
	
	for verts in vertListFlattened:
		vertPosition = cmds.pointPosition([verts],w=True)
		distance = GetDistanceBetweenObjects(centerPos,vertPosition)
		totalDistance = totalDistance + distance
	averageDistance = totalDistance/len(vertListFlattened)
	
	return averageDistance	#returns float		

def createCyl(pos,width,vertListFlattened):
	cyl = cmds.polyCylinder(radius=width, sx=len(vertListFlattened), height=0)
	
	unNeededFaces = []
	for faces in range(len(vertListFlattened)+1):
		faceName = str(cyl[0])+".f[" + str(faces) + "]"
		unNeededFaces.append( faceName )
	cmds.delete(unNeededFaces)
	
	return cyl

def moveCyl():
	global cylObject_PUBLIC
	global centerPos_PUBLIC

	cmds.move(centerPos_PUBLIC.x,centerPos_PUBLIC.y,centerPos_PUBLIC.z, cylObject_PUBLIC)

def rotateCyl():
	global storedObjects_PUBLIC
	global cylObject_PUBLIC

	extra = 360 / len(storedObjects_PUBLIC)
	
	cmds.rotate(0,0,180, cylObject_PUBLIC, ws=True,a=True)
	cmds.makeIdentity(cylObject_PUBLIC, apply=True, t=1, r=1, s=1, n=0)

	cmds.rotate(0,extra*2,180, cylObject_PUBLIC, ws=True, r=True)

def findRotation():
	global storedObjects_PUBLIC
	global cylObject_PUBLIC
	global centerPos_PUBLIC
	global HUDobject_PUBLIC

	firstVertPos = cmds.xform(storedObjects_PUBLIC[0], query=True, ws=True, a=True, t=True)
	
	firstPoint_x = centerPos_PUBLIC.x
	firstPoint_z = centerPos_PUBLIC.z
	secondPoint_x = firstVertPos[0]
	secondPoint_z = firstVertPos[2]

	deltaY =  firstPoint_z - secondPoint_z
	deltaX =  firstPoint_x - secondPoint_x

	#angleInDegrees =  270 + abs(math.atan2(deltaY, deltaX) * 180 / math.pi)
	angleInDegrees =  abs(math.atan2(deltaY, deltaX) * 180 / math.pi)

	ahh = math.atan2(deltaY, deltaX) * 180 / math.pi

	cmds.rotate(angleInDegrees, HUDobject_PUBLIC, y=True, xz=False, r=True, ws=True)
	cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
	
def snapToCyl():
	global cylObject_PUBLIC
	global storedObjects_PUBLIC
	global HUDobject_PUBLIC
	
	cmds.undoInfo(openChunk=True)
	
	listOfCylVertPos = []
	
	for verts in range(len(storedObjects_PUBLIC)):
		vertName = str(cylObject_PUBLIC) +".vtx[" + str(verts)+ "]"
		vertPosition = cmds.xform(vertName, q=True, a=True, ws=True, t=True)
		
		listOfCylVertPos.append(vertPosition)

	counter = 0
	for objects in storedObjects_PUBLIC:
		currentPos = listOfCylVertPos[counter]
		cmds.xform(objects, t=(currentPos[0],currentPos[1],currentPos[2]), a=True, ws=True,)
		
		counter += 1

	cmds.undoInfo(closeChunk=True)



#############
#	SCRIPTJOBS
#############
def startScriptJobs():
	listenForChangedSelection = cmds.scriptJob(event=['SelectionChanged', lambda : findDifference()], protected=True)
	lisitenForNoSelection = cmds.scriptJob(conditionFalse=['SomethingSelected', lambda : clearactiveObjects_PUBLIC()], protected=True)
	
	listenForUIClose = cmds.scriptJob( uid = [uiName, lambda : UI_close()], protected=True)

	activeScriptJobs_PUBLIC.append(listenForChangedSelection)
	activeScriptJobs_PUBLIC.append(lisitenForNoSelection)

def killAllScriptJobs():
	global activeScriptJobs_PUBLIC
	for activeJobs_iteration in activeScriptJobs_PUBLIC:
		cmds.scriptJob(kill=activeJobs_iteration, force=True)
		activeScriptJobs_PUBLIC.remove(activeJobs_iteration)
	clearactiveObjects_PUBLIC()



#############
#	TRACK SELECTIONS
#############
def findDifference():
	selection = cmds.ls(sl=True, fl=1)
	new = getNewObjects_LIST( selection )
	lost = getLostObjects_LIST( selection )

	addToactiveObjects_PUBLIC( new )
	removeFromactiveObjects_PUBLIC( lost )

def getNewObjects_LIST(selection):						# returns [ string ]
	newObjects = []
	for selection_iteration in selection:
		if selection_iteration not in activeObjects_PUBLIC:
			newObjects.append(selection_iteration)
	return newObjects

def getLostObjects_LIST(selection):						# returns [ string ]
	lostObjects = []
	for activeObjects_PUBLIC_iteration in activeObjects_PUBLIC:
		if activeObjects_PUBLIC_iteration not in selection:
			lostObjects.append(activeObjects_PUBLIC_iteration)
	return lostObjects

def convertListToStrings(convertingList):
	returnList = []
	for iteration in convertingList:
		iterationName = str(convertingList) 		#converted to a string in order to prevent condensing
		returnList.append(iterationName)
	return returnList

def addToactiveObjects_PUBLIC(objectList):
	global activeObjects_PUBLIC
	for objects in objectList:
		activeObjects_PUBLIC.append(objects)

def removeFromactiveObjects_PUBLIC(objectList):
	global activeObjects_PUBLIC
	for objects in objectList:
		activeObjects_PUBLIC.remove(objects)

def clearactiveObjects_PUBLIC():
	global activeScriptJobs_PUBLIC
	activeObjects_PUBLIC = []



#############
#	HUD
#############
def drawHUD():
	global HUDobject_PUBLIC
	global width_PUBLIC
	
	diameter = width_PUBLIC
	diameterBuffer = 1.2
	anchorRadius = .2
	normalLength  = 1
	
	parent = cmds.group(empty=True, n="_rotationHUD")
	border = cmds.circle(radius=diameter * diameterBuffer)
	exact = cmds.circle(radius=diameter)
	anchor = cmds.circle(radius=anchorRadius)
	normal = cmds.curve( p=[(0, 0, 0), (0, 0, -normalLength)], degree = 1)

	borderShapeNode = cmds.listRelatives(border, shapes=True)
	exactShapeNode = cmds.listRelatives(exact, shapes=True)
	anchorShapeNode = cmds.listRelatives(anchor, shapes=True)
	normalShapeNode = cmds.listRelatives(normal, shapes=True)
	
	cmds.move(0,diameter,0,anchorShapeNode)
	
	cmds.parent( borderShapeNode,parent, s=True, r=True)
	cmds.parent( exactShapeNode, parent, s=True, r=True)
	cmds.parent( normalShapeNode,parent, s=True, r=True)
	cmds.parent( anchorShapeNode,parent, s=True, a=True)

	cmds.delete(border)
	cmds.delete(exact)
	cmds.delete(anchor)
	cmds.delete(normal)
	
	HUDobject_PUBLIC = parent
	cmds.lockNode(HUDobject_PUBLIC, lock=True)

	cmds.select(HUDobject_PUBLIC)

def rotateHUD():
	global HUDobject_PUBLIC
	
	cmds.rotate(90,0,0, HUDobject_PUBLIC, ws=True, a=True)
	cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
	
	cmds.rotate(0,270,0, HUDobject_PUBLIC, ws=True, r=True)

def moveHUD():
	global HUDobject_PUBLIC
	global centerPos_PUBLIC
	cmds.move(centerPos_PUBLIC.x,centerPos_PUBLIC.y, centerPos_PUBLIC.z, HUDobject_PUBLIC)
	cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)

def destroyHUD():
	global HUDobject_PUBLIC
	if HUDobject_PUBLIC != None:
		if cmds.objExists(HUDobject_PUBLIC):
			cmds.lockNode(HUDobject_PUBLIC, lock=False)
			cmds.delete(HUDobject_PUBLIC)

def turnOnTrackHUDMovement():
	global HUDobject_PUBLIC

	cylObjectName = str(HUDobject_PUBLIC)

	listenForMovement_x = cmds.scriptJob(attributeChange=[ cylObjectName + '.tx', lambda:snapToCyl() ])
	listenForMovement_y = cmds.scriptJob(attributeChange=[ cylObjectName + '.ty', lambda:snapToCyl() ])
	listenForMovement_z = cmds.scriptJob(attributeChange=[ cylObjectName + '.tz', lambda:snapToCyl() ])

	listenForScale_x = cmds.scriptJob(attributeChange=[ cylObjectName + '.sx', lambda:snapToCyl() ])
	listenForScale_y = cmds.scriptJob(attributeChange=[ cylObjectName + '.sy', lambda:snapToCyl() ])
	listenForScale_z = cmds.scriptJob(attributeChange=[ cylObjectName + '.sz', lambda:snapToCyl() ])

	listenForRotation_x = cmds.scriptJob(attributeChange=[ cylObjectName + '.rx', lambda:snapToCyl() ])
	listenForRotation_y = cmds.scriptJob(attributeChange=[ cylObjectName + '.ry', lambda:snapToCyl() ])
	listenForRotation_z = cmds.scriptJob(attributeChange=[ cylObjectName + '.rz', lambda:snapToCyl() ])

	activeScriptJobs_PUBLIC.append(listenForMovement_x)
	activeScriptJobs_PUBLIC.append(listenForMovement_y)
	activeScriptJobs_PUBLIC.append(listenForMovement_z)

	activeScriptJobs_PUBLIC.append(listenForScale_x)
	activeScriptJobs_PUBLIC.append(listenForScale_y)
	activeScriptJobs_PUBLIC.append(listenForScale_z)

	activeScriptJobs_PUBLIC.append(listenForRotation_x)
	activeScriptJobs_PUBLIC.append(listenForRotation_y)
	activeScriptJobs_PUBLIC.append(listenForRotation_z)



#############
#	MISC
#############
def GetDistanceBetweenObjects(pos1,pos2):
    distanceNode = cmds.distanceDimension(sp=(pos1[0],pos1[1],pos1[2]),ep=(pos2[0],pos2[1],pos2[2]))
    distance = cmds.getAttr( distanceNode +".distance")
    cmds.delete(distanceNode)
    if cmds.objExists('locator1'):
    	cmds.delete('locator1')
    if cmds.objExists('locator2'):
    	cmds.delete('locator2')
    if cmds.objExists('distanceDimension1'):
    	cmds.delete('distanceDimension1')
    return distance

def FindMatchesInLists(list1,list2):
	matches = []
	for num1 in list1:
		for num2 in list2:
			if (num1 == num2):
				matches.append(num1)

	return matches
 
def zoomCamera():

	cmds.viewFit(animate=True)

def lockCylToHUD():
	global cylObject_PUBLIC
	global HUDobject_PUBLIC

	cmds.parent(cylObject_PUBLIC,HUDobject_PUBLIC)

def hideCyl():
	global cylObject_PUBLIC
	cmds.hide( cylObject_PUBLIC )

def breaker():
	selectedObjects = cmds.ls(sl=True,fl= 1)

	if len(selectedObjects) < 4 :										# more than 4 verts
		cmds.warning("please select at least 4 verts; aborted")
		
		ui.flashAnimation( 'mainUI_C', 2, .05, black )
		ui.shakeAnimation( uiName, .2, 10 )
		
		return False
	
	selectedVertComponents = cmds.polyEvaluate(vertexComponent=True )	# only verts
	if len(selectedObjects) != selectedVertComponents:
		cmds.warning("please select only verts; aborted")
		
		ui.flashAnimation( 'mainUI_C', 2, .05, black )
		ui.shakeAnimation( uiName, .2, 10 )
		
		return False
	
	return True



#############
#	PLUG-IN
#############

class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    def doIt(self,argList):
        UI_create()
        startScriptJobs()

def cmdCreator():

    return OpenMayaMPx.asMPxPtr( scriptedCommand() )
 
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand( kPluginCmdName, cmdCreator )
        createShelf()
    except:
        sys.stderr.write( "Failed to register command: %s\n" % kPluginCmdName )
        raise

def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand( kPluginCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % kPluginCmdName )

def createShelf():
	if cmds.layout( dumpstertree, q=True, e=True) == False:
		mel.eval('addNewShelfTab "dumpstertree";')

	exists = False
	children = cmds.layout(dumpstertree, q=True, ca=True )
	if children != None:
		for buttons in children:
			if cmds.shelfButton(buttons, q=True, l=True) == toolName:
				exists = True
	
	if exists == False:
		cmds.shelfButton(buttonName, l=toolName, annotation='make a perfect circle', image1='circleperfect_icon.png', command='cmds.circlePerfect()', p=shelfName)
