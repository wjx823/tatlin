from __future__ import division

import math

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import pygtk
pygtk.require('2.0')
import gtk
from gtk.gtkgl.apputils import GLScene, GLSceneButton, GLSceneButtonMotion

from .vector3 import Vector3


def paginate(sequence, n):
    """
    Yield n-sized pieces of sequence.
    """
    for i in range(0, len(sequence), n):
        yield sequence[i:i+n]

def html_color(color):
    if color.startswith('#'):
        color = color[1:]
    parsed = [int(c, 16) / 255 for c in paginate(color, 2)]
    return parsed


class Scene(GLScene, GLSceneButton, GLSceneButtonMotion):
    def __init__(self):
        GLScene.__init__(self, gtk.gdkgl.MODE_RGB | gtk.gdkgl.MODE_DEPTH | gtk.gdkgl.MODE_DOUBLE)

        self.actors = []

        self.begin_x = 0
        self.begin_y = 0

        self.obj_pos = Vector3(0.0, 180.0, -20.0)

        self.__sphi   = 0.0
        self.__stheta = -20.0
        self.fovy     = 80.0
        self.z_near   = 1.0
        self.z_far    = 9000.0 # very far

    def init(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)

        # simulate translucency by blending colors
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glutInit()
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)

        import time
        t_start = time.time()

        for actor in self.actors:
            actor.init()

        t_end = time.time()
        print '--- actor init took %.2f seconds' % (t_end - t_start)

    def display(self, width, height):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLoadIdentity()
        glRotate(-90, 1.0, 0.0, 0.0) # make z point up

        glDisable(GL_CULL_FACE)
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        self.view_ortho(width, height)

        self.draw_axes()

        self.view_perspective()
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

        glTranslatef(self.obj_pos.x, self.obj_pos.y, self.obj_pos.z)
        glRotatef(-self.__stheta, 1.0, 0.0, 0.0)
        glRotatef(self.__sphi, 0.0, 0.0, 1.0)

        for actor in self.actors:
            actor.display()

        glFlush()

    def view_ortho(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, 0, height, -100.0, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def view_perspective(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def reshape(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fovy, width / height, self.z_near, self.z_far)
        glMatrixMode(GL_MODELVIEW)

    def button_press(self, width, height, event):
        self.begin_x = event.x
        self.begin_y = event.y

    def button_release(self, width, height, event):
        pass

    def button_motion(self, width, height, event):
        delta_x = event.x - self.begin_x
        delta_y = event.y - self.begin_y

        if event.state & gtk.gdk.BUTTON1_MASK: # left mouse button
            self.rotate(delta_x, delta_y)
        elif event.state & gtk.gdk.BUTTON2_MASK: # middle mouse button
            self.zoom(delta_x, delta_y)
        elif event.state & gtk.gdk.BUTTON3_MASK: # right mouse button
            self.pan(delta_x, delta_y, width, height)

        self.begin_x = event.x
        self.begin_y = event.y

        self.invalidate()

    def rotate(self, delta_x, delta_y):
        self.__sphi   += delta_x / 4.0
        self.__stheta -= delta_y / 4.0

    def zoom(self, delta_x, delta_y):
        self.obj_pos.y += delta_y / 10.0

    def pan(self, delta_x, delta_y, width, height):
        """
        Pan the model.

        Pannings works by translating relating mouse movements to movements in object space,
        using program window dimensions and field of view angle. A factor is applied to avoid
        speeding up on rapid mouse movements.
        """
        window_h = 2 * abs(self.obj_pos) * math.tan(self.fovy / 2) # height of window in object space

        magnitude_x = abs(delta_x)
        if magnitude_x > 0.0:
            x_scale = magnitude_x / width
            x_slow = 1 / magnitude_x
            self.obj_pos.x -= delta_x * x_scale * window_h * x_slow

        magnitude_y = abs(delta_y)
        if magnitude_y > 0.0:
            y_scale = magnitude_y / width
            y_slow = 1 / magnitude_y
            self.obj_pos.z += delta_y * y_scale * window_h * y_slow

    def draw_axes(self, length=50.0):
        glPushMatrix()

        glRotate(-90, 1.0, 0.0, 0.0) # make z point up
        glTranslatef(length + 20.0, 0.0, length + 20.0)
        glRotatef(-self.__stheta, 1.0, 0.0, 0.0)
        glRotatef(self.__sphi, 0.0, 0.0, 1.0)

        glBegin(GL_LINES)
        glColor(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(-length, 0.0, 0.0)

        glColor(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, -length, 0.0)

        glColor(*html_color('008aff'))
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, length)
        glEnd()

        glPopMatrix()


