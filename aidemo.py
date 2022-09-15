# Copyright (c) 2020 PHYTEC Messtechnik GmbH
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import time
import gi
import cv2
import numpy as np
from threading import Event, Thread, Lock
from queue import Queue

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository.GdkPixbuf import Colorspace, Pixbuf
from gi.repository import Gtk, GLib, GObject

import copy

CAMERA = 'VM-016'
#CAMERA = 'USB'

if CAMERA == 'VM-016':
    import camvm016 as camera
else:
    import camusb as camera

from ai import Ai
from loadscreen import LoadScreen


class AiDemo(Gtk.Window):
    def __init__(self, int_event):
        Gtk.Window.__init__(self, title='Celebrity Face Match')

        # model_file = 'demo-data/models/tflite/quantized_modelh5-15.tflite'
        model_file = 'lite-model_movenet_singlepose_lightning_3.tflite'
        # embeddings_file = 'demo-data/EMBEDDINGS_quantized_modelh5-15.json'

        self.EDGES = {
            (0, 1): 'm',
            (0, 2): 'c',
            (1, 3): 'm',
            (2, 4): 'c',
            (0, 5): 'm',
            (0, 6): 'c',
            (5, 7): 'm',
            (7, 9): 'm',
            (6, 8): 'c',
            (8, 10): 'c',
            (5, 6): 'y',
            (5, 11): 'm',
            (6, 12): 'c',
            (11, 12): 'y',
            (11, 13): 'm',
            (13, 15): 'm',
            (12, 14): 'c',
            (14, 16): 'c'
        }

        self.ai = Ai(os.path.join(sys.path[0], model_file),
                     modeltype = 'normal')

        self.cap = camera.get_camera()

        self.set_resizable(False)
        self.set_border_width(20)
        self.lock_ai = Lock()
        # self.lock_control = Lock()
        self.lock_kp = Lock()
        self.int_event = int_event
        self.start_detect_event = Event()
        # self.start_shuffle_event = Event()
        self.loaded_event = Event()
        # self.trigger_event = Event()
        # self.contineous = True
        self.connect('key-press-event', self.key_pressed)

        self.image_stream = Gtk.Image()
        # self.image_face = Gtk.Image()
        # self.image_celeb = Gtk.Image()
        # self.you_label = Gtk.Label()
        # self.top5_grid = Gtk.Grid()
        # self.celeb_labels = [
        #     Gtk.Label(),
        #     Gtk.Label(),
        #     Gtk.Label(),
        #     Gtk.Label(),
        #     Gtk.Label(),
        # ]
        # self.dist_labels = [
        #     Gtk.Label(),
        #     Gtk.Label(),
        #     Gtk.Label(),
        #     Gtk.Label(),
        #     Gtk.Label(),
        # ]
        # self.result_label = Gtk.Label()
        self.main_label = Gtk.Label()
        # self.switch_label = Gtk.Label()
        # self.trigger_btn = Gtk.Button()
        # self.trigger_btn.connect('clicked', self.trigger_clicked)
        # self.mode_switch = Gtk.Switch()
        # self.mode_switch.connect('notify::active', self.mode_switch_action)
        # self.mode_switch.set_active(self.contineous)

        self.pic_size = (300, 300)

        self.setup_layout()

        # self.face_cascade = cv2.CascadeClassifier(
        #     'demo-data/haarcascade_frontalface.xml')

        # self.celebs = []
        # celebs = [ 'danny', 'fairuza', 'richard', 'shirley', 'vin']

        # for c in celebs:
        #     celeb = cv2.imread('demo-data/{}.jpg'.format(c))
        #     celeb = cv2.cvtColor(celeb, cv2.COLOR_BGR2RGB)
        #     celeb = cv2.resize(celeb, self.pic_size,
        #                        interpolation=cv2.INTER_CUBIC)
        #     self.celebs.append(celeb)

        # self.cam = cv2.imread('demo-data/camera.jpg')
        # self.cam = cv2.cvtColor(self.cam, cv2.COLOR_BGR2RGB)
        # self.cam = cv2.resize(self.cam, self.pic_size,
        #                       interpolation=cv2.INTER_CUBIC)

        # self.update_face(self.cam)
        # self.update_celeb(self.celebs[0])
        # self.update_stream(self.celebs[0])

        self.load_thread = Thread(target=self.load_ai)
        stream_thread = Thread(target=self.stream)
        # faces_thread = Thread(target=self.detect_faces)
        # shuffle_thread = Thread(target=self.shuffle_celebs)
        ai_thread = Thread(target=self.detect)

        self.image_queue = Queue(maxsize=1)
        self.keypoints_with_scores = None
        # self.faces = None
        # self.face = self.cam
        # self.celeb = None
        # self.rectangle = None
        # self.face_corner = (0, 0)

        self.start_detect_event.set()
        # self.start_shuffle_event.set()
        self.loaded_event.clear()

        self.load_thread.daemon = True
        stream_thread.daemon = True
        # faces_thread.daemon = True
        # shuffle_thread.daemon = True
        ai_thread.daemon = True
        self.load_thread.start()
        stream_thread.start()
        # faces_thread.start()
        # shuffle_thread.start()
        ai_thread.start()

        self.loadscreen = LoadScreen()
        self.loadscreen.connect('delete-event', Gtk.main_quit)

    def setup_layout(self):
        self.main_label.set_markup(
            '<span font="20" font_weight="bold"> Celebrity Face Match </span>'
        )
        # self.switch_label.set_markup(
        #     '<b>Contineous Mode</b>'
        # )
        # self.result_label.set_markup(
        #     '<span font="16.0" font_weight="bold">Last Result</span>'
        # )
        # self.you_label.set_markup(
        #     '<span font="14.0" font_weight="bold">Your Face</span>'
        # )
        # self.you_label.set_valign(Gtk.Align.START)
        # self.you_label.set_margin_bottom(50)
        # self.result_label.set_valign(Gtk.Align.START)
        # self.result_label.set_margin_bottom(20)
        # self.image_face.set_valign(Gtk.Align.START)
        # self.image_celeb.set_valign(Gtk.Align.START)

        # btn_label = Gtk.Label()
        # btn_label.set_markup(
        #     '<span font="14.0" font_weight="bold">Trigger</span>'
        # )
        # self.trigger_btn.add(btn_label)
        # self.trigger_btn.set_size_request(270, 80)

        # self.mode_switch.set_valign(Gtk.Align.CENTER)
        # switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        # switch_box.set_halign(Gtk.Align.START)
        # switch_box.pack_start(self.switch_label, False, True, 0)
        # switch_box.pack_start(self.mode_switch, False, True, 0)

        # trigger_box = Gtk.Box(spacing=5)
        # trigger_box.set_homogeneous(False)
        # trigger_box.set_valign(Gtk.Align.END)
        # trigger_box.set_halign(Gtk.Align.START)
        # trigger_box.pack_start(switch_box, False, True, 0)
        # trigger_box.pack_start(self.trigger_btn, False, True, 300)

        stream_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        stream_box.set_valign(Gtk.Align.START)
        stream_box.set_halign(Gtk.Align.CENTER)
        stream_box.pack_start(self.image_stream, False, True, 0)
        # stream_box.pack_start(trigger_box, False, True, 0)

        # self.top5_grid.set_row_spacing(6)
        # self.top5_grid.set_column_spacing(12)
        # self.top5_grid.set_margin_top(15)
        # self.top5_grid.set_halign(Gtk.Align.CENTER)
        # for i in range(5):
        #     num_label = Gtk.Label()
        #     if i == 0:
        #         color = 'red'
        #     else:
        #         color = 'black'

        #     num_label.set_markup(
        #         '<span font="14.0" fgcolor="{}"><b>{}.</b></span>'.format(
        #             color, i+1)
        #     )
        #     num_label.set_halign(Gtk.Align.START)
        #     self.celeb_labels[i].set_width_chars(26)
        #     self.celeb_labels[i].set_xalign(0)
        #     self.dist_labels[i].set_xalign(1)
        #     self.dist_labels[i].set_width_chars(10)
        #     self.top5_grid.attach(num_label, 0, i, 1, 1)
        #     self.top5_grid.attach(self.celeb_labels[i], 1, i, 1, 1)
        #     self.top5_grid.attach(self.dist_labels[i], 3, i, 1, 1)

        # self.update_top5(None)

        # picture_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        # picture_box.set_homogeneous(False)
        # picture_box.pack_start(self.result_label, False, True, 0)
        # picture_box.pack_start(self.image_face, False, True, 0)
        # picture_box.pack_start(self.you_label, False, True, 0)
        # picture_box.pack_start(self.image_celeb, False, True, 0)
        # picture_box.pack_start(self.top5_grid, False, True, 0)

        content_box = Gtk.Box(spacing=20)
        content_box.pack_start(stream_box, True, True, 0)
        # content_box.pack_start(picture_box, True, True, 0)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.pack_start(self.main_label, True, True, 0)
        main_box.pack_start(content_box, True, True, 0)
        self.add(main_box)

    def load_ai(self):
        time.sleep(1)

        if self.cap is None:
            GLib.idle_add(self.loadscreen.append_text,
                          'Failed to open Videodevice',
                          0.0)
            GLib.idle_add(self.loadscreen.append_text,
                          'VM-016 camera driver was not loaded succesfully',
                          0.0)
            GLib.idle_add(self.loadscreen.append_text,
                          'Check your camera connection',
                          0.0)
            return

        GLib.idle_add(self.loadscreen.append_text,
                      'Loading Model and Embeddings.', 0.25,
                      priority=GLib.PRIORITY_DEFAULT_IDLE)
        start = time.time()
        self.ai.initialize()
        duration = time.time() - start
        GLib.idle_add(self.loadscreen.append_text,
                      'Loading Model and Embeddings done. ({:6.3f} s)'.format(
                          duration
                      ), 0.5,
                      priority=GLib.PRIORITY_DEFAULT_IDLE)

        # AI warmup
        GLib.idle_add(self.loadscreen.append_text,
                      'Warming up NPU (can take a minute).', 0.5,
                      priority=GLib.PRIORITY_DEFAULT_IDLE)
        start = time.time()
        # self.ai.run_inference(self.celebs[0])
        duration = time.time() - start
        GLib.idle_add(self.loadscreen.append_text,
                      'Warming up done. ({:6.3f} s)'.format(duration), 0.75,
                      priority=GLib.PRIORITY_DEFAULT_IDLE)

        time.sleep(1)
        GLib.idle_add(self.loadscreen.destroy,
                      priority=GLib.PRIORITY_DEFAULT_IDLE)
        GLib.idle_add(self.show_all,
                      priority=GLib.PRIORITY_DEFAULT_IDLE)
        self.loaded_event.set()

    def stream(self):
        framecount = 0
        facecount = 0

        self.loaded_event.wait()
        self.load_thread.join()

        while True:
            notimeout = self.start_detect_event.wait(timeout=0.5)
            if self.int_event.is_set():
                break

            if not notimeout:
                continue

            ret, frame = self.cap.read()
            if ret == 0:
                print('No Frame')
                continue

            framecount += 1
            frame = camera.color_convert(frame)

            if self.image_queue.full():
                self.image_queue.get()

            self.image_queue.put(frame.copy())

            with self.lock_kp:
                if self.keypoints_with_scores is not None:

                    keypoints_with_scores = copy.deepcopy(self.keypoints_with_scores)

                    self.draw_connections(frame, keypoints_with_scores, self.EDGES, 0.4)
                    self.draw_keypoints(frame, keypoints_with_scores, 0.4)
                #     (x, y, w, h) = self.faces
                #     self.faces = None
                #     framecount = 0
                #     if facecount > 5:
                #         self.trigger_event.set()
                #         facecount = 0
                #     else:
                #         if facecount == 0:
                #             self.face_corner = (x, y)
                #             facecount = 1
                #         else:
                #             (face_x, face_y) = self.face_corner
                #             if (np.abs(face_x - x) < 40 and
                #                     np.abs(face_y - y) < 40):
                #                 with self.lock_control:
                #                     if self.contineous:
                #                         facecount += 1
                #             else:
                #                 facecount = 0

                #     p = 0
                #     if (x - p < 0 or y - p < 0 or
                #           x + w + p > np.shape(frame)[1] or
                #           y + h + p > np.shape(frame)[0]):

                #         self.face = self.cam
                #     else:
                #         self.rectangle = (x-p, y-p+2, x+w+p, y+h+p+2)
                #         self.face = frame[y-p+4:y+h+p, x-p+4:x+w+p]
                #         self.face = cv2.resize(self.face, self.pic_size,
                #                                interpolation=cv2.INTER_CUBIC)

                # else:
                #     if framecount > 15:
                #         framecount = 0
                #         facecount = 0
                #         self.rectangle = None
                #         self.face = self.cam

            # if self.rectangle:
            #     (x, y, w, h) = self.rectangle
            #     frame = cv2.rectangle(frame, (x, y), (w, h), (0, 255, 0), 2)

            #     self.draw_connections(frame, keypoints_with_scores, self.EDGES, 0.4)
            #     self.draw_keypoints(frame, keypoints_with_scores, 0.4)

            GLib.idle_add(self.update_stream, frame,
                          priority=GLib.PRIORITY_HIGH)

        self.cap.release()

    # def shuffle_celebs(self):
    #     count = 0

    #     self.loaded_event.wait()

    #     while True:
    #         notimeout = self.start_shuffle_event.wait(timeout=0.5)
    #         if self.int_event.is_set():
    #             break

    #         if not notimeout:
    #             continue

    #         GLib.idle_add(self.update_celeb, self.celebs[count],
    #                       priority=GLib.PRIORITY_HIGH)

    #         if count < 4:
    #             count += 1
    #         else:
    #             count = 0

    #         time.sleep(0.05)

    def detect(self):
        self.loaded_event.wait()

        while True:
            notimeout = self.start_detect_event.wait(timeout=0.5)
            if self.int_event.is_set():
                break

            if not notimeout:
                continue

            frame = self.image_queue.get()

            if CAMERA == 'VM-016':
                scale = 4
            else:
                scale = 1

            # (h, w, c) = np.shape(frame)
            # frame = cv2.resize(frame, (int(w/scale), int(h/scale)))

            kp = self.ai.run_inference(frame)

            with self.lock_kp:
                self.keypoints_with_scores = self.kp_in_frame(kp, frame)

            # faces = self.face_cascade.detectMultiScale(frame,
            #                                            scaleFactor=1.2,
            #                                            minNeighbors=2)

            # if len(faces) == 0:
            #     continue

            # frame_center = np.shape(frame)[1] / 2
            # face_centers = []
            # # Find face which is closest to the center
            # for (x, y, w, h) in faces:
            #     face_centers = np.append(face_centers, (x + w / 2))

            # center_face_idx = (np.abs(face_centers - frame_center)).argmin()
            # # Extract center face from frame
            # (x, y, w, h) = faces[center_face_idx]
            # (x, y, w, h) = (x * scale, y * scale, w * scale, h * scale)

            # with self.lock_faces:
            #     self.faces = (x, y, w, h)

    # def calculate_embeddings(self):
    #     self.loaded_event.wait()

    #     while True:
    #         notimeout = self.trigger_event.wait(timeout=0.5)
    #         if self.int_event.is_set():
    #             break

    #         if not notimeout:
    #             continue

    #         print('Triggered')
    #         with self.lock_faces:
    #             if self.face is self.cam:
    #                 self.trigger_event.clear()
    #                 continue
    #             else:
    #                 _face = self.face.copy()

    #         self.start_detect_event.clear()

    #         GLib.idle_add(self.update_face, _face,
    #                       priority=GLib.PRIORITY_HIGH)

    #         top5 = self.ai.run_inference(_face)
    #         top5_values = list(top5.values())
    #         GLib.idle_add(self.update_top5, top5_values,
    #                       priority=GLib.PRIORITY_HIGH)

    #         folder = top5_values[0][1]
    #         filename = top5_values[0][2]

    #         path = os.path.join(sys.path[0], 'demo-data/Celebs_faces',
    #                             str(folder), str(filename))
    #         celeb = cv2.imread(path)
    #         celeb = cv2.cvtColor(celeb, cv2.COLOR_BGR2RGB)
    #         celeb = cv2.resize(celeb, self.pic_size,
    #                            interpolation=cv2.INTER_CUBIC)

    #         self.start_shuffle_event.clear()
    #         time.sleep(0.05)

    #         GLib.idle_add(self.update_celeb, celeb,
    #                       priority=GLib.PRIORITY_HIGH)

    #         self.start_detect_event.set()

    #         with self.lock_control:
    #             if not self.contineous:
    #                 self.trigger_event.clear()
    #                 continue

    #         time.sleep(5)
    #         self.start_shuffle_event.set()
    #         GLib.idle_add(self.update_face, self.cam,
    #                       priority=GLib.PRIORITY_HIGH)
    #         GLib.idle_add(self.update_top5, None,
    #                       priority=GLib.PRIORITY_HIGH)

    #         self.trigger_event.clear()

    def key_pressed(self, widget, key):
        if not self.contineous and self.trigger_btn.has_focus():
            if key.keyval == 32:
                self.trigger_event.set()
        return False

    # def trigger_clicked(self, button):
    #     self.trigger_event.set()

    # def mode_switch_action(self, switch, gparam):
    #     if switch.get_active():
    #         active = True
    #         self.trigger_btn.set_sensitive(False)
    #     else:
    #         active = False
    #         self.trigger_btn.set_sensitive(True)
    #         self.trigger_btn.grab_focus()

    #     with self.lock_control:
    #         self.contineous = active

    #     if active:
    #         if self.start_detect_event.is_set():
    #             self.start_shuffle_event.set()
    #             self.update_face(self.cam)
    #             self.update_top5(None)

    def update_stream(self, frame):
        frame = cv2.resize(frame, (1280, 800))
        height, width = frame.shape[:2]
        arr = np.ndarray.tostring(frame)
        pixbuf = Pixbuf.new_from_data(arr, Colorspace.RGB, False, 8,
                                      width, height, width * 3, None, None)
        self.image_stream.set_from_pixbuf(pixbuf)
        return False

    # def update_face(self, face):
    #     height, width = face.shape[:2]
    #     arr = np.ndarray.tostring(face)
    #     pixbuf = Pixbuf.new_from_data(arr, Colorspace.RGB, False, 8,
    #                                   width, height, width * 3, None, None)
    #     self.image_face.set_from_pixbuf(pixbuf)
    #     return False

    # def update_celeb(self, celeb):
    #     height, width = celeb.shape[:2]
    #     arr = np.ndarray.tostring(celeb)
    #     pixbuf = Pixbuf.new_from_data(arr, Colorspace.RGB, False, 8,
    #                                   width, height, width * 3, None, None)
    #     self.image_celeb.set_from_pixbuf(pixbuf)
    #     return False

    # def update_top5(self, ranking):
    #     if ranking is None:
    #         for i in range(5):
    #             self.celeb_labels[i].set_markup(
    #                 '<span font="14.0"> <b>...</b></span>'
    #             )
    #             self.dist_labels[i].set_markup(
    #                 ''
    #             )

    #         return False

    #     for i in range(5):
    #         if i == 0:
    #             color = 'red'
    #         else:
    #             color = 'black'

    #         self.celeb_labels[i].set_markup(
    #             '<span font="14.0" fgcolor="{}"><b>{}</b></span>'.format(
    #                 color, ranking[i][1])
    #         )
    #         self.dist_labels[i].set_markup(
    #             '<span font="14.0" fgcolor="{}"><b>{:8.3f}</b></span>'.format(
    #                 color, ranking[i][0])
    #         )

    #     return False

    def kp_in_frame(self, keypoints, frame):
        y, x, c = frame.shape
        shaped = np.squeeze(np.multiply(keypoints, [y,x,1]))

        return shaped

    
    def draw_keypoints(self, frame, shaped, confidence_threshold):
        
        for kp in shaped:
            ky, kx, kp_conf = kp
            if kp_conf > confidence_threshold:
                cv2.circle(frame, (int(kx), int(ky)), 4, (0,255,0), -1)
    

    def draw_connections(self, frame, shaped, edges, confidence_threshold):
        
        for edge, color in edges.items():
            p1, p2 = edge
            y1, x1, c1 = shaped[p1]
            y2, x2, c2 = shaped[p2]
            
            if (c1 > confidence_threshold) & (c2 > confidence_threshold):      
                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0,0,255), 2)


def main():
    int_event = Event()
    window = AiDemo(int_event)
    window.connect('delete-event', Gtk.main_quit)

    try:
        Gtk.main()
    except KeyboardInterrupt:
        print('Interrupted')

    print('Termination')
    int_event.set()
    time.sleep(1)


if __name__ == '__main__':
    main()
