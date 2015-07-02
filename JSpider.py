from Adafruit_PWM_Servo_Driver import PWM
from subprocess import call
import pygame
import time
import sys

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
		return abs(angleInDegreeTo - angleInDegreeFrom) if angleInDegreeTo > angleInDegreeFrom else abs((angleInDegreeTo + 360) - angleInDegreeTo)
	
	@staticmethod
	def getAngleDistanceInBackward(angleInDegreeFrom, angleInDegreeTo):
		return abs(angleInDegreeFrom - angleInDegreeTo) if angleInDegreeFrom > angleInDegreeTo else abs((angleInDegree + 360) - angleInDegreeTo)
	
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
		this.setCurrentPower(inputPower)
		if this.isPinPort(this.port):
			call("echo " + str(-this.port) + "=" + str(power) + ">/dev/servoblaster", shell=True)
		else:
			pwm.setPWM(this.port, 0, power)
	
	def setCurrentPower(this, inputPower):
		currentPower = inputPower
		currentRate = this.convertPowerToRate(currentPower)
		currentAngle = this.convertRateToAngle(currentRate)
	
	def convertRateToPower(this, rate):
		clampedRate = max(min(rate, 1), 0)
		return (int(this.minimumPower + this.minToMaxPowerVector * clampedRate))
	
	def convertPowerToRate(this, power):
		clampedRate = (this.minimumPower - power) / this.minToMaxPowerVector
		return clampedRate;
	
	def convertRateToAngle(this, rate):
		clampedAngle = rate * this.minToMaxAngleVector + this.minAngle
		return clampedAngle
	
	def convertAngleToRate(this, angleInDegree):
		clampedAngle = this.clampAngle(angleInDegree)
		rate = (clampedAngle - this.minAngle) / this.minToMaxAngleVector
		return rate
		
	def stop(this):
		if this.isPinPort(this.port):
			call("echo " + str(-this.port) + "=" + str(0) + ">/dev/servoblaster", shell=True)
		else:
			pwm.setPWM(this.port, 0, 0)
	
	def isPinPort(this, port):
		return port < 0
	
	def moveByRate(this, rate):
		this.move(this.convertRateToPower(rate))
	
	def moveByAngle(this, angleInDegree):
		rate = this.convertAngleToRate(angleInDegree)
		this.moveByRate(rate)
	
	def graduallyMoveToAngle(this, targetAngle, duration, subdivde = 5):
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
		
		currentRate = startRate
		# this is bad because it will block other operations.
		# should be async operation... or have general loop. 
		for x in range(0, subdivide):
			time.sleep(delayDuration)
			currentRate = currentRate + dividedRateVector
			moveByRate(currentRate)
		
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
		angleInDegree = Angle.sanctify(angleInDegree)
		if(this.isAngleInRange(angleInDegree) is False):
			forwardDistanceFromMinAngle = getAngleDistanceInForward(angleInDegree, this.minAngle)
			forwardDistanceFromMaxAngle = getAngleDistanceInForward(angleInDegree, this.maxAngle)
			backwardDistanceFromMinAngle = getAnlgeDistanceInBackward(angleInDegree, this.minAngle)
			backwardDistanceFromMaxAngle = getAngleDistanceInForward(angleInDegree, this.maxAngle)
			
			distanceFromMinAngle = min(forwardDistanceFromMinAngle, backwardDistanceFromMinAngle)
			distanceFromMaxAngle = max(forwardDistanceFromMaxAngle, backwardDistanceFromMaxAngle)
			
			return this.minAngle if distanceFromMinAngle < distanceFromMaxAngle else this.maxAngle
		else:
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
		
	
class JSpider:
	fl_leg = 0
	fr_leg = 0
	cl_leg = 0
	cr_leg = 0
	br_leg = 0
	bl_leg = 0
	
	legs = [ ]
	
	def __init__(this):
		this.fl_leg = JSpiderLeg(0, 2, 4, 400, 650, 300, 600, 200, 600, 
		50, 330, 40, 290, 220, 0, 
		False, False, True)
		this.fr_leg = JSpiderLeg(1, 3, 5, 150, 400, 200, 500, 200, 600, 
		205, 130, 285, 35, 10, 225, 
		False, True, False)
		this.cl_leg = JSpiderLeg(6, 8, 10, 400, 600, 300, 600, 200, 600, 
		30, 340, 40, 285, 225, 10, 
		False, False, True)
		this.cr_leg = JSpiderLeg(7, 9, 11, 200, 400, 200, 500, 200, 600, 
		190, 130, 295, 25, 15, 260,
		False, True, False)
		this.bl_leg = JSpiderLeg(12, 14, -1, 300, 600, 300, 600, 
		50, 290, 40, 300, 200, 40, 
		False, False, True)
		this.br_leg = JSpiderLeg(13, 15, -4, 150, 400, 200, 600, 
		215, 170, 350, 65, 40, 200,
		False, True, False)
		this.legs = [[this.fl_leg, this.fr_leg] , [this.cl_leg, this.cr_leg], [this.bl_leg, this.br_leg]]
		
	def __getitem__(this, index):
		return this.legs[index];
		
	def stop(this):
		this.fl_leg[0].stop()
		
		
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


