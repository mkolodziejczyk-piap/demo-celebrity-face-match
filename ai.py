# Copyright (c) 2020 PHYTEC Messtechnik GmbH
# SPDX-License-Identifier: Apache-2.0

import os
import time
import cv2

import tflite_runtime.interpreter as tflite
import numpy as np
import json
import concurrent.futures


class Ai:
    def __init__(self, model_path, modeltype='quant'):
        self.model_path = model_path
        self.modeltype = modeltype
        self.width = 192
        self.height = 192

    def initialize(self):
        start = time.time()

        self.init_tflite()

        print('Initialization done (duration: {})'.format(time.time() - start))

    def run_inference(self, face):
        #Resize face
        print('Resize face')
        if face.shape > (self.width, self.height):
            face = cv2.resize(face, (self.width, self.height),
                              interpolation=cv2.INTER_AREA)
        elif face.shape < (self.width, self.height):
            face = cv2.resize(face, (self.width, self.height),
                              interpolation=cv2.INTER_CUBIC)

        #TODO resize with pad vide 
        # image = tf.image.resize_with_pad(image, 192, 192)

        print('Preprocess')
        if self.modeltype is 'quant':
            face = face.astype('float32')
            samples = np.expand_dims(face, axis=0)
            samples = self.preprocess_input(samples,
                                            data_format='channels_last',
                                            version=3).astype('int8')
        else:
            face = face.astype('float32')
            samples = np.expand_dims(face, axis=0)
            samples = self.preprocess_input(samples,
                                            data_format='channels_last',
                                            version=2)

        output_data = self.run_tflite(samples)

        print('Create EUdist')
        start = time.time()
        # with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        #     result_1 = executor.submit(self.faceembedding, output_data,
        #                                np.array(self.celeb_embeddings[0]))
        #     result_2 = executor.submit(self.faceembedding, output_data,
        #                                np.array(self.celeb_embeddings[1]))
        #     result_3 = executor.submit(self.faceembedding, output_data,
        #                                np.array(self.celeb_embeddings[2]))
        #     result_4 = executor.submit(self.faceembedding, output_data,
        #                                np.array(self.celeb_embeddings[3]))

        # EUdist = []
        # if result_1.done() & result_2.done() & result_3.done() & result_4.done():
        #     EUdist.extend(result_1.result())
        #     EUdist.extend(result_2.result())
        #     EUdist.extend(result_3.result())
        #     EUdist.extend(result_4.result())

        # idx = np.argpartition(EUdist, 5)
        # idx = idx[:5]

        # top5 = dict()
        # for id in idx:
        #     top5[id] = [EUdist[id], self.names[id], self.files[id]]

        # top5 = {key: value for key, value in sorted(top5.items(), key=lambda item: item[1][0])}

        # print('EUdist duration: {}'.format(time.time() - start))

        #TODO POSTPROCESSING



        return output_data

    def init_tflite(self):

        os.environ['VIV_VX_CACHE_BINARY_GRAPH_DIR'] = os.getcwd()
        os.environ['VIV_VX_ENABLE_CACHE_GRAPH_BINARY'] = '1'

        try:
            self.interpreter = tflite.Interpreter(self.model_path)
        except ValueError as e:
            print('Failed to find model file: ' + str(e))
            return

        print('Allocate Tensors')
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def run_tflite(self, samples):
        print('Invoke TFlite')
        start = time.time()
        self.interpreter.set_tensor(self.input_details[0]['index'], samples)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(
                        self.output_details[0]['index'])
        print('Interpreter done ({})'.format(time.time() - start))
        return output_data

    # def split_data_frame(self, df, chunk_size):
    #     list_of_df = list()
    #     number_chunks = len(df) // chunk_size + 1
    #     for i in range(number_chunks):
    #         list_of_df.append(df[i*chunk_size:(i+1)*chunk_size])

        return list_of_df

    def preprocess_input(self, x, data_format, version):
        x_temp = np.copy(x)
        assert data_format in {'channels_last', 'channels_first'}

        if version == 1:
            if data_format == 'channels_first':
                x_temp = x_temp[:, ::-1, ...]
                x_temp[:, 0, :, :] -= 93.5940
                x_temp[:, 1, :, :] -= 104.7624
                x_temp[:, 2, :, :] -= 129.1863
            else:
                x_temp = x_temp[..., ::-1]
                x_temp[..., 0] -= 93.5940
                x_temp[..., 1] -= 104.7624
                x_temp[..., 2] -= 129.1863

        elif version == 2:
            if data_format == 'channels_first':
                x_temp = x_temp[:, ::-1, ...]
                # x_temp[:, 0, :, :] -= 91.4953
                # x_temp[:, 1, :, :] -= 103.8827
                # x_temp[:, 2, :, :] -= 131.0912
            else:
                x_temp = x_temp[..., ::-1]
                # x_temp[..., 0] -= 91.4953
                # x_temp[..., 1] -= 103.8827
                # x_temp[..., 2] -= 131.0912

        elif version == 3:
            if data_format == 'channels_first':
                x_temp = x_temp[:, ::-1, ...]
                # x_temp[:, 0, :, :] -= np.round(91.4953).astype('uint8')
                # x_temp[:, 1, :, :] -= np.round(103.8827).astype('uint8')
                # x_temp[:, 2, :, :] -= np.round(131.0912).astype('uint8')
            else:
                x_temp = x_temp[..., ::-1]
                # x_temp[..., 0] -= np.round(91.4953).astype('uint8')
                # x_temp[..., 1] -= np.round(103.8827).astype('uint8')
                # x_temp[..., 2] -= np.round(131.0912).astype('uint8')
        else:
            raise NotImplementedError

        return x_temp

    # def faceembedding(self, face, celebdata):
    #     dist = []
    #     for i in range(len(celebdata)):
    #         celebs = np.array(celebdata[i])
    #         dist.append(np.linalg.norm(face - celebs))

    #     return dist
