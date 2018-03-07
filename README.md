# prosdk-addons-python - Calibration validation

## What is it
Add-ons for the Tobii Pro SDK.

![alt text](https://www.tobiipro.com/imagevault/publishedmedia/6rkt3jb83qlottsfh1ts/Tobii-Pro-SDK-with-VR-3_1-banner.jpg)


The Tobii Pro SDK is available at: https://www.tobiipro.com/product-listing/tobii-pro-sdk/ <br/>
Documentation to the API: http://developer.tobiipro.com/python.html
Getting started: http://developer.tobiipro.com/python/python-getting-started.html

Do not hesitate to contribute to this project and create issues if you find something that might be wrong or could be improved.

## Installation

* Download or clone this folder.
* Navigate to the cloned or downloaded and unpacked folder.
* Install by using pip.
```
pip install .
```

The Tobii Pro SDK Python package will be installed automatically by pip.

## Features

### Calibration Validation

The package contains functionality for validating calibrations by calculating various statistics for different
stimuli points. Note: There are no functionality for actually presenting the stimuli points on screen.

#### Example
Before starting a calibration validation, some setup with the desired tracker is needed.

```python
import time
import tobii_research as tr
from tobii_research_addons import ScreenBasedCalibrationValidation, Point2

eyetracker_address = 'Replace the address of the desired tracker'
eyetracker = tr.EyeTracker(eyetracker_address)
```

Now it is possible to create a calibration validation object with the eye tracker object previously created.
More information about this class and its methods can be found in the [ScreenBasedCalibrationValidation](./source/ScreenBasedCalibrationValidation.py) definition.

```python
sample_count = 30
timeout_ms = 1000

calib = ScreenBasedCalibrationValidation(eyetracker, sample_count, timeout_ms)
```

The next step is to enter validation mode. Note that this action will cause the tracker to start collecting gaze data.

```python
calib.enter_validation_mode()
```

List the points that are to be used during the validation.

```python
points_to_collect = [
    Point2(0.1, 0.1),
    Point2(0.1, 0.9),
    Point2(0.5, 0.5),
    Point2(0.9, 0.1),
    Point2(0.9, 0.9)]
```

When collecting data a point should be presented on the screen in the appropriate position.

```python
for point in points_to_collect:
    # Visualize point on screen
    # ...
    calib.start_collecting_data(point)
    while calib.is_collecting_data:
        time.sleep(0.5)
```

Next, just call the compute method to obtain the calibration validation result object.

```python
calibration_result = calib.compute()
```

Now the calibration validation result should be available for inspection.

More information about the calibration validation result can be found in the [CalibrationValidationResult](./source/ScreenBasedCalibrationValidation.py) class.

If the result is satisfactory then the only thing left to do is to leave validation mode.
This action will clear all the data collected in the current validation session and stop the gaze data collection
from the tracker.

```python
calib.leave_validation_mode()
```

You can also use the with statement to simplify the workings with the ScreenBasedCalibrationValidation object. It will
automatically enter and leave calibration mode.

```python
sample_count = 30
timeout_ms = 1000
points_to_collect = [
    Point2(0.1, 0.1),
    Point2(0.1, 0.9),
    Point2(0.5, 0.5),
    Point2(0.9, 0.1),
    Point2(0.9, 0.9)]

with ScreenBasedCalibrationValidation(eyetracker, sample_count, timeout_ms) as calib:
    for point in points_to_collect:
        # Visualize point on screen
        # ...
        calib.start_collecting_data(point)
        while calib.is_collecting_data:
            time.sleep(0.5)
    calibration_result = calib.compute()

# Do something with the result
# ...
```
