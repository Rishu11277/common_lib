from hub import port
import motor
import motor_pair
import runloop
import time

from Rockstar_lib import RW


async def _runMission1(robot: RW) -> None:
    # Mission 1 (Drone Survey)
    await robot.moveForward(rotations=4.76, velocityPercentage=100)
    await robot.moveForward(rotations=-2.1, velocityPercentage=100)
    await robot.turn(-23.5, velocityPercentage=25, turnType="PIVOT")
    await robot.moveForward(rotations=2.95, velocityPercentage=100)
    await robot.turn(45, velocityPercentage=50, turnType="CAR")
    # await robot.moveForward(rotations=3, velocityPercentage=100, acceleration=10000, deceleration=4000)
    return


async def _runMission2(robot: RW) -> None:
    # Mission 2 (Exploding Seeds)
    # await robot.turn(35, velocityPercentage=25, turnType="PIVOT")
    await robot.proportionalTurn(40, velocityPercentage=25, turnType="PIVOT")
    await robot.moveStraightGyro(1.8, 100)
    # 1110 deg/s is 100% velocity on a medium motor.
    await motor.run_for_degrees(port.C, 980, 1000)
    # await robot.moveForward(rotations=-2, velocityPercentage=100)
    await robot.moveForward(rotations=-2, velocityPercentage=100, acceleration=10000, deceleration=4000)  # acceleration/deceleration of 10,000 is max

    motor.run_for_degrees(port.C, -980, 1110)
    await robot.moveForward(-1, velocityPercentage=100)  # squares up against wall

    return


async def _runMission3(robot: RW) -> None:
    # Mission 3 (Flip the Rock)
    # 19.6035381584 WHEEL CIRCUMFERENCE
    motor.run_for_degrees(port.C, 2000, 1110)  # was 1600
    time.sleep(0.5)  # motor needs a bit of time to raise the attachment

    # don't need gyro correction because masher aligns
    await robot.moveForward(rotations=2.38, velocityPercentage=100, acceleration=5000, deceleration=1000)
    motor.run_for_degrees(port.C, -1800, 1110)

    # this works if running alone
    await robot.moveForward(rotations=-2.41, velocityPercentage=100, acceleration=10000, deceleration=4000)  # acceleration/deceleration of 10,000 is max
    # await robot.moveStraightGyro(-2.41, 30) #this is best if combining with another mission

    return


async def runMission2and3(robot: RW) -> None:
    await _runMission2(robot)
    time.sleep(2)
    await _runMission3(robot)
    return


async def runMission2and3and1(robot: RW) -> None:
    await _runMission2(robot)
    time.sleep(2)
    await _runMission3(robot)
    time.sleep(10)
    await _runMission1(robot)
    return


async def main() -> None:
    motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    robot = RW(
        robot="Ash",
        leftMotorPort=port.A,
        rightMotorPort=port.B,
        leftSensorPort=port.E,
        rightSensorPort=port.F,
    )

    # await _runMission3(robot)
    # await runMission2and3(robot)
    # await _runMission1(robot)
    await runMission2and3and1(robot)


runloop.run(main())
