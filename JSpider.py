from Adafruit_PWM_Servo_Driver import PWM
from subprocess import call
import pygame
import time
import sys
import math

pwm = PWM(0x40)
pwm.setPWMFreq(60)

class Angle:
	value = 0
	def __init__(this, angleInDegree):
		this.value = angleInDegree
	
	def getAngle(this):
		return this.value;

	def sanctify(this):
		this.value = Angle.sanctify(this.value)
	
	@staticmethod
	def sanctify(angle):
		angleInDegree = angle % 360
		if(angleInDegree < 0):
			angleInDegree = 360 - angleInDegree
		return angleInDegree
		
	@staticmethod
	def getAngleDistanceInForward(angleInDegreeFrom, angleInDegreeTo):
		return abs(angleInDegreeTo - angleInDegreeFrom) if angleInDegreeTo > angleInDegreeFrom else abs((angleInDegreeTo + 360) - angleInDegreeFrom) % 360
	
	@staticmethod
	def getAngleDistanceInBackward(angleInDegreeFrom, angleInDegreeTo):
		return abs(angleInDegreeFrom - angleInDegreeTo) if angleInDegreeFrom > angleInDegreeTo else abs((angleInDegreeFrom + 360) - angleInDegreeTo) % 360
	
	def setAngle(this, angle):
		this.value = angle
		sanctify()
		
	def getRadians(this):
		return float(this.value) * 0.01745329251
		
	def setRadians(this, radians):
		this.value = radians * 565.486677646
		sanctify()
		
		

