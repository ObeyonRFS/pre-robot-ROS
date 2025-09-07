# pre-robot-ROS
Study ObeyonRFS requirement by making pre-robot with ROS






# Potential Errors & handling


## Can't SSH into Raspberry Pi

For error when SSH into robot/RPi like this
```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ @ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY! Someone could be eavesdropping on you right now (man-in-the-middle attack)! It is also possible that a host key has just been changed. The fingerprint for the ED25519 key sent by the remote host is SHA256:DDWuhZNWg11w+dRBtohHKDj3fK2jqrcZPuikI4YSrzc. Please contact your system administrator. Add correct host key in C:\\Users\\yanot/.ssh/known_hosts to get rid of this message. Offending ECDSA key in C:\\Users\\yanot/.ssh/known_hosts:3 Host key for urpi has changed and you have requested strict checking. Host key verification failed.
```
Can be the case for reinstall ubuntu on Raspberry Pi

You need to just remove old key entry on Windows with this command

```
ssh-keygen -R urpi
```
Then you can ssh into Raspberry Pi once again

## Can't clone git over SSH

```
ssh-keygen -t ed25519 -C "your_email@example.com"

ls ~/.ssh

cat ~/.ssh/id_ed25519.pub
```
leave everything as default, and copy the result to SSH key settings in your profile.

## Can't find anywhere on how to install microROS on arduino

MicroROS repository said it themselves, that they are not ready for production

The way to handle is
Create extra node

## Ubuntu can't access to rplidar (permission denied)

Try
```
sudo usermod -aG dialout $USER
```
Then restart ubuntu

Or
```
sudo chmod 0666 /dev/ttyUSB0
```

## colcon build skips rplidar_ros package

This is a weird bug, Try remove rplidar_ros folder in src, then clone it from official (follow slamtec instruction)
Then colcon build again