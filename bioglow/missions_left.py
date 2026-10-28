from hub import port, motion_sensor
import runloop, time
from Rockstar_lib import RW
import motor, motor_pair

#Returns true if the gyro yaw angle has reached the degreesToTurn value indicating that a turn has been completed.
def __turnCompleted(degreesToTurn) -> bool:
    #multiplying by -0.1 makes yaw angle match values in hub
    return abs(motion_sensor.tilt_angles()[0] * -0.1) >= abs(degreesToTurn)


async def runMission1(robot: RW) -> None:
    #Mission 1 (Drone Survey)
    await robot.moveForward(rotations=4.76, velocityPercentage=100)
    await robot.moveForward(rotations=-2.1, velocityPercentage=100)
    await robot.turn(-23.5, turnType="PIVOT")
    await robot.moveForward(rotations=2.95, velocityPercentage=100)
    await robot.turn(45, turnType="CAR")
    #await robot.moveForward(rotations=3, velocityPercentage=100, acceleration=10000, deceleration=4000)
    return


async def _runMission2(robot: RW):
    #Mission 2 (Exploding Seeds)
    #await robot.turn(35, turnType="PIVOT")
    await robot.proportionalTurn(35, turnType="PIVOT", velocityPercentage=25)
    await robot.moveStraightGyro(1.78, 100)
    await motor.run_for_degrees(port.C, 1000, 1110) #1110 is 100% velocity on a medium motor
    await robot.moveForward(rotations=-2, velocityPercentage=100)
    motor.run_for_degrees(port.C, -1000, 1110)
    await robot.moveForward(-1, velocityPercentage=100) #squares up against wall

    return


async def _runMission3(robot: RW) -> None:
    #Mission 3 (Flip the Rock)
    #19.6035381584 WHEEL CIRCUMFERENCE
    motor.run_for_degrees(port.C, 2000, 1110) #was 1600
    time.sleep(0.5) #motor needs a bit of time to raise the attachment

    #don't need gyro correction because masher aligns
    await robot.moveForward(rotations=2.38, velocityPercentage=100, acceleration=5000, deceleration=1000)
    motor.run_for_degrees(port.C, -1800, 1110)

    #this works if running alone
    await robot.moveForward(rotations=-2.41, velocityPercentage=100, acceleration=10000, deceleration=4000) #acceleration/deceleration of 10,000 is max
    #await robot.moveStraightGyro(-2.41, 30) #this is best if combining with another mission

    return

async def runMission2and3(robot: RW) -> None:
    await _runMission2(robot)
    time.sleep(2)
    await _runMission3(robot)
    return


async def main():
    robot = RW(
        robot="Misty",
        leftMotorPort=port.A,
        rightMotorPort=port.B
    )

    #await runMission2and3(robot)

    await runMission1(robot)

runloop.run(main())