class JSpiderJoint:
	port = 0
	minimumPower = 300
	maximumPower = 600
	minToMaxPowerVector = 0
	
	minAngle = 0
	maxAngle = 0
	minToMaxAngleVector = 0

	currentPower = 0
	currentRate = 0
	currentAngle = 0
	
	
	def __init__(this, port, minPower, maxPower, minMappedDegree = 0, maxMappedDegree = 0, doesIncreaseToReachMax = False):
		this.port = port
		this.minimumPower = minPower
		this.maximumPower = maxPower
		this.minToMaxPowerVector = maxPower - minPower

		# I assume that values are already in range of 0 to 360. 
		this.minAngle = minMappedDegree#Angle(minMappedDegree)
		this.maxAngle = maxMappedDegree#Angle(maxMappedDegree)
		
		# This will make decreasing vector less than or equal to 0, increasing vector more than 0.
		if(doesIncreaseToReachMax): #increasing
			if(minMappedDegree < maxMappedDegree):
				this.minToMaxAngleVector = maxMappedDegree - minMappedDegree;
			else:
				this.minToMaxAngleVector = (maxMappedDegree + 360) - minMappedDegree
		else: #decreasing
			if(minMappedDegree < maxMappedDegree):
				this.minToMaxAngleVector = maxMappedDegree - (minMappedDegree + 360);
			else:
				this.minToMaxAngleVector = maxMappedDegree - minMappedDegree
	
	def move(this, inputPower):
		power = min(max(inputPower, this.minimumPower), this.maximumPower)
		this.currentPower = power;
		if this.isPinPort(this.port):
			call("echo " + str(-this.port) + "=" + str(power) + ">/dev/servoblaster", shell=True)
		else:
			pwm.setPWM(this.port, 0, power)
	
	def getInfo(this):
		print "-------------"
		print "port: " + str(this.port)
		print "currentPower: " + str(this.currentPower)
		print "currentRate: " + str(this.currentRate)
		print "currentAngle: " + str(this.currentAngle)
		print "maxAngle: " + str(this.maxAngle)
		print "minAngle: " + str(this.minAngle)
		print "minToMax: " + str(this.minToMaxAngleVector)
		print "-------------"
	
	def clampRate(this, rate):
		return max(min(rate, 1), 0)
	
	def convertRateToPower(this, clampedRate):
		return (int(this.minimumPower + this.minToMaxPowerVector * clampedRate))
	
	def convertAngleToRate(this, clampedAngle):
		# while(clampedAngle > this.minAngle):
		#	clampedAngle = clampedAngle - 360
		if(this.minToMaxAngleVector > 0 and clampedAngle < this.minAngle):
			clampedAngle = clampedAngle + 360
		if(this.minToMaxAngleVector < 0 and clampedAngle > this.minAngle):
			clampedAngle = clampedAngle - 360
		
		rate = (clampedAngle - this.minAngle) / this.minToMaxAngleVector
		print "angle " + str(clampedAngle) + " converted to rate " + str(rate)
		return rate
		
	
	def stop(this):
		if this.isPinPort(this.port):
			call("echo " + str(-this.port) + "=" + str(0) + ">/dev/servoblaster", shell=True)
		else:
			pwm.setPWM(this.port, 0, 0)
	
	def isPinPort(this, port):
		return port < 0
	
	def moveByRate(this, rate):
		rate = this.clampRate(rate)
		this.currentRate = rate;
		this.move(this.convertRateToPower(rate))
	
	def moveByAngle(this, angleInDegree):
		angleInDegree = this.clampAngle(angleInDegree)
		this.currentAngle = angleInDegree
		rate = this.convertAngleToRate(angleInDegree)
		this.moveByRate(rate)
	
	def graduallyMoveToAngle(this, targetAngle, duration, subdivide = 5):
		# this does not work because all points in between must be valid. 
		# differences = targetAngle - currentAngle
		# going to subdivide angles into multiple, and check if they are valid
		# subdivide could work in most cases, but it doesn't work if dead angle is very tiny. 
		# should have more solid algorithm for detecting correct angle...
		
		# min to max angle vector already have it figured out
		# so i should use find current rate, and find target rate, and get vector. 
		startRate = this.currentRate
		targetRate = this.convertAngleToRate(targetAngle)
		
		# so i can subdivide this rate!
		rateVector = targetRate - startRate
		dividedRateVector = rateVector / subdivide
		delayDuration = duration / subdivide
		
		# this is LOCAL
		currentRate = startRate
		# this is bad because it will block other operations.
		# should be async operation... or have general loop. 
		for x in range(0, int(subdivide)):
			time.sleep(delayDuration)
			# this is LOCAL TOO
			currentRate = currentRate + dividedRateVector
			this.moveByRate(currentRate)
		
	def isAngleInRange(this, angleInDegree):
		angleInDegree = Angle.sanctify(angleInDegree) # case 3 and 4
		if(this.minAngle < this.maxAngle):
			if(this.minToMaxAngleVector > 0):
				#case 1
				return this.isNumberInBetween(this.minAngle, this.maxAngle, angleInDegree)
			else:
				#case 2
				return not this.isNumberInBetween(this.minAngle, this.maxAngle, angleInDegree)
		else:
			if(this.minToMaxAngleVector > 0):
				#case 5, flip min and max, and do case 2 chk. 
				return not this.isNumberInBetween(this.maxAngle, this.minAngle, angleInDegree)
			else:
				#case 6
				return this.isNumberInBetween(this.maxAngle, this.minAngle, angleInDegree)

	def isNumberInBetween(this, min, max, a):
		return min <= a and max > a
	
	#clamps given angle to max and min angle
	def clampAngle(this, angleInDegree):
		originalAngleInDegree = angleInDegree
		angleInDegree = Angle.sanctify(angleInDegree)
		print "angleInDegree " + str(originalAngleInDegree) + " was sanctified to " + str(angleInDegree)
		if(this.isAngleInRange(angleInDegree) is False):
			forwardDistanceFromMinAngle = Angle.getAngleDistanceInForward(angleInDegree, this.minAngle)
			forwardDistanceFromMaxAngle = Angle.getAngleDistanceInForward(angleInDegree, this.maxAngle)
			backwardDistanceFromMinAngle = Angle.getAngleDistanceInBackward(angleInDegree, this.minAngle)
			backwardDistanceFromMaxAngle = Angle.getAngleDistanceInBackward(angleInDegree, this.maxAngle)
			
			print "forwardDistanceFromMinAngle: " + str(forwardDistanceFromMinAngle)
			print "forwardDistanceFromMaxAngle: " + str(forwardDistanceFromMaxAngle)
			print "backwardDistanceFromMinAngle: " + str(backwardDistanceFromMinAngle)
			print "backwardDistanceFromMaxAngle: " + str(backwardDistanceFromMaxAngle)
			
			distanceFromMinAngle = min(forwardDistanceFromMinAngle, backwardDistanceFromMinAngle)
			distanceFromMaxAngle = min(forwardDistanceFromMaxAngle, backwardDistanceFromMaxAngle)
			
			print "distanceFromMinAngle: " + str(distanceFromMinAngle)
			print "distanceFromMaxAngle: " + str(distanceFromMaxAngle)
			
			result = this.minAngle if distanceFromMinAngle < distanceFromMaxAngle else this.maxAngle
			
			print "result: " + str(result)
			
			return result
		else:
			print "angle in degree already clamped"
			return angleInDegree
	

