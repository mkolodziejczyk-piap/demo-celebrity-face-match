This is a toy example of pose keypoint detection to test Phytec iMX8 Plus NPU capabilites

# Prerequirements

## For desktop installation
* (recommended) use dedicated virtualenv

* install requirements
```
sudo apt install libgirepository1.0-dev
pip install requirements_desktop.txt
```

## iMX and desktop

```
git clone ...
cd ...
wget -q -O model.tflite https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/3?lite-format=tflite
```


# Usage

```
python3 aidemo.py
```

# References

* [AI Demo - Celebrity Face Match](https://github.com/phytec/demo-celebrity-face-match)
* [Pose estimation](https://www.tensorflow.org/lite/examples/pose_estimation/overview)