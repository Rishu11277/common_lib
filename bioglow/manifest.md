# Rockstar_lib.py End-User API Manifest

Use this manifest when writing end-user robot programs that import and use the `RW` class from `Rockstar_lib.py`.

## IMPORT

```python
from hub import port
import runloop
import color
import motor_pair
from Rockstar_lib import RW
```

## BASIC SETUP

Pair the drive motors, then create the robot. Do both inside `main()` before calling any movement function.

```python
motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
robot = RW(robot="Misty", leftMotorPort=port.A, rightMotorPort=port.B)
```

Every movement function is called on `robot`.

## CREATE THE ROBOT

```python
robot = RW(
    robot="Misty",
    leftMotorPort=port.A,
    rightMotorPort=port.B,
    leftSensorPort=port.E,
    rightSensorPort=port.F,
    wheelBaseInCentimeters=8.8,
    acceleration=500,
    deceleration=1000,
    brakeStartPercentage=0.9,
    correctionMultiplier=-3.5,
    debug=True,
)
```

Every parameter is optional. The values above are the defaults.

| Parameter | Meaning |
|---|---|
| `robot` | Name shown in debug output |
| `leftMotorPort`, `rightMotorPort` | Drive motor ports |
| `leftSensorPort`, `rightSensorPort` | Light sensor ports used by line functions |
| `wheelBaseInCentimeters` | Distance between the centers of the two tires |
| `acceleration`, `deceleration` | Default acceleration and deceleration for movement |
| `brakeStartPercentage` | Fraction of a gyro move (0 to 1) after which braking starts |
| `correctionMultiplier` | Gyro drift correction strength. Must be negative. Typical values are -1 to -5 |
| `debug` | `True` prints movement diagnostics and enables `thatWasEasy()`. `False` keeps input validation errors enabled |

The pair ports and the `RW` motor ports must match.

## DEBUG OUTPUT

With `debug=True`, movement methods print their name, inputs, measured results, and elapsed time in seconds.

```
[Misty] Turn
[Type] SPIN
[Degrees] 90
[Velocity] 30
[Actual Degrees Turned] 90.4
[Time] 0.62
```

If input validation fails, the method prints the validation errors and returns before moving, even with `debug=False`.

```
[Misty] Turn
[Type] BAD
[Degrees] 200
[Velocity] 150
[Error] Turn type must be PIVOT or SPIN or CAR, got BAD
[Error] Degrees must be -179 to 179 and not 0, got 200
[Error] Velocity must be 1 to 100, got 150
[Time] 0.00
```

## UNITS

- **Velocity** is a percentage of `RW.WHEEL_MAX_VELOCITY`.
- **Rotations** are wheel rotations. Positive values drive forward and negative values drive backward.
- **Turn degrees** are relative to the starting heading. The allowed range is -179 to 179, excluding 0. Positive angles turn right for `turn()`, `proportionalTurn()`, and forward arcs. Backward arcs reverse that heading change.

## MOVEMENT

Move straight without gyro correction.

```python
await robot.moveForward(rotations)
```

Examples:

```python
await robot.moveForward(2, velocityPercentage=50)
await robot.moveForward(-2, velocityPercentage=50)
```

Optional settings:

```python
await robot.moveForward(rotations, velocityPercentage, acceleration=500, deceleration=1000)
```

| Input | Allowed values |
|---|---|
| `rotations` | Any number except 0 |
| `velocityPercentage` | 1 to 100. Default 40 |
| `acceleration`, `deceleration` | Default to the values set on the `RW` instance |

Move straight with gyro correction. The braking calculation uses 10% of maximum wheel speed as its floor. A move that starts below that speed can speed up during braking.

```python
await robot.moveStraightGyro(rotations)
```

Examples:

```python
await robot.moveStraightGyro(3, velocityPercentage=60)
await robot.moveStraightGyro(-0.5, velocityPercentage=30)
```

Optional settings:

```python
await robot.moveStraightGyro(rotations, velocityPercentage, acceleration=500, brakeStartPercentage=0.9, correctionMultiplier=-3.5)
```

| Input | Allowed values |
|---|---|
| `rotations` | Any number except 0 |
| `velocityPercentage` | -100 to 100, excluding 0. Default 40. `rotations` sets direction |
| `brakeStartPercentage` | 0 to 1. Defaults to the value set on the `RW` instance |
| `correctionMultiplier` | Negative. Defaults to the value set on the `RW` instance |
| `acceleration` | Defaults to the value set on the `RW` instance |