class JSpiderLeg:
	bas = 0
	mid = 0
	tip = 0
	
	def __init__(this, basPort, midPort, tipPort, 
		basMin = 300, basMax = 600, midMin = 300, midMax = 600, tipMin = 300, tipMax = 600,
		basMinMappedDegree = 0, basMaxMappedDegree = 0,
		midMinMappedDegree = 0, midMaxMappedDegree = 0,
		tipMinMappedDegree = 0, tipMaxMappedDegree = 0,
		basDoesIncreaseToReachMax = False,
		midDoesIncreaseToReachMax = False,
		tipDoesIncreaseToReachMax = False
	):
		this.bas = JSpiderJoint(basPort, basMin, basMax, basMinMappedDegree, basMaxMappedDegree, basDoesIncreaseToReachMax)
		this.mid = JSpiderJoint(midPort, midMin, midMax, midMinMappedDegree, midMaxMappedDegree, midDoesIncreaseToReachMax)
		this.tip = JSpiderJoint(tipPort, tipMin, tipMax, tipMinMappedDegree, tipMaxMappedDegree, tipDoesIncreaseToReachMax)
		
	def __getitem__(this, index):
		if index is 0:
			return this.bas
		if index is 1:
			return this.mid
		if index is 2:
			return this.tip
		raise IndexError("JSpiderLeg only has 3 joints")
		
	def getInfo(this):
		this.bas.getInfo()
		this.mid.getInfo()
		this.tip.getInfo()
	
	def moveByEndEffectorPosition(this, EEPosition):
		# assumes that root position is at 0 0 0, 
		# assumes that z axis represents up and down movement
		# and y axis represents forward and backward movement
		# and x axis represents left and right movement
		rootPosition = [ 0, 0, 0 ]
		
		#joint 0 is the first joint that rotates joint 2 and 3 around z axis. 
		joint0Angle = 0
		#joint 1 is the second joint that rotates joint 3 around y axis relative to joint 0. 
		joint1Angle = 0
		#joint 2 is the last joint that rotates EE around y axis relative to joint 1. 
		joint2Angle = 0

		# just like simulation assumes that root is always at 0
		root2EEDirection = Vector3.direction(rootPosition, EEPosition)
		
		joint0AngleInRadius = math.atan2(root2EEDirection[1], root2EEDirection[0])
		
		yVectorOnPlane = Vector3.project(root2EEDirection, [0, 0, 1])
		xVectorOnPlane = Vector3.subtract(root2EEDirection, yVectorOnPlane)
		y = (1 if yVectorOnPlane[2] > 0 else -1) * Vector3.length(yVectorOnPlane)
		planarAngleFromRootToEEInRadius = math.atan2(y, Vector3.length(xVectorOnPlane))
		
		# joint length
		a1 = 7.5
		a2 = 10.5
		D = Vector3.length(root2EEDirection)
		
		
		cosVal = -(math.pow(a2, 2) - math.pow(a1, 2) - math.pow(D, 2)) / (2 * a1 * D)
		cosVal = min(max(cosVal, -1), 1)
		joint1AngleInRadius = math.acos(cosVal) + planarAngleFromRootToEEInRadius
		cosVal = -(math.pow(D, 2) - math.pow(a1, 2) - math.pow(a2, 2)) / (2 * a1 * a2)
		cosVal = min(max(cosVal, -1), 1)
		angle2 = math.acos(cosVal)
		joint2AngleInRadius = angle2 - 3.14159265358979
		
		joint0Angle = math.degrees(joint0AngleInRadius)
		joint1Angle = math.degrees(joint1AngleInRadius)
		joint2Angle = math.degrees(joint2AngleInRadius)
		
		this.bas.moveByAngle(joint0Angle)
		this.mid.moveByAngle(joint1Angle)
		this.tip.moveByAngle(joint2Angle)
		
		print "joint0Angle: " + str(joint0Angle)
		print "joint1Angle: " + str(joint1Angle)
		print "joint2Angle: " + str(joint2Angle)
		# this.bas.graduallyMoveToAngle(joint0Angle, 1, 5)
		# this.mid.graduallyMoveToAngle(joint1Angle, 1, 5)
		# this.tip.graduallyMoveToAngle(joint2Angle, 1, 5)

