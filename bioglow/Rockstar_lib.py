from hub import light_matrix, motion_sensor, port
import runloop, motor, motor_pair, time, color_sensor, color

class RW:
    MOTOR_MAX_VELOCITIES = {"SMALL": 660, "MEDIUM": 1110, "LARGE": 1050}
    WHEEL_MAX_VELOCITY = MOTOR_MAX_VELOCITIES["MEDIUM"]
    LIGHT_REFLECTIONS = {"BLACK": 25, "WHITE": 95}
    BLACK_LINE_RIGHT_EDGE = "Right"
    BLACK_LINE_LEFT_EDGE = "Left"
    RANDOM = [(523, 60), (659, 60), (784, 60), (1047, 60), (1319, 60), (1568, 250)]
    RANDOM_2 = 100

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
        "GENERAL_VELOCITY": 40,
        "TURN_TYPE": TURN_TYPES[0],
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

    def __format(self, value):
        if isinstance(value, float):
            return str(round(value, 2))
        return str(value)

    def __portName(self, portNumber):
        if 0 <= portNumber < len(self.PORT_NAMES):
            return "Port " + self.PORT_NAMES[portNumber]
        return str(portNumber)

    def __colorName(self, lineColor):
        return self.LINE_COLOR_NAMES.get(lineColor, "Invalid (" + str(lineColor) + ")")

    def __printResults(self, functionName, inputs, results, startTime):
        if not self.DEBUG:
            return
        print("[" + self.ROBOT_NAME + "] " + functionName)
        for name, value in inputs + results:
            print("[" + name + "] " + self.__format(value))
        print("[Time] " + "{:.2f}".format(time.ticks_diff(time.ticks_ms(), startTime) / 1000))
        print("")

    def __printErrors(self, functionName, inputs, errors, startTime):
        print("[" + self.ROBOT_NAME + "] " + functionName)
        for name, value in inputs:
            print("[" + name + "] " + self.__format(value))
        for message in errors:
            print("[Error] " + message)
        print("[Time] " + "{:.2f}".format(time.ticks_diff(time.ticks_ms(), startTime) / 1000))
        print("")

    def __isNumber(self, value) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def __findErrors(self, *checks):
        return [message for message in checks if message]

    def __checkRange(self, name, value, low=None, high=None):
        if not self.__isNumber(value):
            return name + " must be a number, got " + str(value)
        if (low is not None and value < low) or (high is not None and value > high):
            if high is None:
                return name + " must be " + str(low) + " or more, got " + str(value)
            if low is None:
                return name + " must be " + str(high) + " or less, got " + str(value)
            return name + " must be " + str(low) + " to " + str(high) + ", got " + str(value)

    def __checkAbove(self, name, value, minimum):
        if not self.__isNumber(value) or value <= minimum:
            return name + " must be more than " + str(minimum) + ", got " + str(value)

    def __checkBelow(self, name, value, maximum):
        if not self.__isNumber(value) or value >= maximum:
            return name + " must be less than " + str(maximum) + ", got " + str(value)

    def __checkNotZero(self, name, value, maximum=None):
        if not self.__isNumber(value) or value == 0 or (maximum is not None and abs(value) > maximum):
            limit = "a number" if maximum is None else "-" + str(maximum) + " to " + str(maximum)
            return name + " must be " + limit + " and not 0, got " + str(value)

    def __checkOneOf(self, name, value, allowed):
        if value not in allowed:
            names = list(allowed.values()) if isinstance(allowed, dict) else list(allowed)
            return name + " must be " + " or ".join(str(n) for n in names) + ", got " + str(value)

    def __checkVelocity(self, velocityPercentage, allowNegative=False):
        if allowNegative:
            return self.__checkNotZero("Velocity", velocityPercentage, self.MAX_VELOCITY_PERCENTAGE)
        return self.__checkRange("Velocity", velocityPercentage, 1, self.MAX_VELOCITY_PERCENTAGE)

    def __checkDegrees(self, degrees):
        return self.__checkNotZero("Degrees", degrees, self.MAX_TURN_DEGREES)

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

    def __sensorReadings(self, leftPort, rightPort):
        return [("Left Sensor Reflection", color_sensor.reflection(leftPort)), ("Right Sensor Reflection", color_sensor.reflection(rightPort))]

    async def turn(self, degrees, velocityPercentage=None, turnType=None) -> None:
        turnType = self.DEFAULTS["TURN_TYPE"] if turnType is None else turnType
        if velocityPercentage is None:
            velocityPercentage = self.DEFAULTS["GENERAL_VELOCITY"]
        callStartTime = time.ticks_ms()
        inputs = [("Type", turnType), ("Degrees", degrees), ("Velocity", velocityPercentage)]
        errors = self.__findErrors(
            self.__checkOneOf("Turn type", turnType, self.TURN_TYPES),
            self.__checkDegrees(degrees),
            self.__checkVelocity(velocityPercentage),
        )
        if errors:
            self.__printErrors("Turn", inputs, errors, callStartTime)
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
        self.__printResults("Turn", inputs, [("Actual Degrees Turned", self.__yaw())], callStartTime)

    async def arcTurn(self, radiusInCm, degrees, velocityPercentage=None) -> None:
        if velocityPercentage is None:
            velocityPercentage = self.DEFAULTS["ARC_VELOCITY"]
        callStartTime = time.ticks_ms()
        inputs = [("Radius", radiusInCm), ("Degrees", degrees), ("Velocity", velocityPercentage)]
        errors = self.__findErrors(
            self.__checkRange("Radius", radiusInCm, low=0),
            self.__checkDegrees(degrees),
            self.__checkVelocity(velocityPercentage, allowNegative=True),
        )
        if errors:
            self.__printErrors("Arc Turn", inputs, errors, callStartTime)
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
        self.__printResults("Arc Turn", inputs, [("Steering", steering), ("Actual Degrees Turned", self.__yaw())], callStartTime)

    async def proportionalTurn(self, degrees, turnType=None, velocityPercentage=None, timeout=None) -> None:
        turnType = self.DEFAULTS["TURN_TYPE"] if turnType is None else turnType
        if timeout is None:
            timeout = self.DEFAULTS["TURN_TIMEOUT"]
        if velocityPercentage is None and turnType in self.PROPORTIONAL_TURN_TYPES:
            velocityPercentage = self.PROPORTIONAL_TURN[turnType]["VELOCITY"]
        callStartTime = time.ticks_ms()
        inputs = [
            ("Type", turnType),
            ("Degrees", degrees),
            ("Velocity", velocityPercentage),
            ("Timeout", timeout),
        ]
        errors = self.__findErrors(
            self.__checkOneOf("Turn type", turnType, self.PROPORTIONAL_TURN_TYPES),
            self.__checkDegrees(degrees),
            self.__checkVelocity(velocityPercentage),
            self.__checkAbove("Timeout", timeout, 0),
        )
        if errors:
            self.__printErrors("Proportional Turn", inputs, errors, callStartTime)
            return
        settings = self.PROPORTIONAL_TURN[turnType]

        await self.__resetYaw()
        minTurnPower = self.WHEEL_MAX_VELOCITY * settings["MIN"]
        maxTurnPower = self.WHEEL_MAX_VELOCITY * settings["MAX"]
        turnStartTime = time.ticks_ms()
        result = "Timed Out"

        while time.ticks_diff(time.ticks_ms(), turnStartTime) < timeout * 1000:
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
        self.__printResults("Proportional Turn", inputs, [("Result", result), ("Actual Degrees Turned", self.__yaw())], callStartTime)

    async def moveForward(self, rotations, velocityPercentage=None, acceleration=None, deceleration=None) -> None:
        velocityPercentage = self.DEFAULTS["GENERAL_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        deceleration = self.DECELERATION if deceleration is None else deceleration
        callStartTime = time.ticks_ms()
        inputs = [
            ("Rotations", rotations),
            ("Velocity", velocityPercentage),
            ("Acceleration", acceleration),
            ("Deceleration", deceleration),
        ]
        errors = self.__findErrors(
            self.__checkNotZero("Rotations", rotations),
            self.__checkVelocity(velocityPercentage),
        )
        if errors:
            self.__printErrors("Move Forward", inputs, errors, callStartTime)
            return

        motor.reset_relative_position(self.PORTS["RIGHT_MOTOR"], 0)
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, int(rotations * self.DEGREES_PER_ROTATION), 0,
                                          velocity=int(self.__percentageToUnits(velocityPercentage)), stop=motor.BRAKE,
                                          acceleration=acceleration, deceleration=deceleration)
        self.__printResults("Move Forward", inputs, [("Actual Rotations Traveled", motor.relative_position(self.PORTS["RIGHT_MOTOR"]) / self.DEGREES_PER_ROTATION)], callStartTime)

    async def moveStraightGyro(self, rotations, velocityPercentage=None, acceleration=None, brakeStartPercentage=None, correctionMultiplier=None) -> None:
        velocityPercentage = self.DEFAULTS["GENERAL_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        brakeStartPercentage = self.BRAKE_START_PERCENTAGE if brakeStartPercentage is None else brakeStartPercentage
        correctionMultiplier = self.CORRECTION_MULTIPLIER if correctionMultiplier is None else correctionMultiplier
        callStartTime = time.ticks_ms()
        inputs = [
            ("Rotations", rotations),
            ("Velocity", velocityPercentage),
            ("Acceleration", acceleration),
            ("Brake Start", brakeStartPercentage),
            ("Correction Multiplier", correctionMultiplier),
        ]
        errors = self.__findErrors(
            self.__checkNotZero("Rotations", rotations),
            self.__checkVelocity(velocityPercentage, allowNegative=True),
            self.__checkRange("Brake start", brakeStartPercentage, 0, 1),
            self.__checkBelow("Correction multiplier", correctionMultiplier, 0),
        )
        if errors:
            self.__printErrors("Move Straight (Gyro)", inputs, errors, callStartTime)
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
        self.__printResults("Move Straight (Gyro)", inputs, [("Actual Rotations Traveled", motor.relative_position(rightPort) / self.DEGREES_PER_ROTATION), ("Ending Drift", self.__yaw())], callStartTime)

    async def squareUpOnWall(self, seconds=None, velocityPercentage=None, acceleration=None, deceleration=None) -> None:
        seconds = self.DEFAULTS["WALL_SECONDS"] if seconds is None else seconds
        velocityPercentage = self.DEFAULTS["WALL_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.DEFAULTS["WALL_ACCELERATION"] if acceleration is None else acceleration
        deceleration = self.DEFAULTS["WALL_DECELERATION"] if deceleration is None else deceleration
        callStartTime = time.ticks_ms()
        inputs = [
            ("Seconds", seconds),
            ("Velocity", velocityPercentage),
            ("Acceleration", acceleration),
            ("Deceleration", deceleration),
        ]
        errors = self.__findErrors(
            self.__checkAbove("Seconds", seconds, 0),
            self.__checkVelocity(velocityPercentage, allowNegative=True),
        )
        if errors:
            self.__printErrors("Square Up On Wall", inputs, errors, callStartTime)
            return

        wallStartTime = time.ticks_ms()
        await motor_pair.move_for_time(motor_pair.PAIR_1, int(seconds * 1000), 0, velocity=int(self.__percentageToUnits(velocityPercentage)),
                                       stop=motor.BRAKE, acceleration=acceleration, deceleration=deceleration)
        self.__printResults("Square Up On Wall", inputs, [("Actual Seconds", time.ticks_diff(time.ticks_ms(), wallStartTime) / 1000)], callStartTime)

    async def moveStraightUntilLine(self, lineColor, bothSensorsOnLine=False, velocityPercentage=None, acceleration=None) -> int:
        leftPort, rightPort = self.PORTS["LEFT_SENSOR"], self.PORTS["RIGHT_SENSOR"]
        velocityPercentage = self.DEFAULTS["LINE_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        callStartTime = time.ticks_ms()
        inputs = [
            ("Line Color", self.__colorName(lineColor)),
            ("Wait For Both Sensors", bothSensorsOnLine),
            ("Left Sensor", self.__portName(leftPort)),
            ("Right Sensor", self.__portName(rightPort)),
            ("Velocity", velocityPercentage),
            ("Acceleration", acceleration),
        ]

        errors = self.__findErrors(
            self.__checkOneOf("Line color", lineColor, self.LINE_COLOR_NAMES),
            self.__checkVelocity(velocityPercentage, allowNegative=True),
        )
        if errors:
            self.__printErrors("Move Straight Until Line", inputs, errors, callStartTime)
            return -1

        motor_pair.move(motor_pair.PAIR_1, 0, velocity=int(self.__percentageToUnits(velocityPercentage)), acceleration=acceleration)
        await runloop.until(lambda: self.__lineFound(leftPort, rightPort, lineColor, bothSensorsOnLine))
        triggeredSensorPort = leftPort if self.__onLine(leftPort, lineColor) else rightPort

        motor_pair.stop(motor_pair.PAIR_1)
        self.__printResults("Move Straight Until Line", inputs, [("Triggered Sensor", self.__portName(triggeredSensorPort))] + self.__sensorReadings(leftPort, rightPort), callStartTime)
        return triggeredSensorPort

    async def moveStraightUntilLineGyro(self, lineColor, bothSensorsOnLine=False, velocityPercentage=None, acceleration=None, correctionMultiplier=None) -> int:
        leftPort, rightPort = self.PORTS["LEFT_SENSOR"], self.PORTS["RIGHT_SENSOR"]
        velocityPercentage = self.DEFAULTS["LINE_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        correctionMultiplier = self.CORRECTION_MULTIPLIER if correctionMultiplier is None else correctionMultiplier
        callStartTime = time.ticks_ms()
        inputs = [
            ("Line Color", self.__colorName(lineColor)),
            ("Wait For Both Sensors", bothSensorsOnLine),
            ("Left Sensor", self.__portName(leftPort)),
            ("Right Sensor", self.__portName(rightPort)),
            ("Velocity", velocityPercentage),
            ("Acceleration", acceleration),
            ("Correction Multiplier", correctionMultiplier),
        ]
        errors = self.__findErrors(
            self.__checkOneOf("Line color", lineColor, self.LINE_COLOR_NAMES),
            self.__checkVelocity(velocityPercentage, allowNegative=True),
            self.__checkBelow("Correction multiplier", correctionMultiplier, 0),
        )
        if errors:
            self.__printErrors("Move Straight Until Line (Gyro)", inputs, errors, callStartTime)
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
        self.__printResults("Move Straight Until Line (Gyro)", inputs, [("Triggered Sensor", self.__portName(triggeredSensorPort))] + self.__sensorReadings(leftPort, rightPort) +
                         [("Actual Rotations Traveled", motor.relative_position(motorPort) / self.DEGREES_PER_ROTATION), ("Ending Drift", self.__yaw())], callStartTime)
        return triggeredSensorPort

    async def squareUpOnLine(self, lineColor, velocityPercentage=None, acceleration=None) -> None:
        leftPort, rightPort = self.PORTS["LEFT_SENSOR"], self.PORTS["RIGHT_SENSOR"]
        velocityPercentage = self.DEFAULTS["SQUARE_UP_LINE_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        callStartTime = time.ticks_ms()
        inputs = [
            ("Line Color", self.__colorName(lineColor)),
            ("Left Sensor", self.__portName(leftPort)),
            ("Right Sensor", self.__portName(rightPort)),
            ("Velocity", velocityPercentage),
            ("Acceleration", acceleration),
        ]

        errors = self.__findErrors(
            self.__checkOneOf("Line color", lineColor, self.LINE_COLOR_NAMES),
            self.__checkVelocity(velocityPercentage, allowNegative=True),
        )
        if errors:
            self.__printErrors("Square Up On Line", inputs, errors, callStartTime)
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

        self.__printResults("Square Up On Line", inputs, self.__sensorReadings(leftPort, rightPort), callStartTime)

    async def pidBlackLineFollow(self, rotations, sensorPort, midPointReflectionPercentage, edgeToFollow, proportionalCoef=None, integralCoef=None, derivativeCoef=None, velocityPercentage=None, acceleration=None) -> None:
        proportionalCoef = self.DEFAULTS["PID_P"] if proportionalCoef is None else proportionalCoef
        integralCoef = self.DEFAULTS["PID_I"] if integralCoef is None else integralCoef
        derivativeCoef = self.DEFAULTS["PID_D"] if derivativeCoef is None else derivativeCoef
        velocityPercentage = self.DEFAULTS["PID_VELOCITY"] if velocityPercentage is None else velocityPercentage
        acceleration = self.ACCELERATION if acceleration is None else acceleration
        callStartTime = time.ticks_ms()
        inputs = [
            ("Rotations", rotations),
            ("Sensor", self.__portName(sensorPort)),
            ("Midpoint Reflection", midPointReflectionPercentage),
            ("Edge", edgeToFollow),
            ("P", proportionalCoef),
            ("I", integralCoef),
            ("D", derivativeCoef),
            ("Velocity", velocityPercentage),
            ("Acceleration", acceleration),
        ]
        errors = self.__findErrors(
            self.__checkNotZero("Rotations", rotations),
            self.__checkVelocity(velocityPercentage),
            self.__checkRange("Midpoint reflection", midPointReflectionPercentage, 0, 100),
            self.__checkOneOf("Edge", edgeToFollow, (self.BLACK_LINE_LEFT_EDGE, self.BLACK_LINE_RIGHT_EDGE)),
        )
        if errors:
            self.__printErrors("PID Black Line Follow", inputs, errors, callStartTime)
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
        self.__printResults("PID Black Line Follow", inputs, [("Actual Rotations Traveled", motor.relative_position(rightPort) / self.DEGREES_PER_ROTATION), ("Final Sensor Reflection", color_sensor.reflection(sensorPort))], callStartTime)

    async def thatWasEasy(self, missionNumber=None):
        if not self.DEBUG:
            return
        for frequency, duration in self.RANDOM:
            await sound.beep(frequency, duration, self.RANDOM_2, waveform=sound.WAVEFORM_SQUARE)
        print("That was easy!")
        if missionNumber is not None:
            print("Mission " + str(missionNumber) + " was a piece of cake.")
        print("")
