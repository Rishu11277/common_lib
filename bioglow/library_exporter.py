import sys, os

libraryFile = 'Rockstar_lib.py'

libCode: str = """
# version date: 10/21/26
from hub import light_matrix, motion_sensor, port
import runloop, motor, motor_pair, time, color_sensor, color

class RW:
    MOTOR_MAX_VELOCITIES = {"SMALL": 660, "MEDIUM": 1110, "LARGE": 1050}
    WHEEL_MAX_VELOCITY = MOTOR_MAX_VELOCITIES["MEDIUM"]
    LIGHT_REFLECTIONS = {"BLACK": 25, "WHITE": 95}
    BLACK_LINE_RIGHT_EDGE = "Right"
    BLACK_LINE_LEFT_EDGE = "Left"

    YAW_SCALE = -0.1
    YAW_RESET_DELAY = 0.1
    DEGREES_PER_ROTATION = 360
    END_SPEED_PERCENTAGE = 0.1
    INTEGRAL_LIMIT = 100
    LOOP_DELAY_MS = 10
    MAX_VELOCITY_PERCENTAGE = 100
    MAX_TURN_DEGREES = 179

    TURN_TYPES = ("PIVOT", "SPIN", "CAR")
    PROPORTIONAL_TURN_TYPES = ("PIVOT", "SPIN")
    CAR_TURN_WHEEL_RATIOS = {"OUTER": 0.75, "INNER": 0.25}
    PROPORTIONAL_TURN = {
        "PIVOT": {"MIN": 0.15, "MAX": 0.40, "DIVISOR": 40, "VELOCITY": 40},
        "SPIN":  {"MIN": 0.10, "MAX": 0.35, "DIVISOR": 60, "VELOCITY": 25},
    }

    DEFAULTS = {
        "ARC_VELOCITY": 20,
        "TURN_TIMEOUT": 2.0,
        "LINE_VELOCITY": 25,
        "SQUARE_UP_LINE_VELOCITY": 15,
        "WALL_SECONDS": 1.0,
        "WALL_VELOCITY": 100,
        "WALL_ACCELERATION": 1000,
        "WALL_DECELERATION": 1000,
        "PID_P": 0.15,
        "PID_I": 0.0,
        "PID_D": 0.0,
        "PID_VELOCITY": 10,
    }

    PORT_NAMES = "ABCDEF"
    LINE_COLOR_NAMES = {color.BLACK: "Black", color.WHITE: "White"}

    def __init__(self, robot="Misty", leftMotorPort=port.A, rightMotorPort=port.B, leftSensorPort=port.E, rightSensorPort=port.F,
                 wheelBaseInCentimeters=8.8, acceleration=500, deceleration=1000, brakeStartPercentage=0.9, correctionMultiplier=-3.5, debug=True):
        self.ROBOT_NAME = robot
        self.PORTS = {"LEFT_MOTOR": leftMotorPort, "RIGHT_MOTOR": rightMotorPort, "LEFT_SENSOR": leftSensorPort, "RIGHT_SENSOR": rightSensorPort}
        self.WHEEL_BASE_IN_CENTIMETERS = wheelBaseInCentimeters
        self.ACCELERATION = acceleration
        self.DECELERATION = deceleration
        self.BRAKE_START_PERCENTAGE = brakeStartPercentage
        self.CORRECTION_MULTIPLIER = correctionMultiplier
        self.DEBUG = debug
        self.__startTime = time.ticks_ms()

    def __format(self, value):
        if isinstance(value, float):
            return "{:.1f}".format(value)
        return str(value)

    def __portName(self, portNumber):
        if 0 <= portNumber < len(self.PORT_NAMES):
            return "Port " + self.PORT_NAMES[portNumber]
        return str(portNumber)

    def __colorName(self, lineColor):
        return self.LINE_COLOR_NAMES.get(lineColor, "Invalid (" + str(lineColor) + ")")

    def __printPairs(self, pairs):
        for i in range(0, len(pairs) - 1, 2):
            print("[" + str(pairs[i]) + "] " + self.__format(pairs[i + 1]))

    def __logStart(self, functionName, *pairs):
        self.__startTime = time.ticks_ms()
        if not self.DEBUG:
            return
        print("[" + self.ROBOT_NAME + "] " + functionName)
        self.__printPairs(pairs)

    def __logResult(self, *pairs):
        if not self.DEBUG:
            return
        self.__printPairs(pairs)
        print("[Time] " + "{:.2f}".format(time.ticks_diff(time.ticks_ms(), self.__startTime) / 1000))
        print("")

    def __logError(self, message):
        print("[Error] " + message)

    def __isNumber(self, value) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def __inputsValid(self, *checks) -> bool:
        valid = True
        for passed, message in checks:
            if not passed:
                self.__logError(message)
                valid = False
        return valid

    def __velocityCheck(self, velocityPercentage, allowNegative):
        maximum = self.MAX_VELOCITY_PERCENTAGE
        if allowNegative:
            passed = self.__isNumber(velocityPercentage) and 0 < abs(velocityPercentage) <= maximum
            message = "Velocity must be -" + str(maximum) + " to " + str(maximum) + " and not 0, got " + str(velocityPercentage)
        else:
            passed = self.__isNumber(velocityPercentage) and 0 < velocityPercentage <= maximum
            message = "Velocity must be 1 to " + str(maximum) + ", got " + str(velocityPercentage)
        return (passed, message)

    def __degreesCheck(self, degrees):
        passed = self.__isNumber(degrees) and 0 < abs(degrees) <= self.MAX_TURN_DEGREES
        return (passed, "Degrees must be -" + str(self.MAX_TURN_DEGREES) + " to " + str(self.MAX_TURN_DEGREES) + " and not 0, got " + str(degrees))

    def __rotationsCheck(self, rotations):
        return (self.__isNumber(rotations) and rotations != 0, "Rotations must be a number and not 0, got " + str(rotations))

    def __turnTypeCheck(self, turnType, allowedTypes):
        return (turnType in allowedTypes, "Turn type must be " + " or ".join(allowedTypes) + ", got " + str(turnType))

    def __lineColorCheck(self, lineColor):
        return (self.__validLineColor(lineColor), "Line color must be color.BLACK or color.WHITE")

    def __percentageToUnits(self, percentage):
        return self.WHEEL_MAX_VELOCITY * percentage/100

    def __yaw(self):
        return motion_sensor.tilt_angles()[0] * self.YAW_SCALE

    async def __resetYaw(self):
        motion_sensor.reset_yaw(0)
        await runloop.sleep_ms(int(self.YAW_RESET_DELAY * 1000))

    def __turnCompleted(self, degrees) -> bool:
        return abs(self.__yaw()) >= abs(degrees)

    def __onLine(self, sensorPort, lineColor) -> bool:
        if lineColor == color.BLACK:
            return color_sensor.reflection(sensorPort) < self.LIGHT_REFLECTIONS["BLACK"]
        return color_sensor.reflection(sensorPort) > self.LIGHT_REFLECTIONS["WHITE"]

    def __lineFound(self, leftPort, rightPort, lineColor, bothSensorsOnLine) -> bool:
        if bothSensorsOnLine:
            return self.__onLine(leftPort, lineColor) and self.__onLine(rightPort, lineColor)
        return self.__onLine(leftPort, lineColor) or self.__onLine(rightPort, lineColor)

    def __validLineColor(self, lineColor) -> bool:
        return lineColor == color.BLACK or lineColor == color.WHITE

    def __sensorReadings(self, leftPort, rightPort):
        return ("Left Sensor Reflection", color_sensor.reflection(leftPort), "Right Sensor Reflection", color_sensor.reflection(rightPort))

    async def turn(self, degrees, velocityPercentage, turnType) -> None:
        self.__logStart("Turn", "Type", turnType, "Degrees", degrees, "Velocity", velocityPercentage)
        if not self.__inputsValid(self.__turnTypeCheck(turnType, self.TURN_TYPES), self.__degreesCheck(degrees), self.__velocityCheck(velocityPercentage, False)):
            self.__logResult()
            return
        velocity = int(self.__percentageToUnits(velocityPercentage))

        await self.__resetYaw()
        if turnType == "SPIN":
            if degrees > 0:
                motor_pair.move_tank(motor_pair.PAIR_1, velocity, -1 * velocity)
            else:
                motor_pair.move_tank(motor_pair.PAIR_1, -1 * velocity, velocity)
        elif turnType == "PIVOT":
            if degrees > 0:
                motor_pair.move_tank(motor_pair.PAIR_1, velocity, 0)
            else:
                motor_pair.move_tank(motor_pair.PAIR_1, 0, velocity)
        else:
            outerVelocity = int(velocity * self.CAR_TURN_WHEEL_RATIOS["OUTER"])
            innerVelocity = int(velocity * self.CAR_TURN_WHEEL_RATIOS["INNER"])
            if degrees > 0:
                motor_pair.move_tank(motor_pair.PAIR_1, outerVelocity, innerVelocity)
            else:
                motor_pair.move_tank(motor_pair.PAIR_1, innerVelocity, outerVelocity)

        await runloop.until(lambda: self.__turnCompleted(degrees))
        motor_pair.stop(motor_pair.PAIR_1)
        self.__logResult("Actual Degrees Turned", self.__yaw())

    async def arcTurn(self, radiusInCm, degrees, velocityPercentage=None) -> None:
        if velocityPercentage is None:
            velocityPercentage = self.DEFAULTS["ARC_VELOCITY"]
        self.__logStart("Arc Turn", "Radius", radiusInCm, "Degrees", degrees, "Velocity", velocityPercentage)
        if not self.__inputsValid((self.__isNumber(radiusInCm) and radiusInCm >= 0, "Radius must be 0 or more, got " + str(radiusInCm)),
                                  self.__degreesCheck(degrees), self.__velocityCheck(velocityPercentage, True)):
            self.__logResult()
            return

        velocity = self.__percentageToUnits(velocityPercentage)
        halfWheelBase = self.WHEEL_BASE_IN_CENTIMETERS / 2.0
        wheelRadiusRatio = (radiusInCm - halfWheelBase) / (radiusInCm + halfWheelBase)

        steering = int((1 - wheelRadiusRatio) * 50)
        if degrees < 0:
            steering = -steering

        await self.__resetYaw()
        motor_pair.move(motor_pair.PAIR_1, steering, velocity=int(velocity))
        await runloop.until(lambda: self.__turnCompleted(degrees))
        motor_pair.stop(motor_pair.PAIR_1)
        self.__logResult("Steering", steering, "Actual Degrees Turned", self.__yaw())

    async def proportionalTurn(self, degrees, turnType, velocityPercentage=None, timeout=None) -> None:
        if timeout is None:
            timeout = self.DEFAULTS["TURN_TIMEOUT"]
        if velocityPercentage is None and turnType in self.PROPORTIONAL_TURN_TYPES:
            velocityPercentage = self.PROPORTIONAL_TURN[turnType]["VELOCITY"]
        self.__logStart("Proportional Turn", "Type", turnType, "Degrees", degrees, "Velocity", velocityPercentage, "Timeout", timeout)
        if not self.__inputsValid(self.__turnTypeCheck(turnType, self.PROPORTIONAL_TURN_TYPES), self.__degreesCheck(degrees), self.__velocityCheck(velocityPercentage, False),
                                  (self.__isNumber(timeout) and timeout > 0, "Timeout must be more than 0, got " + str(timeout))):
            self.__logResult()
            return
        settings = self.PROPORTIONAL_TURN[turnType]

        await self.__resetYaw()
        minTurnPower = self.WHEEL_MAX_VELOCITY * settings["MIN"]
        maxTurnPower = self.WHEEL_MAX_VELOCITY * settings["MAX"]
        startTime = time.ticks_ms()
        result = "Timed Out"

        while time.ticks_diff(time.ticks_ms(), startTime) < timeout * 1000:
            if degrees > 0:
                turnError = degrees - self.__yaw()
            else:
                turnError = self.__yaw() - degrees

            turnPower = turnError * velocityPercentage/100 * self.WHEEL_MAX_VELOCITY/settings["DIVISOR"]

            turnPower = max(minTurnPower, min(maxTurnPower, turnPower))
            power = int(turnPower)

            if turnType == "PIVOT":
                if degrees > 0:
                    motor_pair.move_tank(motor_pair.PAIR_1, power, 0)
                else:
                    motor_pair.move_tank(motor_pair.PAIR_1, 0, power)
            else:
                if degrees > 0:
                    motor_pair.move_tank(motor_pair.PAIR_1, power, -1 * power)
                else:
                    motor_pair.move_tank(motor_pair.PAIR_1, -1 * power, power)

            if self.__turnCompleted(degrees):
                result = "Completed"
                break

            await runloop.sleep_ms(self.LOOP_DELAY_MS)

        motor_pair.stop(motor_pair.PAIR_1)
        self.__logResult("Result", result, "Actual Degrees Turned", self.__yaw())

    async def moveForward(self, rotations, velocityPercentage, acceleration=None, deceleration=None) -> None:
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        deceleration = self.DECELERATION if deceleration is None else deceleration
        self.__logStart("Move Forward", "Rotations", rotations, "Velocity", velocityPercentage, "Acceleration", acceleration, "Deceleration", deceleration)
        if not self.__inputsValid(self.__rotationsCheck(rotations), self.__velocityCheck(velocityPercentage, False)):
            self.__logResult()
            return

        motor.reset_relative_position(self.PORTS["RIGHT_MOTOR"], 0)
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, int(rotations * self.DEGREES_PER_ROTATION), 0,
                                          velocity=int(self.__percentageToUnits(velocityPercentage)), stop=motor.BRAKE,
                                          acceleration=acceleration, deceleration=deceleration)
        self.__logResult("Actual Rotations Traveled", motor.relative_position(self.PORTS["RIGHT_MOTOR"]) / self.DEGREES_PER_ROTATION)

    async def moveStraightGyro(self, rotations, velocityPercentage, acceleration=None, brakeStartPercentage=None, correctionMultiplier=None) -> None:
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        brakeStartPercentage = self.BRAKE_START_PERCENTAGE if brakeStartPercentage is None else brakeStartPercentage
        correctionMultiplier = self.CORRECTION_MULTIPLIER if correctionMultiplier is None else correctionMultiplier
        self.__logStart("Move Straight (Gyro)", "Rotations", rotations, "Velocity", velocityPercentage, "Acceleration", acceleration,
                        "Brake Start", brakeStartPercentage * 100, "Correction Multiplier", correctionMultiplier)
        if not self.__inputsValid(self.__rotationsCheck(rotations), self.__velocityCheck(velocityPercentage, True),
                                  (self.__isNumber(brakeStartPercentage) and 0 <= brakeStartPercentage <= 1, "Brake start must be 0 to 1, got " + str(brakeStartPercentage)),
                                  (self.__isNumber(correctionMultiplier) and correctionMultiplier < 0, "Correction multiplier must be negative, got " + str(correctionMultiplier))):
            self.__logResult()
            return

        await self.__resetYaw()

        direction = 1 if rotations > 0 else -1
        velocity = int(self.__percentageToUnits(abs(velocityPercentage)) * direction)
        rightPort = self.PORTS["RIGHT_MOTOR"]
        degrees = rotations * self.DEGREES_PER_ROTATION
        motor.reset_relative_position(rightPort, 0)
        brakeStartDistance = degrees * brakeStartPercentage
        endSpeed = self.WHEEL_MAX_VELOCITY * self.END_SPEED_PERCENTAGE

        while direction * motor.relative_position(rightPort) < direction * degrees:
            correction = int(self.__yaw() * correctionMultiplier)
            deceleration = 0
            degreesTraveled = motor.relative_position(rightPort)
            if direction * degreesTraveled > direction * brakeStartDistance:
                deceleration = direction * min(abs(velocity) * degreesTraveled/degrees, abs(velocity) - endSpeed)
            motor_pair.move_tank(motor_pair.PAIR_1, velocity + correction - int(deceleration), velocity - correction - int(deceleration), acceleration=acceleration)
            await runloop.sleep_ms(self.LOOP_DELAY_MS)

        motor_pair.stop(motor_pair.PAIR_1)
        self.__logResult("Actual Rotations Traveled", motor.relative_position(rightPort) / self.DEGREES_PER_ROTATION, "Ending Drift", self.__yaw())

    async def squareUpOnWall(self, seconds=None, velocityPercentage=None, acceleration=None, deceleration=None) -> None:
        seconds = self.DEFAULTS["WALL_SECONDS"] if seconds is None else seconds
        velocityPercentage = self.DEFAULTS["WALL_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.DEFAULTS["WALL_ACCELERATION"] if acceleration is None else acceleration
        deceleration = self.DEFAULTS["WALL_DECELERATION"] if deceleration is None else deceleration
        self.__logStart("Square Up On Wall", "Seconds", seconds, "Velocity", velocityPercentage, "Acceleration", acceleration, "Deceleration", deceleration)
        if not self.__inputsValid((self.__isNumber(seconds) and seconds > 0, "Seconds must be more than 0, got " + str(seconds)),
                                  self.__velocityCheck(velocityPercentage, True)):
            self.__logResult()
            return

        startTime = time.ticks_ms()
        await motor_pair.move_for_time(motor_pair.PAIR_1, int(seconds * 1000), 0, velocity=int(self.__percentageToUnits(velocityPercentage)),
                                       stop=motor.BRAKE, acceleration=acceleration, deceleration=deceleration)
        self.__logResult("Actual Seconds", time.ticks_diff(time.ticks_ms(), startTime) / 1000)

    async def moveStraightUntilLine(self, lineColor, bothSensorsOnLine=False, velocityPercentage=None, acceleration=None) -> int:
        leftPort, rightPort = self.PORTS["LEFT_SENSOR"], self.PORTS["RIGHT_SENSOR"]
        velocityPercentage = self.DEFAULTS["LINE_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        self.__logStart("Move Straight Until Line", "Line Color", self.__colorName(lineColor), "Wait For Both Sensors", bothSensorsOnLine,
                        "Left Sensor", self.__portName(leftPort), "Right Sensor", self.__portName(rightPort),
                        "Velocity", velocityPercentage, "Acceleration", acceleration)

        if not self.__inputsValid(self.__lineColorCheck(lineColor), self.__velocityCheck(velocityPercentage, True)):
            self.__logResult()
            return -1

        motor_pair.move(motor_pair.PAIR_1, 0, velocity=int(self.__percentageToUnits(velocityPercentage)), acceleration=acceleration)
        await runloop.until(lambda: self.__lineFound(leftPort, rightPort, lineColor, bothSensorsOnLine))
        triggeredSensorPort = leftPort if self.__onLine(leftPort, lineColor) else rightPort

        motor_pair.stop(motor_pair.PAIR_1)
        self.__logResult("Triggered Sensor", self.__portName(triggeredSensorPort), *self.__sensorReadings(leftPort, rightPort))
        return triggeredSensorPort

    async def moveStraightUntilLineGyro(self, lineColor, bothSensorsOnLine=False, velocityPercentage=None, acceleration=None, correctionMultiplier=None) -> int:
        leftPort, rightPort = self.PORTS["LEFT_SENSOR"], self.PORTS["RIGHT_SENSOR"]
        velocityPercentage = self.DEFAULTS["LINE_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        correctionMultiplier = self.CORRECTION_MULTIPLIER if correctionMultiplier is None else correctionMultiplier
        self.__logStart("Move Straight Until Line (Gyro)", "Line Color", self.__colorName(lineColor), "Wait For Both Sensors", bothSensorsOnLine,
                        "Left Sensor", self.__portName(leftPort), "Right Sensor", self.__portName(rightPort),
                        "Velocity", velocityPercentage, "Acceleration", acceleration, "Correction Multiplier", correctionMultiplier)
        if not self.__inputsValid(self.__lineColorCheck(lineColor), self.__velocityCheck(velocityPercentage, True),
                                  (self.__isNumber(correctionMultiplier) and correctionMultiplier < 0, "Correction multiplier must be negative, got " + str(correctionMultiplier))):
            self.__logResult()
            return -1

        await self.__resetYaw()
        motorPort = self.PORTS["RIGHT_MOTOR"]
        motor.reset_relative_position(motorPort, 0)
        velocity = int(self.__percentageToUnits(velocityPercentage))

        while not self.__lineFound(leftPort, rightPort, lineColor, bothSensorsOnLine):
            correction = int(self.__yaw() * correctionMultiplier)
            motor_pair.move_tank(motor_pair.PAIR_1, velocity + correction, velocity - correction, acceleration=acceleration)
            await runloop.sleep_ms(self.LOOP_DELAY_MS)

        motor_pair.stop(motor_pair.PAIR_1)
        triggeredSensorPort = leftPort if self.__onLine(leftPort, lineColor) else rightPort
        results = (("Triggered Sensor", self.__portName(triggeredSensorPort)) + self.__sensorReadings(leftPort, rightPort) +
                   ("Actual Rotations Traveled", motor.relative_position(motorPort) / self.DEGREES_PER_ROTATION, "Ending Drift", self.__yaw()))
        self.__logResult(*results)
        return triggeredSensorPort

    async def squareUpOnLine(self, lineColor, velocityPercentage=None, acceleration=None) -> None:
        leftPort, rightPort = self.PORTS["LEFT_SENSOR"], self.PORTS["RIGHT_SENSOR"]
        velocityPercentage = self.DEFAULTS["SQUARE_UP_LINE_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        self.__logStart("Square Up On Line", "Line Color", self.__colorName(lineColor), "Left Sensor", self.__portName(leftPort),
                        "Right Sensor", self.__portName(rightPort), "Velocity", velocityPercentage, "Acceleration", acceleration)

        if not self.__inputsValid(self.__lineColorCheck(lineColor), self.__velocityCheck(velocityPercentage, True)):
            self.__logResult()
            return

        velocity = self.__percentageToUnits(velocityPercentage)
        motor.run(self.PORTS["LEFT_MOTOR"], int(-velocity), acceleration=acceleration)
        motor.run(self.PORTS["RIGHT_MOTOR"], int(velocity), acceleration=acceleration)

        leftSensorFoundLine = False
        rightSensorFoundLine = False

        while not leftSensorFoundLine or not rightSensorFoundLine:
            if self.__onLine(leftPort, lineColor):
                motor.stop(self.PORTS["LEFT_MOTOR"])
                leftSensorFoundLine = True
            if self.__onLine(rightPort, lineColor):
                motor.stop(self.PORTS["RIGHT_MOTOR"])
                rightSensorFoundLine = True
            await runloop.sleep_ms(self.LOOP_DELAY_MS)

        self.__logResult(*self.__sensorReadings(leftPort, rightPort))

    async def pidBlackLineFollow(self, rotations, sensorPort, midPointReflectionPercentage, edgeToFollow, proportionalCoef=None, integralCoef=None, derivativeCoef=None, velocityPercentage=None, acceleration=None) -> None:
        proportionalCoef = self.DEFAULTS["PID_P"] if proportionalCoef is None else proportionalCoef
        integralCoef = self.DEFAULTS["PID_I"] if integralCoef is None else integralCoef
        derivativeCoef = self.DEFAULTS["PID_D"] if derivativeCoef is None else derivativeCoef
        velocityPercentage = self.DEFAULTS["PID_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        self.__logStart("PID Black Line Follow", "Rotations", rotations, "Sensor", self.__portName(sensorPort), "Midpoint Reflection", midPointReflectionPercentage,
                        "Edge", edgeToFollow, "P", proportionalCoef, "I", integralCoef, "D", derivativeCoef,
                        "Velocity", velocityPercentage, "Acceleration", acceleration)
        if not self.__inputsValid(self.__rotationsCheck(rotations), self.__velocityCheck(velocityPercentage, False),
                                  (self.__isNumber(midPointReflectionPercentage) and 0 <= midPointReflectionPercentage <= 100, "Midpoint reflection must be 0 to 100, got " + str(midPointReflectionPercentage)),
                                  (edgeToFollow in (self.BLACK_LINE_LEFT_EDGE, self.BLACK_LINE_RIGHT_EDGE), "Edge must be RW.BLACK_LINE_LEFT_EDGE or RW.BLACK_LINE_RIGHT_EDGE, got " + str(edgeToFollow))):
            self.__logResult()
            return

        rightPort = self.PORTS["RIGHT_MOTOR"]
        velocity = self.__percentageToUnits(velocityPercentage)
        degreesToMove = rotations * self.DEGREES_PER_ROTATION
        motor.reset_relative_position(rightPort, 0)

        lastError = 0.0
        integral = 0.0

        while abs(motor.relative_position(rightPort)) < abs(degreesToMove):
            error = midPointReflectionPercentage - color_sensor.reflection(sensorPort)
            integral = max(-self.INTEGRAL_LIMIT, min(self.INTEGRAL_LIMIT, integral + error))
            derivative = error - lastError
            lastError = error

            turnCorrectionPercentage = proportionalCoef * error + integralCoef * integral + derivativeCoef * derivative
            turnCorrectionAmount = self.__percentageToUnits(turnCorrectionPercentage)

            if edgeToFollow == self.BLACK_LINE_RIGHT_EDGE:
                motor_pair.move_tank(motor_pair.PAIR_1, int(velocity + turnCorrectionAmount), int(velocity - turnCorrectionAmount), acceleration=acceleration)
            else:
                motor_pair.move_tank(motor_pair.PAIR_1, int(velocity - turnCorrectionAmount), int(velocity + turnCorrectionAmount), acceleration=acceleration)
            await runloop.sleep_ms(self.LOOP_DELAY_MS)

        motor_pair.stop(motor_pair.PAIR_1)
        self.__logResult("Actual Rotations Traveled", motor.relative_position(rightPort) / self.DEGREES_PER_ROTATION,
                         "Final Sensor Reflection", color_sensor.reflection(sensorPort))"""

def exportLibrary():
    global libCode
    global libraryFile

    deleteLibrary()

    libFile = open(libraryFile, 'w+')
    libFile.write(libCode)
    libFile.close()
    print("Export of library complete.")

#TODO: add error handling for file open/close issues
def readLibrary():
    libFile = open(libraryFile, 'r')
    contents = libFile.read()
    print(contents)
    libFile.close()

    print("\n\n")

def deleteLibrary():
    try:
        os.remove(libraryFile) #remove any existing custom library with the same name
    except:
        print("No current library to delete")
        pass


def readDirectory():
    print("Directory contents: ")
    dirContents = os.listdir('/flash')
    print(dirContents)


os.chdir('/flash') #change directory to root
readDirectory()
deleteLibrary()
readDirectory()
exportLibrary()
#readLibrary()
readDirectory()
sys.exit(0)