# it is ok to use array to calculate with vector3 for convinicance. 
class Vector3:
	x = 0
	y = 0
	z = 0
	
	def __init__(this, x, y, z):
		this.x = x
		this.y = y
		this.z = z
		
	def __getitem__(this, index):
		if index is 0:
			return this.x
		if index is 1:
			return this.y
		if index is 2:
			return this.z
		raise IndexError("Vector3 has only 3 axis")
		
	@staticmethod
	def add(vec1, vec2):
		return Vector3(vec1[0] + vec2[0], vec1[1] + vec2[1], vec1[2] + vec2[2])
	
	@staticmethod
	def scale(v, scale):
		return Vector3( v[0] * scale, v[1] * scale, v[2] * scale )
	
	@staticmethod
	def subtract(vec1, vec2):
		return Vector3( vec1[0] - vec2[0], vec1[1] - vec2[1], vec1[2] - vec2[2] )
	
	@staticmethod
	def direction(origin, destination):
		return Vector3.subtract(destination, origin)
		
	@staticmethod
	def project(vec, dir):
		# to project, needs to break down into components. 
		normalized = Vector3.normalize(vec)

		xUnit = 0 if normalized[0] == 0 else dir[0] / normalized[0]
		yUnit = 0 if normalized[1] == 0 else dir[1] / normalized[1]
		zUnit = 0 if normalized[2] == 0 else dir[2] / normalized[2]
		
		return Vector3.scale(dir, Vector3.dot(dir, vec) / math.pow(Vector3.length(dir), 2))
		
		
	@staticmethod
	def angleBetweenVector(v1, v2):
		dot = Vector3.dot(v1, v2)
		angle = math.acos(dot)
		return angle
	
	@staticmethod
	def dot(v1, v2):
		return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
		

	@staticmethod
	def normalize(vec):
		length = Vector3.length(vec)
		normalizedVector = Vector3(vec[0], vec[1], vec[2])
		return Vector3.scale(normalizedVector, length)
		
	@staticmethod
	def length(vec):
		return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2])

	
