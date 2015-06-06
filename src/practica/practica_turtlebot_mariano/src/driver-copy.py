#!/usr/bin/env python


# Every python controller needs these lines
import roslib; roslib.load_manifest('practica_turtlebot')
import rospy
import time

# The velocity command message
from geometry_msgs.msg import Vector3, Twist, Quaternion, Pose

# The laser scan message
from sensor_msgs.msg import LaserScan

# The odometry message
from nav_msgs.msg import Odometry

# We use a hyperbolic tangent as a transfer function
from math import tanh, radians, degrees
import math

class Driver:
    def __init__(self, end_pose, rate=5):
      self.current_pose = Pose()
      self.end_pose = end_pose
      self.rate = rate
      self.obstacle = False
      self.obstacle_threshold = 1

      # Subscriber for the encoder data
      # When data of type LaserScal arrives from topic 'scan' call laser_callback function immediately
      self.sub_scan = rospy.Subscriber('scan', LaserScan, self.laser_callback) # self.sub_scan.unregister()
      self.sub_odom = rospy.Subscriber('odom', Odometry, self.odometry_callback) # self.sub_odom.unregister()

      # Publisher for movement commands
      # We publish data of type Twist in velocity topic
      self.cmd_vel = rospy.Publisher("/mobile_base/commands/velocity", Twist)

      # Let the world know we're ready
      rospy.loginfo('Driver initialized')

      # What function to call when you ctrl + c    
      rospy.on_shutdown(self.shutdown)

      time.sleep(1)

    def bug_0(self, turn_orientation = 'Left', accepted_error = 1):
      rospy.loginfo('Starting bug_0 algorithm')
      r = rospy.Rate(self.rate)
      self.head_toward_goal()
      while not self.is_goal():
        if not self.is_obstacle():
          self.go_forward()
          self.head_toward_goal()
        else:
          self.turn()
        r.sleep()
      rospy.loginfo('Stopping bug_0 algorithm')

    # Turn the robot facing the goal
    def head_toward_goal(self):
      self.turn_degrees(self.degrees_to_goal())

      # self.turn_degrees(180)

    # Turn the robot facing the goal
    # Iterative approach. No so accurate
    def head_toward_goal_i(self):
      while not self.is_facing_goal():
        self.turn(5)

    def turn_on_obstacle(self):
      rospy.loginfo('Starting turn_on_obstacle')
      r = rospy.Rate(self.rate)
      while not self.is_goal():
        if not self.is_obstacle():
          self.go_forward()
        else:
          self.turn()
        r.sleep()
      rospy.loginfo('Stopping turn_on_obstacle')
      self.stop()

    def go_no_obstacle(self):
      rospy.loginfo('Starting go_no_obstacle')
      r = rospy.Rate(self.rate)
      self.head_toward_goal()
      while not self.is_goal():
        self.go_forward()
        r.sleep()
      rospy.loginfo('Stopping go_no_obstacle')
      self.stop()

    # Return true if there is a obstacle in the forward direction. False otherwise.
    def is_obstacle(self):
      if self.obstacle:
        rospy.loginfo('Obstacle found!!!')
      return self.obstacle

    # Laser returns NaN if objects is too far or too near. We must take care!
    def laser_callback(self, scan):
      closest = min(scan.ranges)
      self.obstacle = self.obstacle_threshold >= closest or (math.isnan(closest) and self.obstacle)

    def odometry_callback(self, odom):
      self.current_pose = odom.pose.pose
      # rospy.loginfo('Odometry data: {0}'.format(odom))
      # Read odometry params
      # rospy.loginfo('Odometry data:')
      # rospy.loginfo('Current position: x = {0}, y = {1}, z = {2}'.format(odom.pose.pose.position.x, odom.pose.pose.position.y, odom.pose.pose.position.z)) 
      rospy.loginfo('Current orientation: x = {0}, y = {1}, z = {2}'.format(odom.pose.pose.orientation.x, odom.pose.pose.orientation.y, odom.pose.pose.orientation.z)) 
      # rospy.loginfo('Current linear speed: x = {0}, y = {1}, z = {2}'.format(odom.twist.twist.linear.x, odom.twist.twist.linear.y, odom.twist.twist.linear.z)) 
      # rospy.loginfo('Current angular speed: x = {0}, y = {1}, z = {2}'.format(odom.twist.twist.angular.x, odom.twist.twist.angular.y, odom.twist.twist.angular.z)) 

    # Move the robot in the forward direction
    def go_forward(self, speed = 5):
      # rospy.loginfo('Moving forward, Speed: {0}'.format(speed))
      twist_forward = Twist()
      # let's go forward at 0.5 m/s
      twist_forward.linear.x = speed
      # publish the command
      self.cmd_vel.publish(twist_forward)

    # Move the robot in the forward direction
    def go_forward_distance(self, distance, iterations = 10):
      rospy.loginfo('Moving forward, Distance: {0} '.format(distance))
      r = rospy.Rate(self.rate)
      time_per_cicle = 1/float(self.rate)
      total_time = iterations * time_per_cicle
      forward_speed = distance/total_time

      for i in range(0, iterations):
        self.go_forward(forward_speed)
        r.sleep()

      self.go_forward(0)
      time.sleep(1.25)

    def turn(self, turn_speed = 45):
      # rospy.loginfo('Turning robot, Speed: {0} degrees/sec'.format(turn_speed))
      twist_turn = Twist()
      # let's go forward at turn_speed degrees/sec
      twist_turn.angular.z = radians(turn_speed)
      # publish the command
      self.cmd_vel.publish(twist_turn)

    def turn_degrees(self, degrees, iterations = 10):
      rospy.loginfo('Turning robot, Degrees: {0} '.format(degrees))
      r = rospy.Rate(self.rate)
      time_per_cicle = 1/float(self.rate)
      total_time = iterations * time_per_cicle
      turn_speed = degrees/total_time

      for i in range(0, iterations):
        self.turn(turn_speed)
        r.sleep()

      self.turn(0)
      time.sleep(1.25)


    def distance_to_goal(self):
      distance = math.hypot(self.end_pose.position.x - self.current_pose.position.x, self.end_pose.position.y - self.current_pose.position.y)
      rospy.loginfo('Distance to goal: {0}'.format(distance))
      return distance;

    # Return true if the robot has reached the goal with the given accepted error. False otherwise.
    def is_goal(self, accepted_error = 0.5):
      return (self.distance_to_goal() < accepted_error);

    def degrees_to_goal(self):
      deltaX = self.end_pose.position.x - self.current_pose.position.x
      deltaY = self.end_pose.position.y - self.current_pose.position.y

      # TODO revisar angulos negativos --> Valores absolutos
      # Ahora lo hace todo bien pero a veces da mas vueltas de las necesarias.
      desired_angle_radians = math.atan2(deltaY, deltaX)
      current_angle_radians = self.current_pose.orientation.z * math.pi ## REVISAR ZZZZZZZZZZZ

      distance_radians = (desired_angle_radians) - (current_angle_radians)
      distance_degrees = degrees(distance_radians)

      #rospy.loginfo('Degrees to face goal = {0}'.format(distance_degrees))
      #rospy.loginfo('Odometry data: {0}'.format(self.current_pose))
      #rospy.loginfo('deltaX: {0} DeltaY: {1}'.format(deltaX, deltaY))

      return distance_degrees; 

    def is_facing_goal(self, accepted_error = 0.05):
      return math.fabs(self.degrees_to_goal()) < accepted_error

    def stop(self):
      rospy.loginfo('Stopping TurtleBot')
      twist_stop = Twist()
      self.cmd_vel.publish(twist_stop)

    def shutdown(self):
      rospy.loginfo("Shutting down TurtleBot")
      self.stop()
      rospy.sleep(1)
      rospy.signal_shutdown("Shutdown function has been called")