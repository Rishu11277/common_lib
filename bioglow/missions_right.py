from hub import port
import runloop
import color
import motor, motor_pair
from Rockstar_lib import RW
import time


async def _runMission7Old(robot) -> None:
    #Mission 7 (Humongous Fungus) -> Uses move forward until black line (no gyro)
    await robot.moveStraightGyro(rotations=3.5, velocityPercentage=30)
    await robot.moveStraightUntilLine(lineColor=color.BLACK, velocityPercentage=30)
    await robot.moveStraightGyro(0.03, velocityPercentage=5)
    await robot.moveStraightGyro(rotations=-0.6, velocityPercentage=10)
    await robot.proportionalTurn(degrees=15, turnType="SPIN", velocityPercentage=20)
    await robot.proportionalTurn(degrees=-12, turnType="SPIN", velocityPercentage=20)

    return


async def _runMission7Alt(robot) -> None:
    #Mission 7 (Humongous Fungus)
    await robot.moveStraightGyro(rotations=4.02, velocityPercentage=30)
    await robot.moveStraightGyro(rotations=-0.7, velocityPercentage=10)
    await robot.proportionalTurn(degrees=15, turnType="SPIN", velocityPercentage=20)
    await robot.proportionalTurn(degrees=-12, turnType="SPIN", velocityPercentage=20)

    return

async def _runMission7(robot) -> None:
    #Mission 7 (Humongous Fungus)

    motor.run_for_degrees(port.C, 500, 1110)
    await robot.moveStraightGyro(3.5000000000000, velocityPercentage=60)
    await motor.run_for_degrees(port.C, 1400, 1110)
    await robot.moveStraightGyro(0.2, velocityPercentage=40)
    motor.run_for_degrees(port.C, 600, 1110)
    await robot.moveStraightGyro(rotations=-0.4, velocityPercentage=50)
    return

async def _runMission6(robot, forwardRotations=0.51) -> None:
    #Mission 6 (Leafcutter Frenzy)
    await robot.moveStraightUntilLine(lineColor=color.BLACK, velocityPercentage=50)
    await robot.proportionalTurn(degrees=-90, turnType="SPIN", velocityPercentage=20)

    #await robot.pidBlackLineFollow(1.4, sensorPort=port.F, midPointReflectionPercentage=60, edgeToFollow=RW.BLACK_LINE_LEFT_EDGE, proportionalCoef=0.1, velocityPercentage=8) #before derivative correction
    await robot.pidBlackLineFollow(1.4, sensorPort=port.F, midPointReflectionPercentage=60, edgeToFollow=RW.BLACK_LINE_LEFT_EDGE, proportionalCoef=0.1, derivativeCoef=3.0, velocityPercentage=8)
    await robot.proportionalTurn(degrees=-85, turnType="SPIN")
    await robot.moveForward(-0.8, velocityPercentage=10)
    await robot.moveStraightGyro(forwardRotations, velocityPercentage=50, acceleration=400, brakeStartPercentage=0.8, correctionMultiplier=-3.5)

    return


async def _runMission11(robot) -> None:
    #Mission 11 (Window to the Past)
    await robot.proportionalTurn(degrees=-83, turnType="SPIN", velocityPercentage=25)
    await robot.moveStraightGyro(4, velocityPercentage=75, acceleration=400, brakeStartPercentage=0.8, correctionMultiplier=-3.5)
    return


async def runMission7_6_11(robot) -> None:
    await _runMission7(robot)
    await _runMission6(robot)
    await _runMission11(robot)
    return



async def runMission6_11(robot) -> None:
    #use if Mission 7 (Humongous Fungus) is not to be run
    await robot.moveStraightGyro(rotations=3.3, velocityPercentage=65)
    await robot.moveStraightUntilLine(lineColor=color.BLACK, velocityPercentage=30)

    await _runMission6(robot, 0.64)
    await _runMission11(robot)
    return


async def _runMission13(robot) -> None:
    #Mission 13 (Keystone Species)
    await robot.moveStraightGyro(3.7, velocityPercentage=40)
    await robot.proportionalTurn(degrees=45, turnType="PIVOT")
    await robot.moveStraightGyro(0.25, velocityPercentage=30)
    return


async def _runMission12(robot) -> None:
    #Mission 12 (Forest Elder)
    await motor.run_for_degrees(port.D, -120, 400)
    await robot.moveStraightGyro(-0.37, velocityPercentage=30)
    await robot.proportionalTurn(degrees=-30, turnType="PIVOT")
    await robot.arcTurn(42, 85, velocityPercentage=-50)
    return


async def runMission13_12(robot) -> None:
    await _runMission13(robot)
    await _runMission12(robot)


async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.A, port.B)
    robot = RW(robot="Misty", leftMotorPort=port.A, rightMotorPort=port.B)

    await _runMission7(robot)
    await _runMission6(robot)
    # await runMission7_6_11(robot)
    #await runMission13_12(robot)

    #await runMission6_11(robot)

    #right home base to left home base
    #await robot.arcTurn(32, -90, velocityPercentage=20)
    #await robot.moveStraightGyro(4, velocityPercentage=40)
    #await robot.proportionalTurn(degrees=-45, turnType="SPIN")
    #await robot.moveForward(1.4, velocityPercentage=40)

runloop.run(main())