# pose represents a single configuration for ALL legs. 
class SpiderPose:
	fl = [ 0, 0, 0 ]
	fr = [ 0, 0, 0 ]
	cl = [ 0, 0, 0 ]
	cr = [ 0, 0, 0 ]
	bl = [ 0, 0, 0 ]
	br = [ 0, 0, 0 ]
	
	def __init__(this, fl, fr, cl, cr, bl, br):
		this.fl = fl
		this.fr = fr
		this.cl = cl
		this.cr = cr
		this.bl = bl
		this.br = br
	
	def Add(this, fl, fr, cl, cr, bl, br):
		this.fl = Vector3.add(this.fl, fl)
		this.fr = Vector3.add(this.fr, fr)
		this.cl = Vector3.add(this.cl, cl)
		this.cr = Vector3.add(this.cr, cr)
		this.bl = Vector3.add(this.bl, bl)
		this.br = Vector3.add(this.br, br)
	
	
	# fl fr cr cl br bl are bool
	def ModifyPose(this, fl, fr, cl, cr, bl, br, vec):
		if(fl):
			this.fl = Vector3.add(this.fl, vec)
		if(fr):
			this.fr = Vector3.add(this.fr, vec)
		if(cl):
			this.cl = Vector3.add(this.cl, vec)
		if(cr):
			this.cr = Vector3.add(this.cr, vec)
		if(bl):
			this.bl = Vector3.add(this.bl, vec)
		if(br):
			this.br = Vector3.add(this.br, vec)
	
	def ModifyJigJagLeft(this, vec):
		this.ModifyPose(True, False, False, True, True, False, vec)
	
	def ModifyJigJagRight(this, vec):
		this.ModifyPose(False, True, True, False, False, True, vec)
		
	def ModifyLeft(this, vec):
		this.ModifyPose(True, False, True, False, True, False, vec)
	
	def ModifyRight(this, vec):
		this.ModifyPose(False, True, False, True, False, True, vec)
	
	
	@staticmethod
	def GetPoseByName(name):
		if(name == "idle"):
			return SpiderPose.GetIdlePose()
		elif(name == "forward1"):
			return SpiderPose.GetForward1Pose()
		elif(name == "forward2"):
			return SpiderPose.GetForward2Pose()
		elif(name == "forward3"):
			return SpiderPose.GetForward3Pose()
		elif(name == "forward4"):
			return SpiderPose.GetForward4Pose()
		
		raise IndexError("Pose name " + str(name) + " is invalid")
		
	@staticmethod
	def GetIdlePose():
		pose = SpiderPose(
			[8, 5, -12], [-8, 5, -12],
			[8, 0, -12], [-8, 0, -12], 
			[8, -5, -12], [-8, -5, -12]
		)
		return pose
		
	@staticmethod
	def GetForward1Pose():
		pose = SpiderPose.GetIdlePose()
		# lift your legs and go forward
		pose.ModifyJigJagLeft( [ 0, 3, 7 ] )
		# move your other legs backward
		# pose.ModifyJigJagRight( [ 0, -6, 0 ] )
		return pose
	
	@staticmethod
	def GetForward2Pose():
		pose = SpiderPose.GetForward1Pose()
		# put your legs down and go forward
		pose.ModifyJigJagLeft( [ 0, 3, 0 ] )
		return pose
		
	@staticmethod
	def GetForward3Pose():
		pose = SpiderPose.GetForward2Pose()
		pose.ModifyJigJagLeft( [ 0, 0, -7 ] )
		return pose
	
	@staticmethod
	def GetForward4Pose():
		pose = SpiderPose.GetForward3Pose()
		pose.ModifyJigJagLeft( [ 0, -6, 0 ] )
		return pose
	
class JSpider:
	fl_leg = 0
	fr_leg = 0
	cl_leg = 0
	cr_leg = 0
	bl_leg = 0
	br_leg = 0
	
	legs = [ ]
	
	def __init__(this):
		this.fl_leg = JSpiderLeg(0, 2, 4, 300, 650, 200, 700, 100, 600, 
		90, 330, 80, 260, 190, 0, 
		False, False, True)
		this.fr_leg = JSpiderLeg(1, 3, 5, 122, 500, 100, 600, 100, 700, 
		210, 85, 265, 60, 20, 205, 
		False, True, False)
		this.cl_leg = JSpiderLeg(6, 8, 10, 300, 680, 200, 700, 130, 700, 
		65, 300, 80, 260, 200, 35, 
		False, False, True)
		this.cr_leg = JSpiderLeg(7, 9, 11, 100, 500, 100, 600, 110, 700, 
		240, 105, 260, 70, 40, 200,
		False, True, False)
		this.bl_leg = JSpiderLeg(12, 14, -1, 200, 700, 200, 700, 50, 250,
		50, 300, 80, 250, 190, 30, 
		False, False, True)
		this.br_leg = JSpiderLeg(13, 15, -4, 50, 500, 100, 700, 50, 250,
		240, 140, 280, 80, 30, 190,
		False, True, False)
		
		this.legs = [[this.fl_leg, this.fr_leg] , [this.cl_leg, this.cr_leg], [this.bl_leg, this.br_leg]]
	
	
	def getInfo(this):
		this.fl_leg.getInfo()
		this.fr_leg.getInfo()
		this.cl_leg.getInfo()
		this.cr_leg.getInfo()
		this.bl_leg.getInfo()
		this.br_leg.getInfo()
	
	def __getitem__(this, index):
		return this.legs[index];
		
	def stop(this):
		this.fl_leg[0].stop()
	
	def moveByPose(this, pose):
		this.fl_leg.moveByEndEffectorPosition(pose.fl)
		this.fr_leg.moveByEndEffectorPosition(pose.fr)
		this.cl_leg.moveByEndEffectorPosition(pose.cl)
		this.cr_leg.moveByEndEffectorPosition(pose.cr)
		this.bl_leg.moveByEndEffectorPosition(pose.bl)
		this.br_leg.moveByEndEffectorPosition(pose.br)
		