Square up against a wall by driving for a set time.

```python
await robot.squareUpOnWall()
```

Optional settings:

```python
await robot.squareUpOnWall(seconds=1.0, velocityPercentage=100, acceleration=1000, deceleration=1000)
```

`seconds` must be greater than 0. `velocityPercentage` accepts -100 to 100, excluding 0. Use a negative value to back into a wall.

```python
await robot.squareUpOnWall(seconds=0.8, velocityPercentage=-50)
```

## TURN

All turns use the gyro and reset the heading to 0 before turning.

Pivot, spin, or car turn:

```python
await robot.turn(degrees)
```

| `turnType` | What happens |
|---|---|
| `"PIVOT"` | One wheel moves, the other stays stopped |
| `"SPIN"` | Both wheels move in opposite directions |
| `"CAR"` | Outer wheel at 75% and inner wheel at 25% of the velocity |

Examples:

```python
await robot.turn(90, 30, "SPIN")
await robot.turn(-45, 40, "PIVOT")
await robot.turn(45, 50, "CAR")
```

`velocityPercentage` accepts 1 to 100 and defaults to 40. `turnType` defaults to `"PIVOT"`.

Arc turn along a curve with a set radius:

```python
await robot.arcTurn(radiusInCm, degrees)
```

Examples:

```python
await robot.arcTurn(20, 90)
await robot.arcTurn(20, -90, velocityPercentage=30)
await robot.arcTurn(42, 85, velocityPercentage=-50)
```

| Input | Allowed values |
|---|---|
| `radiusInCm` | 0 or more. 0 equals a spin turn |
| `velocityPercentage` | -100 to 100, not 0. Default 20. Negative drives backward |

