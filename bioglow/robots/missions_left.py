from hub import port
import color
import hub
import motor
import motor_pair
import runloop
import time

from Rockstar_lib import RW


async def _runMission1(robot: RW) -> None:
    # Mission 1 (Drone Survey)
    await robot.moveForward(93.312842, velocityPercentage=100)
    await robot.moveForward(-43.127784, velocityPercentage=100)
    await robot.turn(-23.56, velocityPercentage=25, turnType="PIVOT")
    await robot.moveForward(57.830438, velocityPercentage=100)
    # The original mission runs this car turn at 554 degrees per second.
    await robot.turn(45, velocityPercentage=49.91, turnType="CAR")
    await robot.moveForward(58.810614, velocityPercentage=100, acceleration=10000, deceleration=4000)
    return


async def _runMission2(robot: RW) -> None:
    # Mission 2 (Exploding Seeds)
    # await robot.turn(35, velocityPercentage=25, turnType="PIVOT")
    await robot.proportionalTurn(40, velocityPercentage=25, turnType="PIVOT")
    await robot.moveStraightGyro(35.286369, 100)
    # 1110 deg/s is 100% velocity on a medium motor.
    await motor.run_for_degrees(port.C, 980, 1000)
    # await robot.moveForward(-39.207076, velocityPercentage=100)
    await robot.moveForward(-39.207076, velocityPercentage=100, acceleration=10000, deceleration=4000)  # acceleration/deceleration of 10,000 is max

    motor.run_for_degrees(port.C, -980, 1110)
    await robot.moveForward(-19.603538, velocityPercentage=100)  # squares up against wall

    return


async def _runMission3(robot: RW) -> None:
    # Mission 3 (Flip the Rock)
    motor.run_for_degrees(port.C, 2000, 1110)  # was 1600
    time.sleep(0.5)  # motor needs a bit of time to raise the attachment

    # don't need gyro correction because masher aligns
    await robot.moveForward(46.656421, velocityPercentage=100, acceleration=5000, deceleration=1000)
    motor.run_for_degrees(port.C, -1800, 1110)

    # this works if running alone
    await robot.moveForward(-47.244527, velocityPercentage=100, acceleration=10000, deceleration=4000)  # acceleration/deceleration of 10,000 is max
    # await robot.moveStraightGyro(-47.244527, 30) #this is best if combining with another mission

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
        robot="Misty",
        leftMotorPort=port.A,
        rightMotorPort=port.B,
        leftSensorPort=port.E,
        rightSensorPort=port.F,
        CENTIMETERS=True,
    )

    missionSelected = 0
    colors = [color.GREEN, color.AZURE, color.ORANGE, color.MAGENTA, color.YELLOW, color.PURPLE]
    alphabet = "ABCDEFGHIJKLMN"
    hub.light.color(0, colors[0])
    hub.light.color(1, colors[0])
    hub.light_matrix.write(alphabet[0])

    while True:
        if hub.button.pressed(hub.button.RIGHT):
            time.sleep(0.25)
            missionSelected += 1
            hub.light_matrix.write(alphabet[missionSelected % len(alphabet)])
            hub.light.color(0, colors[missionSelected % len(colors)])
            hub.light.color(1, colors[missionSelected % len(colors)])
            hub.sound.beep(freq=85, volume=100, duration=250)
        elif hub.button.pressed(hub.button.LEFT):
            time.sleep(0.25)
            missionSelected -= 1
            hub.light_matrix.write(alphabet[missionSelected % len(alphabet)])
            hub.light.color(0, colors[missionSelected % len(colors)])
            hub.light.color(1, colors[missionSelected % len(colors)])
            hub.sound.beep(freq=300, volume=100, duration=250)
        elif hub.button.pressed(3):
            if missionSelected == 0:
                print("Running mission 0.")
                await runMission2and3and1(robot)
            elif missionSelected == 1:
                print("Running mission 1.")
                await _runMission3(robot)
            elif missionSelected == 2:
                print("Running mission 2.")
                await _runMission1(robot)
            elif missionSelected == 3:
                print("Running mission 3.")


runloop.run(main())