#Constants (servo PWM values). Servo positions:
#FRONT: 0=left base, 1=right base, 2=left mid, 3=right mid, 4=left tip, 5=right tip
#MIDDLE: 6=left base, 7=right base, 8=left mid, 9=right mid, 10=left tip, 11=right tip
#BACK: 12=left base, 13=right base, 14=left mid, 15=right mid, PIN1=left tip, PIN4=right tip

class CommandLineInterpreter:
	rowId = 0
	legId = 0
	jointId = 0
	spidy = 0
	
	def __init__(this, spider):
		this.spidy = spider

	def moveSpider(this, params):
		val = int(params[1])
		this.spidy[this.rowId][this.legId][this.jointId].move(val)

	def moveSpiderByRate(this, params):
		val = float(params[1])
		this.spidy[this.rowId][this.legId][this.jointId].moveByRate(val)

	def moveSpiderByAngle(this, params):
		val = float(params[1])
		this.spidy[this.rowId][this.legId][this.jointId].moveByAngle(val)
		
	def moveSpiderGraduallyByAngle(this, params):
		val1 = float(params[1])
		val2 = float(params[2])
		val3 = float(params[3])
		this.spidy[this.rowId][this.legId][this.jointId].graduallyMoveToAngle(val1, val2, val3)

	def moveSpiderLegTip(this, params):
		val1 = float(params[1])
		val2 = float(params[2])
		val3 = float(params[3])
		val = [val1, val2, val3]
		this.spidy[this.rowId][this.legId].moveByEndEffectorPosition(val)
	
	def moveByPose(this, params):
		val = params[1]
		this.spidy.moveByPose(SpiderPose.GetPoseByName(val))
	
	def getLegInfo(this):
		this.spidy[this.rowId][this.legId].getInfo()
	
	def getJointInfo(this):
		this.spidy[this.rowId][this.legId][this.jointId].getInfo()
	
	def getInfo(this):
		this.spidy.getInfo()
	
	def setLegId(this, params):
		val = int(params[1])
		this.legId = val
		
	def setJointId(this, params):
		val = int(params[1])
		this.jointId = val
		
	def setRowId(this, params):
		val = int(params[1])
		this.rowId = val
		
		
	def interpretCommand(this, cmd):
		params = cmd.split()
		option = params[0]
		if option == "move" or option == "m":
			this.moveSpider(params)
		elif option == "movef" or option == "mf":
			this.moveSpiderByRate(params)
		elif option == "movea" or option == "ma":
			this.moveSpiderByAngle(params)
		elif option == "moveag" or option == "mg":
			this.moveSpiderGraduallyByAngle(params)
		elif option == "movetip" or option == "mt":
			this.moveSpiderLegTip(params)
		elif option == "setpose" or option == "sp":
			this.moveByPose(params)
		elif option == "getleginfo" or option == "gli":
			this.getLegInfo()
		elif option == "getjointinfo" or option == "gji":
			this.getJointInfo()
		elif option == "getinfo" or option == "gi":
			this.getInfo()
		elif option == "setlegid" or option == "setleg" or option == "sl" or option == "leg":
			this.setLegId(params)
		elif option == "setjointid" or option == "setjoint" or option == "sj" or option == "joint":
			this.setJointId(params)
		elif option == "setrowid" or option == "setrow" or option == "sr" or option == "row":
			this.setRowId(params)
		else:
			print "Command " + option + " not found."
			
	def listen(this):
		while(True):
			this.interpretCommand(raw_input("Enter Command: "))

			
			

spidy = JSpider()
cmd = CommandLineInterpreter(spidy)

try:
	cmd.listen()
except KeyboardInterrupt:
	spidy.stop()
	call("echo 1=0 > /dev/servoblaster", shell=True)
	call("echo 2=0 > /dev/servoblaster", shell=True)
	call("echo 3=0 > /dev/servoblaster", shell=True)
	call("echo 4=0 > /dev/servoblaster", shell=True)
	pwm = PWM(0x40)
	pwm.setPWMFreq(60)

