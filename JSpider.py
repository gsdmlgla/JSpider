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
		this.value = this.value % 360
		if(this.value < 0):
			this.value = 360 - this.value
		
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
	minimumToMaximumPowerVector = 0
	
	minimumAngle = 0
	maximumAngle = 0
	minimumToMaximumAngleVector = 0
	
	increaseToReach = False
	
	def __init__(this, port, minPower, maxPower, minMappedDegree = 0, maxMappedDegree = 0, doesIncreaseToReachMax = False):
		this.port = port
		this.minimumPower = minPower
		this.maximumPower = maxPower
		this.minimumAngle = Angle(minMappedDegree)
		this.maximumAngle = Angle(maxMappedDegree)
		this.minimumToMaximumPowerVector = maxPower - minPower
		if(doesIncreaseToReachMax):
			if(this.maximumAngle.getAngle()
			this.minimumToMaximumAngleVector = this.maximumAngle.getAngle() - this.minimumAngle.getAngle()
		this.increaseToReach = doesIncreaseToReachMax
	
	def move(this, inputPower):
		power = min(max(inputPower, this.minimumPower), this.maximumPower)
		if this.isPinPort(this.port):
			call("echo " + str(-this.port) + "=" + str(power) + ">/dev/servoblaster", shell=True)
		else:
			pwm.setPWM(this.port, 0, power)
	
	def stop(this):
		if this.isPinPort(this.port):
			call("echo " + str(-this.port) + "=" + str(0) + ">/dev/servoblaster", shell=True)
		else:
			pwm.setPWM(this.port, 0, 0)
	
	def isPinPort(this, port):
		return port < 0;
	
	def moveByRate(this, rate):
		clampedRate = max(min(rate, 1), 0)
		this.move(int(this.minimumPower + this.minimumToMaximumPowerVector * clampedRate))
	

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