Arc motion matches the reference `arcTurn` in [byronrockstars/common_lib](https://github.com/byronrockstars/common_lib/blob/a798ccf7be8537dd5288f70bab7827ebe3c58162/edu/byron/bioglow/rockstar_lib.py#L84): steering is selected from the angle's sign, and completion uses the magnitude of the gyro angle. Reversing velocity keeps the steering value and reverses the physical heading change.

Proportional turn that slows down near the target for better accuracy:

```python
await robot.proportionalTurn(degrees)
```

Examples:

```python
await robot.proportionalTurn(90, "SPIN")
await robot.proportionalTurn(-45, "PIVOT", velocityPercentage=40, timeout=3)
```

| Input | Allowed values |
|---|---|
| `turnType` | `"PIVOT"` or `"SPIN"`. Default `"PIVOT"` |
| `velocityPercentage` | 1 to 100. Default is 40 for PIVOT, 25 for SPIN |
| `timeout` | More than 0 seconds. Default 2.0 |

If the turn reaches the timeout, it stops. With `debug=True`, it prints `[Result] Timed Out`.

## LINE DETECTION

Line functions use the sensor ports set when the robot was created. Line color must be `color.BLACK` or `color.WHITE`.

Move straight until a light sensor finds the line:

```python
triggeredSensorPort = await robot.moveStraightUntilLine(lineColor)
```

Move straight with gyro correction until a light sensor finds the line:

```python
triggeredSensorPort = await robot.moveStraightUntilLineGyro(lineColor)
```

Examples:

```python
await robot.moveStraightUntilLine(color.BLACK, velocityPercentage=30)
await robot.moveStraightUntilLineGyro(color.WHITE, bothSensorsOnLine=True)
```

Optional settings:

```python
await robot.moveStraightUntilLine(lineColor, bothSensorsOnLine=False, velocityPercentage=25, acceleration=500)
await robot.moveStraightUntilLineGyro(lineColor, bothSensorsOnLine=False, velocityPercentage=25, acceleration=500, correctionMultiplier=-3.5)
```

- `bothSensorsOnLine=True` waits until both sensors see the line at the same time.
- `velocityPercentage` accepts -100 to 100, excluding 0. Default 25. Negative values drive backward.
- Both return a sensor port. If the left sensor sees the line when the result is checked, they return its port. Otherwise they return the right sensor port. If input validation fails, they return `-1`.
- `acceleration` and the gyro method’s `correctionMultiplier` default to the values set on the `RW` instance.

Square up on a line. Each wheel stops when its sensor sees the line.

```python
await robot.squareUpOnLine(lineColor)
```

Examples:

```python
await robot.squareUpOnLine(color.BLACK)
await robot.squareUpOnLine(color.WHITE, velocityPercentage=10)
```

Optional settings:

```python
await robot.squareUpOnLine(lineColor, velocityPercentage=15, acceleration=500)
```

`velocityPercentage` accepts -100 to 100, excluding 0. Default 15. Negative values drive backward. `acceleration` defaults to the value set on the `RW` instance.

For best results, run slowly, back off the line, and run it a second time.

Follow a black line using PID correction. Positive rotations move forward; negative rotations move backward. Keep `velocityPercentage` positive for either direction.

```python
await robot.pidBlackLineFollow(rotations, sensorPort, midPointReflectionPercentage, edgeToFollow)
```

Example:

```python
await robot.pidBlackLineFollow(1.4, port.F, 60, RW.BLACK_LINE_LEFT_EDGE, proportionalCoef=0.1, derivativeCoef=3.0, velocityPercentage=8)
await robot.pidBlackLineFollow(-1.4, port.F, 60, RW.BLACK_LINE_LEFT_EDGE, proportionalCoef=0.1, derivativeCoef=3.0, velocityPercentage=8)
```

Optional settings:

```python
await robot.pidBlackLineFollow(
    rotations,
    sensorPort,
    midPointReflectionPercentage,
    edgeToFollow,
    proportionalCoef=0.15,
    integralCoef=0.0,
    derivativeCoef=0.0,
    velocityPercentage=10,
    acceleration=500,
)
```

| Input | Allowed values |
|---|---|
| `midPointReflectionPercentage` | 0 to 100. Average of the black and white readings |
| `edgeToFollow` | `RW.BLACK_LINE_LEFT_EDGE` or `RW.BLACK_LINE_RIGHT_EDGE` |
| `velocityPercentage` | 1 to 100. Default 10 |
| `acceleration` | Defaults to the value set on the `RW` instance |

Tune P first, then D, then I last.

## CLASS CONSTANTS

Change these on the class to adjust behavior for every robot.

| Constant | Default | Meaning |
|---|---|---|
| `WHEEL_MAX_VELOCITY` | 1110 | Max wheel speed that 100% maps to |
| `LIGHT_REFLECTIONS` | `{"BLACK": 25, "WHITE": 95}` | Black is detected below 25 and white above 95 |
| `LOOP_DELAY_MS` | 10 | Milliseconds between updates in loops that call `runloop.sleep_ms()` |
| `YAW_RESET_DELAY` | 0.1 | Seconds to wait after resetting yaw in `turn()`, `proportionalTurn()`, and `moveStraightUntilLineGyro()`. `arcTurn()` uses a fixed 0.1-second delay |
| `CAR_TURN_WHEEL_RATIOS` | `{"OUTER": 0.75, "INNER": 0.25}` | Wheel speeds for CAR turns |
| `PROPORTIONAL_TURN` | See file | Min power, max power, divisor, and default velocity for proportional turns |
| `DEFAULTS` | See file | Default values for optional parameters |

Example:

```python
RW.LIGHT_REFLECTIONS["BLACK"] = 20
```

## COMPLETION SOUND

With `debug=True`, `thatWasEasy()` plays a short tune and prints `That was easy!`. With `debug=False`, the method returns immediately.

```python
await robot.thatWasEasy()
await robot.thatWasEasy(missionNumber=3)
```

Pass an optional `missionNumber` to include it in the output.

## COMPLETE STARTER PROGRAM

```python
from hub import port
import runloop
import color
import motor_pair
from Rockstar_lib import RW


async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    robot = RW(robot="Misty", leftMotorPort=port.A, rightMotorPort=port.B)

    await robot.moveStraightGyro(2, velocityPercentage=50)
    await robot.proportionalTurn(90, "SPIN")
    await robot.moveStraightUntilLineGyro(color.BLACK)
    await robot.moveForward(-1, velocityPercentage=40)


runloop.run(main())
```

## IMPORTANT NOTES

All movement methods and `thatWasEasy()` are asynchronous. Call them with `await` from inside an `async` function.

```python
await robot.moveForward(1, velocityPercentage=50)
```

Creating the robot with `RW(...)` is a normal call and does not use `await`.

Run the whole program once with `runloop.run(main())`.

`moveStraightUntilLineGyro()` and `pidBlackLineFollow()` yield between control updates. The gyro distance, proportional turn, and line squaring loops update continuously. `turn()`, `arcTurn()`, and `proportionalTurn()` pause synchronously after resetting yaw before starting the motors.
