from hub import port
import runloop
import color
import motor
import motor_pair
from Rockstar_lib import RW


async def runMission1(robot: RW) -> None:
    # Mission 1 (Drone Survey)
    await robot.moveForward(4.76, velocityPercentage=100)
    await robot.moveForward(-2, velocityPercentage=100)
    await robot.turn(-23, 30, "PIVOT")
    await robot.moveForward(2.9, velocityPercentage=100)
    await robot.turn(45, 30, "CAR")
    await robot.moveForward(3, velocityPercentage=100, acceleration=10000, deceleration=4000)


async def runMission2(robot: RW) -> None:
    # Mission 2 (Exploding Seeds)
    await robot.turn(46, 30, "PIVOT")
    await robot.moveForward(2.25, velocityPercentage=100)
    await motor.run_for_degrees(port.C, 500, 1110)  # 1110 = 100% on a medium motor
    await robot.moveForward(-2, velocityPercentage=100)
    motor.run_for_degrees(port.C, -400, 1110)


async def runMission3(robot: RW) -> None:
    # Mission 3 (Flip the Rock)
    motor.run_for_degrees(port.C, 1600, 1110)
    await robot.moveForward(2.38, velocityPercentage=100, acceleration=1000, deceleration=1000)
    motor.run_for_degrees(port.C, -1600, 1110)
    await robot.moveForward(-2.41, velocityPercentage=100, acceleration=10000, deceleration=4000)


async def runMission2and3(robot: RW) -> None:
    # Mission 3 (Flip the Rock)
    motor.run_for_degrees(port.C, 1600, 1110)
    await robot.moveStraightGyro(2.40, velocityPercentage=80, acceleration=1000)
    motor.run_for_degrees(port.C, -1600, 1110)
    await robot.moveStraightGyro(-2.39, velocityPercentage=40, acceleration=10000)
    await robot.moveStraightGyro(-0.5, velocityPercentage=100)  # square up against wall

    # Mission 2 (Exploding Seeds)
    await robot.turn(42, 30, "PIVOT")
    await robot.moveStraightGyro(2.3, velocityPercentage=40, correctionMultiplier=-1.5)
    await motor.run_for_degrees(port.C, 850, 1110)
    await robot.moveStraightGyro(-2.3, velocityPercentage=40, correctionMultiplier=-1.5)
    await motor.run_for_degrees(port.C, -800, 1110)


async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    robot = RW(robot="Misty", leftMotorPort=port.A, rightMotorPort=port.B)

    # await runMission1(robot)
    # await runMission2(robot)
    await runMission3(robot)
    # await runMission2and3(robot)


runloop.run(main())
