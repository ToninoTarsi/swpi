import camera
import config

configfile = 'swpi.cfg'

cfg = config.config(configfile)


cam = camera.PhotoCamera(cfg)

cam.reset_camera()

print "Camera reset"