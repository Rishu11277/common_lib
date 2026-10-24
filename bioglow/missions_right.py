from hub import port
import runloop
import color
import motor
import motor_pair
from Rockstar_lib import RW


async def _runMission7Old(robot: RW) -> None:
    # Mission 7 (Humongous Fungus) -> uses move until black line (no gyro)
    await robot.moveStraightGyro(3.5, velocityPercentage=30)
    await robot.moveStraightUntilLine(color.BLACK, velocityPercentage=30)
    await robot.moveStraightGyro(0.03, velocityPercentage=5)
    await robot.moveStraightGyro(-0.6, velocityPercentage=10)
    await robot.proportionalTurn(15, "SPIN", velocityPercentage=20)
    await robot.proportionalTurn(-12, "SPIN", velocityPercentage=20)


async def _runMission7Alt(robot: RW) -> None:
    # Mission 7 (Humongous Fungus)
    await robot.moveStraightGyro(4.02, velocityPercentage=30)
    await robot.moveStraightGyro(-0.7, velocityPercentage=10)
    await robot.proportionalTurn(15, "SPIN", velocityPercentage=20)
    await robot.proportionalTurn(-12, "SPIN", velocityPercentage=20)


async def _runMission7(robot: RW) -> None:
    # Mission 7 (Humongous Fungus)
    motor.run_for_degrees(port.C, 500, 1110)
    await robot.moveStraightGyro(3.5, velocityPercentage=60)
    await motor.run_for_degrees(port.C, 1400, 1110)
    await robot.moveStraightGyro(0.2, velocityPercentage=40)
    motor.run_for_degrees(port.C, 600, 1110)
    await robot.moveStraightGyro(-0.4, velocityPercentage=50)


async def _runMission6(robot: RW, forwardRotations=0.51) -> None:
    # Mission 6 (Leafcutter Frenzy)
    await robot.moveStraightUntilLine(color.BLACK, velocityPercentage=50)
    await robot.proportionalTurn(-90, "SPIN", velocityPercentage=20)
    await robot.pidBlackLineFollow(1.4, port.F, 60, RW.BLACK_LINE_LEFT_EDGE, proportionalCoef=0.1, derivativeCoef=3.0, velocityPercentage=10)
    await robot.proportionalTurn(-85, "SPIN")
    await robot.moveForward(-0.8, velocityPercentage=10)
    await robot.moveStraightGyro(forwardRotations, velocityPercentage=50, acceleration=400, brakeStartPercentage=0.8, correctionMultiplier=-3.5)


async def _runMission11(robot: RW) -> None:
    # Mission 11 (Window to the Past)
    await robot.proportionalTurn(-83, "SPIN", velocityPercentage=25)
    await robot.moveStraightGyro(4, velocityPercentage=75, acceleration=400, brakeStartPercentage=0.8, correctionMultiplier=-3.5)


async def runMission7_6_11(robot: RW) -> None:
    await _runMission7(robot)
    await _runMission6(robot)
    await _runMission11(robot)


async def runMission6_11(robot: RW) -> None:
    # Use if Mission 7 (Humongous Fungus) is not run
    await robot.moveStraightGyro(3.3, velocityPercentage=65)
    await robot.moveStraightUntilLine(color.BLACK, velocityPercentage=30)
    await _runMission6(robot, 0.64)
    await _runMission11(robot)


async def _runMission13(robot: RW) -> None:
    # Mission 13 (Keystone Species)
    await robot.moveStraightGyro(3.7, velocityPercentage=40)
    await robot.proportionalTurn(45, "PIVOT")
    await robot.moveStraightGyro(0.25, velocityPercentage=30)


async def _runMission12(robot: RW) -> None:
    # Mission 12 (Forest Elder)
    await motor.run_for_degrees(port.D, -120, 400)
    await robot.moveStraightGyro(-0.37, velocityPercentage=30)
    await robot.proportionalTurn(-30, "PIVOT")
    await robot.arcTurn(42, 85, velocityPercentage=-50)


async def runMission13_12(robot: RW) -> None:
    await _runMission13(robot)
    await _runMission12(robot)


async def _runMission15(robot: RW) -> None:
    # Biocentric Architecture
    await robot.moveStraightGyro(1.2, velocityPercentage=25)
    await robot.moveStraightGyro(-2, velocityPercentage=100)


async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    robot = RW(
        robot="Misty",
        leftMotorPort=port.A,
        rightMotorPort=port.B,
        leftSensorPort=port.E,
        rightSensorPort=port.F,
    )

    # await _runMission15(robot)
    # await _runMission7(robot)
    # await _runMission6(robot)
    await runMission7_6_11(robot)
    # await runMission13_12(robot)
    # await runMission6_11(robot)

    # Right home base to left home base
    # await robot.arcTurn(32, -90, velocityPercentage=20)
    # await robot.moveStraightGyro(4, velocityPercentage=40)
    # await robot.proportionalTurn(-45, "SPIN")
    # await robot.moveForward(1.4, velocityPercentage=40)


runloop.run(main())
